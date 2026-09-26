"""
zatca_client.py — Sign and submit invoices to ZATCA.

Wraps the fatoora CLI (bundled in the container) and the ZATCA HTTP
gateway. Called from app.py. No DB code, no Flask code — pure ZATCA
interaction.

Environment variables (all optional):
  ZATCA_ENV         sandbox | simulation | production   (default: sandbox)
  ZATCA_CSID_PATH   path to CSID JSON                    (default: /app/credentials/compliance_csid.json)
  ZATCA_TIMEOUT     HTTP timeout in seconds              (default: 30)

All credentials come from the CSID file. Nothing is hardcoded.
"""
import base64
import json
import logging
import os
import subprocess

try:
    import requests
except ImportError:
    requests = None


ENDPOINTS = {
    "sandbox":    "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal",
    "simulation": "https://gw-fatoora.zatca.gov.sa/e-invoicing/simulation",
    "production": "https://gw-fatoora.zatca.gov.sa/e-invoicing/core",
}

DEFAULT_ENV = "sandbox"
DEFAULT_CSID_PATH = "/app/credentials/compliance_csid.json"
DEFAULT_TIMEOUT = 30


# ----------------------------------------------------------------------
# Config helpers
# ----------------------------------------------------------------------

def get_env():
    env = os.environ.get("ZATCA_ENV", DEFAULT_ENV).lower().strip()
    if env not in ENDPOINTS:
        raise ValueError(f"Unknown ZATCA_ENV: {env}. Must be one of {list(ENDPOINTS)}")
    return env


def get_csid_path():
    return os.environ.get("ZATCA_CSID_PATH", DEFAULT_CSID_PATH)


def get_timeout():
    return int(os.environ.get("ZATCA_TIMEOUT", DEFAULT_TIMEOUT))


def endpoint_for(env, invoice_type_code, invoice_type_name="0100000", cert_type="compliance"):
    """
    Return the submission URL for the environment + invoice type + cert type.

    cert_type:
      "compliance" -> /compliance/invoices       (Compliance CSID)
      "production" -> /invoices/clearance/single (Standard, Production CSID)
                   -> /invoices/reporting/single (Simplified, Production CSID)

    invoice_type_name:
      "0100000"    -> Standard (B2B)
      "0200000"    -> Simplified (B2C)
    """
    base = ENDPOINTS[env]

    if cert_type == "compliance":
        return f"{base}/compliance/invoices"

    # Simplified routes to reporting, Standard routes to clearance
    if str(invoice_type_name).strip() == "0200000":
        return f"{base}/invoices/reporting/single"

    return f"{base}/invoices/clearance/single"


def load_csid():
    """Read the CSID JSON. Returns (token, secret, request_id)."""
    path = get_csid_path()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    token = data.get("binarySecurityToken")
    secret = data.get("secret")
    request_id = data.get("requestID")
    if not token or not secret:
        raise ValueError(f"CSID file {path} is missing binarySecurityToken or secret")
    return token, secret, request_id


# ----------------------------------------------------------------------
# fatoora CLI wrappers
# ----------------------------------------------------------------------

