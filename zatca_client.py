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


def endpoint_for(env, invoice_type_code, cert_type="compliance"):
    """
    Return the submission URL for the environment + invoice type + cert type.

    cert_type:
      "compliance" -> /compliance/invoices       (Compliance CSID)
      "production" -> /invoices/clearance/single (Standard, Production CSID)
                   -> /invoices/reporting/single (Simplified, Production CSID)
    """
    base = ENDPOINTS[env]

    if cert_type == "compliance":
        return f"{base}/compliance/invoices"

    # Production endpoints
    code = str(invoice_type_code).strip()
    if code == "388":  # Standard -> clearance
        return f"{base}/invoices/clearance/single"
    if code == "389":  # Simplified -> reporting
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

def submit(invoice_type_code, body, env=None, cert_type="compliance"):
    """POST the request body to the ZATCA gateway."""
    if requests is None:
        return {"ok": False, "error": "requests library not installed"}

    if env is None:
        env = get_env()

    try:
        token, secret, _ = load_csid()
    except Exception as e:
        return {"ok": False, "error": f"CSID load failed: {e}"}

    url = endpoint_for(env, invoice_type_code, cert_type=cert_type)
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
                   cert_type="compliance"):
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
                           env=env, cert_type=cert_type)
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