def _run_fatoora(args, timeout=120):
    """Run a fatoora subcommand. Returns (stdout, stderr, returncode)."""
    cmd = ["fatoora"] + args
    logging.info(f"zatca_client: running {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout or "", result.stderr or "", result.returncode
    except subprocess.TimeoutExpired:
        return "", f"fatoora timed out after {timeout}s", -1
    except FileNotFoundError:
        return "", "fatoora binary not found in PATH", -1


def sign_invoice(invoice_path, signed_path):
    """Sign the invoice XML using the cert + key at the SDK's configured paths."""
    if not os.path.exists(invoice_path):
        return {"ok": False, "error": f"Invoice file not found: {invoice_path}"}

    stdout, stderr, rc = _run_fatoora([
        "-sign",
        "-invoice", invoice_path,
        "-signedInvoice", signed_path,
    ])

    if rc != 0:
        return {
            "ok": False,
            "error": f"fatoora -sign failed (rc={rc})",
            "stderr": stderr[-500:] if stderr else "",
            "stdout": stdout[-500:] if stdout else "",
        }

    if not os.path.exists(signed_path):
        return {"ok": False, "error": "Signed file was not produced"}

    return {"ok": True, "signed_path": signed_path}

def validate_invoice(invoice_path):
    """
    Run fatoora -validate on an invoice XML.
    Returns {ok, passed, details} — passed is True only if GLOBAL VALIDATION RESULT = PASSED.
    """
    if not os.path.exists(invoice_path):
        return {"ok": False, "error": f"File not found: {invoice_path}"}

    stdout, stderr, rc = _run_fatoora(["-validate", "-invoice", invoice_path])

    output = (stdout or "") + (stderr or "")
    passed = "GLOBAL VALIDATION RESULT = PASSED" in output

    # Extract the individual result lines
    details = []
    for line in output.splitlines():
        if "validation result" in line or "GLOBAL VALIDATION" in line:
            details.append(line.strip())

    return {
        "ok": True,
        "passed": passed,
        "details": details,
        "raw": output[-2000:] if not passed else "",
    }

def build_request(signed_path, request_path):
    """Build the ZATCA submission JSON from the signed invoice."""
    if not os.path.exists(signed_path):
        return {"ok": False, "error": f"Signed file not found: {signed_path}"}

    stdout, stderr, rc = _run_fatoora([
        "-invoiceRequest",
        "-invoice", signed_path,
        "-apiRequest", request_path,
    ])

    if rc != 0:
        return {
            "ok": False,
            "error": f"fatoora -invoiceRequest failed (rc={rc})",
            "stderr": stderr[-500:] if stderr else "",
        }

    if not os.path.exists(request_path):
        return {"ok": False, "error": "Request JSON was not produced"}

    with open(request_path, "r", encoding="utf-8") as f:
        body = json.load(f)

    return {"ok": True, "request_path": request_path, "body": body}


# ----------------------------------------------------------------------
# HTTP submission
# ----------------------------------------------------------------------

def submit(invoice_type_code, body, env=None, cert_type="compliance", invoice_type_name="0100000"):
    """POST the request body to the ZATCA gateway."""
    if requests is None:
        return {"ok": False, "error": "requests library not installed"}

    if env is None:
        env = get_env()

    try:
        token, secret, _ = load_csid()
    except Exception as e:
        return {"ok": False, "error": f"CSID load failed: {e}"}

    url = endpoint_for(env, invoice_type_code,
                       invoice_type_name=invoice_type_name,
                       cert_type=cert_type)
    auth = base64.b64encode(f"{token}:{secret}".encode("utf-8")).decode("ascii")

    headers = {
        "Content-Type": "application/json",
        "Accept-Version": "V2",
        "Accept-Language": "en",
        "Authorization": f"Basic {auth}",
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=get_timeout())
    except Exception as e:
        return {"ok": False, "error": f"HTTP POST failed: {e}", "url": url, "env": env}

    try:
        resp_json = resp.json()
    except Exception:
        resp_json = {"raw": resp.text}

    return {
        "ok": True,
        "url": url,
        "env": env,
        "http_status": resp.status_code,
        "response": resp_json,
    }
# ----------------------------------------------------------------------
# Full pipeline
# ----------------------------------------------------------------------

def submit_invoice(invoice_xml_path, invoice_type_code,
                   signed_path=None, request_path=None, env=None,
                   cert_type="compliance", invoice_type_name="0100000"):
    """
    Sign, build request, submit. One call does it all.
    """
    if signed_path is None:
        signed_path = invoice_xml_path.rsplit(".", 1)[0] + "_signed.xml"
    if request_path is None:
        request_path = invoice_xml_path.rsplit(".", 1)[0] + "_request.json"

    # 1. Sign
    sign_result = sign_invoice(invoice_xml_path, signed_path)
    if not sign_result.get("ok"):
        return {"ok": False, "stage": "sign", **sign_result}

    # 1.5. Validate the signed XML
    validate_result = validate_invoice(signed_path)
    if not validate_result.get("ok"):
        return {"ok": False, "stage": "validate", **validate_result}
    if not validate_result.get("passed"):
        return {
            "ok": False,
            "stage": "validate",
            "error": "Local validation failed on the signed invoice",
            "details": validate_result.get("details", []),
            "raw": validate_result.get("raw", ""),
        }


    # 2. Build request
    build_result = build_request(signed_path, request_path)
    if not build_result.get("ok"):
        return {
            "ok": False,
            "stage": "build",
            "signed_path": signed_path,
            **build_result,
        }

    # 3. Submit
    submit_result = submit(invoice_type_code, build_result["body"],
                           env=env, cert_type=cert_type,
                           invoice_type_name=invoice_type_name)
    if not submit_result.get("ok"):
        return {
            "ok": False,
            "stage": "submit",
            "signed_path": signed_path,
            "request_path": request_path,
            **submit_result,
        }

    return {
        "ok": True,
        "signed_path": signed_path,
        "request_path": request_path,
        "body": build_result["body"],
        **submit_result,
    }


def summarize(response):
    """Extract status, clearance, and top errors from a ZATCA response."""
    if not isinstance(response, dict):
        return {"status": None, "clearance": None, "reporting": None,
                "errors": [], "warnings": []}

    vr = response.get("validationResults") or {}
    errs = vr.get("errorMessages") or []
    warns = vr.get("warningMessages") or []

    # Detect the duplicate-invoice response shape.
    # ZATCA returns 409 with a Duplicate-Invoice errorMessage.
    duplicate = False
    for e in errs:
        cat = (e.get("category") or "").lower()
        code = (e.get("code") or "").lower()
        if "duplicate" in cat or "duplicate" in code:
            duplicate = True
            break

    status = vr.get("status")
    clearance = response.get("clearanceStatus")
    reporting = response.get("reportingStatus")

    if duplicate:
        # A 409 duplicate is not a failure — the invoice was already
        # accepted earlier. Normalise the summary to reflect that.
        status = "DUPLICATE"
        if reporting == "NOT_REPORTED":
            reporting = "REPORTED"
        # Clearance duplicates arrive as 208, handled separately.

    return {
        "status": status,
        "clearance": clearance,
        "reporting": reporting,
        "errors": [e.get("message") for e in errs][:5],
        "warnings": [w.get("message") for w in warns][:5],
        "duplicate": duplicate,
    }

    """Extract status, clearance, and top errors from a ZATCA response."""
    if not isinstance(response, dict):
        return {"status": None, "clearance": None, "reporting": None, "errors": []}

    vr = response.get("validationResults") or {}
    errs = vr.get("errorMessages") or []
    warns = vr.get("warningMessages") or []

    return {
        "status": vr.get("status"),
        "clearance": response.get("clearanceStatus"),
        "reporting": response.get("reportingStatus"),
        "errors": [e.get("message") for e in errs][:5],
        "warnings": [w.get("message") for w in warns][:5],
    }

def classify_response(http_status, response):
    """
    Normalize a ZATCA submission response into a clear outcome.

    Returns one of:
      SUBMITTED           - 200/202, normal acceptance
      DUPLICATE_CLEARED   - 208, same hash already cleared within 24h (B2B)
      DUPLICATE_REPORTED  - 409, same hash already reported within 24h (B2C)
      REJECTED            - any other non-2xx
      UNKNOWN             - could not classify
    """
    if http_status == 208:
        return "DUPLICATE_CLEARED"
    if http_status == 409:
        return "DUPLICATE_REPORTED"
    if http_status in (200, 202):
        return "SUBMITTED"
    if isinstance(http_status, int) and 400 <= http_status < 600:
        return "REJECTED"
    return "UNKNOWN"

# ----------------------------------------------------------------------
# Onboarding — CSR, Compliance CSID, Compliance checks, Production CSID
# ----------------------------------------------------------------------

import glob

def generate_csr(csr_config_path, csr_output, env="sandbox", force=False):
    """
    Generate a CSR + private key. The SDK writes the key with its own
    timestamped name; we find it after the run.

    Refuses to run if a CCSID exists at /app/credentials/compliance_csid.json,
    unless force=True. This prevents accidentally orphaning an active CSID.

    Returns: {ok, csr_path, key_path, stable_key_path, stdout}
    """
    # Safety: refuse to overwrite an active CCSID's key unless forced.
    # Running -csr creates a new key and overwrites credentials/private-key.pem,
    # which orphans any CCSID already issued. Subsequent signings fail with
    # "invalid-digital-signature" because the cert no longer has a matching key.
    csid_path = "/app/credentials/compliance_csid.json"
    if os.path.exists(csid_path) and not force:
        return {
            "ok": False,
            "error": "A CCSID already exists at " + csid_path + ". "
                     "Generating a new CSR will overwrite the matching private key "
                     "and orphan the current CSID. Delete the CSID file first, "
                     "or pass force=True to override.",
        }

    args = [
        "-csr",
        "-csrConfig", csr_config_path,
        "-generatedCsr", csr_output,
    ]
    if env == "sandbox":
        args.append("-nonprod")
    elif env == "simulation":
        args.append("-sim")

    stdout, stderr, rc = _run_fatoora(args, timeout=180)
    if rc != 0:
        return {"ok": False, "error": f"fatoora -csr failed (rc={rc})",
                "stdout": stdout[-500:], "stderr": stderr[-500:]}

    if os.path.exists("/app/credentials/compliance_csid.json"):
        return {
            "ok": False,
            "error": "A CCSID already exists. Generating a new CSR will orphan it. "
                     "Delete /app/credentials/compliance_csid.json first if you "
                     "intend to replace the current CSID."
        }
    if not os.path.exists(csr_output):
        return {"ok": False, "error": f"CSR not produced at {csr_output}"}

    # Find the newest .key file in /app
    candidates = sorted(glob.glob("/app/generated-private-key-*.key"), key=os.path.getmtime)
    if not candidates:
        return {"ok": False, "error": "No private key file found in /app"}

    # Copy the key to a stable location so it survives container restarts.
    # Without this, the key stays at /app/generated-private-key-<ts>.key which
    # is only reachable inside the running container. If the container is
    # recreated before we use the key, the CSID is orphaned.
    stable_key_path = "/app/credentials/private-key.pem"
    try:
        with open(candidates[-1], "r") as src:
            key_content = src.read()
        with open(stable_key_path, "w") as dst:
            dst.write(key_content)
        logging.info(f"generate_csr: copied key to {stable_key_path}")
    except Exception as e:
        logging.warning(f"generate_csr: could not copy key to stable location: {e}")
        # Not fatal — the timestamped key still works for this session.

    return {
        "ok": True,
        "csr_path": csr_output,
        "key_path": candidates[-1],
        "stable_key_path": stable_key_path,
        "stdout": stdout[-300:],
    }


def _basic_auth(token, secret):
    return base64.b64encode(f"{token}:{secret}".encode("utf-8")).decode("ascii")


def get_compliance_csid(csr_b64_path, otp, env="sandbox"):
    """
    Exchange a base64-encoded CSR + OTP for a Compliance CSID.

    Returns: {ok, requestID, binarySecurityToken, secret, raw}
    """
    if requests is None:
        return {"ok": False, "error": "requests library not installed"}

    with open(csr_b64_path, "r") as f:
        csr_b64 = f.read().strip()

    url = f"{ENDPOINTS[env]}/compliance"
    headers = {
        "Content-Type": "application/json",
        "Accept-Version": "V2",
        "Accept-Language": "en",
        "OTP": otp,
    }
    body = {"csr": csr_b64}

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=get_timeout())
    except Exception as e:
        return {"ok": False, "error": f"HTTP POST failed: {e}", "url": url}

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    if resp.status_code != 200:
        return {"ok": False, "http_status": resp.status_code,
                "url": url, "error": data.get("message", "unknown"),
                "raw": data}

    return {
        "ok": True,
        "http_status": resp.status_code,
        "requestID": data.get("requestID"),
        "binarySecurityToken": data.get("binarySecurityToken"),
        "secret": data.get("secret"),
        "raw": data,
    }


def submit_compliance_check(request_body, csid_token, csid_secret,
                            invoice_type_code="388", env="sandbox"):
    """
    Submit one compliance test invoice.

    request_body: the dict from build_request() — {"invoiceHash", "uuid", "invoice"}
    """
    if requests is None:
        return {"ok": False, "error": "requests library not installed"}

    url = f"{ENDPOINTS[env]}/compliance/invoices"
    headers = {
        "Content-Type": "application/json",
        "Accept-Version": "V2",
        "Accept-Language": "en",
        "Clearance-Status": "1" if str(invoice_type_code) == "388" else "0",
        "Authorization": f"Basic {_basic_auth(csid_token, csid_secret)}",
    }

    try:
        resp = requests.post(url, headers=headers, json=request_body, timeout=get_timeout())
    except Exception as e:
        return {"ok": False, "error": f"HTTP POST failed: {e}"}

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    return {
        "ok": resp.status_code in (200, 202),
        "http_status": resp.status_code,
        "response": data,
    }


def get_production_csid(compliance_request_id, csid_token, csid_secret,
                        env="sandbox"):
    """
    Exchange a Compliance CSID for a Production CSID.
    """
    if requests is None:
        return {"ok": False, "error": "requests library not installed"}

    url = f"{ENDPOINTS[env]}/production/csids"
    headers = {
        "Content-Type": "application/json",
        "Accept-Version": "V2",
        "Accept-Language": "en",
        "Authorization": f"Basic {_basic_auth(csid_token, csid_secret)}",
    }
    body = {"compliance_request_id": str(compliance_request_id)}

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=get_timeout())
    except Exception as e:
        return {"ok": False, "error": f"HTTP POST failed: {e}"}

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    if resp.status_code != 200:
        return {"ok": False, "http_status": resp.status_code,
                "error": data.get("message", "unknown"), "raw": data}

    return {
        "ok": True,
        "http_status": resp.status_code,
        "requestID": data.get("requestID"),
        "binarySecurityToken": data.get("binarySecurityToken"),
        "secret": data.get("secret"),
        "raw": data,
    }


def extract_cert_pem(binary_security_token):
    """Decode ZATCA's double-encoded binarySecurityToken to the inner base64 cert."""
    outer = base64.b64decode(binary_security_token)
    return outer.decode("utf-8")


def write_credentials_in_place(cert_inner_b64, key_file_path, base_dir):
    """
    Write cert.pem and private-key.pem in place (truncate, never replace),
    so the docker-compose bind mounts stay valid.
    """
    cert_path = os.path.join(base_dir, "cert.pem")
    key_path = os.path.join(base_dir, "private-key.pem")

    with open(cert_path, "w") as f:
        f.write(cert_inner_b64)

    with open(key_file_path) as f:
        key_data = f.read().strip()

    with open(key_path, "w") as f:
        f.write(key_data)

    return {"cert_path": cert_path, "key_path": key_path,
            "cert_len": len(cert_inner_b64), "key_len": len(key_data)}
