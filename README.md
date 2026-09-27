# ubl_zatca — ZATCA Phase 2 E-Invoicing Pipeline

A free, self-hostable pipeline that turns JSON invoices into **ZATCA-compliant UBL XML**, signs them with XAdES-BES, submits them to the Fatoora gateway, and keeps a local audit trail.

Written for Saudi Arabian e-invoicing (Fatoora). Built on the official ZATCA SDK.

**No signup. No fees. No accounts.** Use as much or as little as you need.

---

## Table of contents

- [What this is](#what-this-is)
- [Architecture — local and remote](#architecture--local-and-remote)
- [Quick start](#quick-start)
- [The pipeline, step by step](#the-pipeline-step-by-step)
- [What's in this repo](#whats-in-this-repo)
- [API endpoints](#api-endpoints)
- [What's tested, what isn't](#whats-tested-what-isnt)
- [What this is not](#what-this-is-not)
- [Environments](#environments)
- [Configuration](#configuration)
- [Roadmap](#roadmap)
- [License](#license)

---

## What this is

ZATCA's Fatoora system requires every B2B and B2C invoice in Saudi Arabia to be issued as signed UBL 2.1 XML, submitted through their gateway. This repo contains one implementation of that flow.

It handles four things:

1. **Generate** — take a JSON invoice and produce UBL XML
2. **Sign** — apply an XAdES-BES signature using your ZATCA-issued certificate
3. **Submit** — post the signed invoice to ZATCA's sandbox, simulation, or production gateway
4. **Log** — record every submission with full request/response for audit

The whole thing runs in Docker. Two containers: a Flask app and a MySQL database.

---

## Architecture — local and remote

The project is split into two halves that can run separately or together.

### Local (this repo, this Docker image)

Everything in this repository. A Flask server plus MySQL, deployed on your network. It:

- Receives invoice JSON (HTTP POST)
- Stores it in local MySQL
- Calls the remote server to generate XML
- Runs the resulting XML through the local ZATCA SDK for validation
- Signs the validated XML with your CSID
- Submits the signed invoice to ZATCA
- Stores the ZATCA response in the `SubmissionLog` table

Your invoice data never leaves your network except for the XML generation call.

### Remote (hosted at `ubl.keytouse.com`)

A small service that takes JSON, generates UBL XML, and returns it. Publicly available, free, single-invoice only. It does not store your data — it holds only the most recent invoice for up to 24 hours.

**The remote code is not in this repo.** If you want to run the whole stack yourself without depending on `ubl.keytouse.com`, you'd need to write the XML generator yourself. That's the only piece missing from this repository for a fully self-contained deployment.

If you just want to use it, you don't need to care — the local stack calls the remote automatically.

---

## Quick start

### Prerequisites

- Docker or Podman
- ~2 GB free disk space
- Outbound HTTPS access to `gw-fatoora.zatca.gov.sa` and `ubl.keytouse.com`

### 1. Pull the image

```bash
docker pull keytouse/ubl_zatca:ktuzatca-flask-app-beta-1.1
```

### 2. Create a working directory

```bash
mkdir zatca-local && cd zatca-local
```

### 3. Extract the application files

```bash
docker run --rm --entrypoint tar \
  keytouse/ubl_zatca:ktuzatca-flask-app-beta-1.1 \
  -cf - -C /app \
  --exclude=jdk11 --exclude=ZatcaSDK --exclude=__pycache__ \
  . | tar -xf -
```

This copies `app.py`, `zatca_client.py`, `InsertIntoDB.py`, `DeleteInvoice.py`, `xmlToSDK.py`, `required_invoice_elements.json`, `schema.sql`, and supporting files into your current directory.

### 4. Create `docker-compose.yml`

```yaml
services:
  flask-app:
    image: keytouse/ubl_zatca:ktuzatca-flask-app-beta-1.1
    container_name: ktuzatca-flask-app
    ports:
      - "5000:5000"
    environment:
      - ZATCA_ENV=sandbox
      - ZATCA_CSID_PATH=/app/credentials/compliance_csid.json
    volumes:
      - ./app.py:/app/app.py:ro
      - ./zatca_client.py:/app/zatca_client.py:ro
      - ./InsertIntoDB.py:/app/InsertIntoDB.py:ro
      - ./DeleteInvoice.py:/app/DeleteInvoice.py:ro
      - ./xmlToSDK.py:/app/xmlToSDK.py:ro
      - ./required_invoice_elements.json:/app/required_invoice_elements.json:ro
      - ./init_config.json:/app/init_config.json:ro
      - ./upload.html:/app/upload.html:ro
      - ./credentials:/app/credentials
      - ./credentials/cert.pem:/app/ZatcaSDK/Data/Certificates/cert.pem
      - ./credentials/private-key.pem:/app/ZatcaSDK/Data/Certificates/ec-secp256k1-priv-key.pem
    networks:
      - my_network
    depends_on:
      - mysql

  mysql:
    image: keytouse/ubl_zatca:mysql-8.0.39
    container_name: ktuzatca-mysql-1
    environment:
      # CHANGE THIS before deploying. The default is a public demo value.
      MYSQL_ROOT_PASSWORD: TheRoot@Pass
      MYSQL_DATABASE: keytouse_zatca
    volumes:
      - mysql_data:/var/lib/mysql
      - ./schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    networks:
      - my_network

networks:
  my_network:
    driver: bridge

volumes:
  mysql_data: {}
```

**Important:** change `MYSQL_ROOT_PASSWORD` to your own value before deploying. The default is a public demo value.

Port 3306 is intentionally not exposed to the host — MySQL is only reachable from inside the Docker network.

### 5. Start the stack

```bash
docker compose up -d
```

Wait about 15 seconds for MySQL to initialize and load the schema.

### 6. Verify

```bash
curl http://localhost:5000/hi
# -> Hello there!
```

If Flask responds, the stack is ready.

### 7. Try it

Send an invoice and get an XML back:

```bash
curl -X POST -F "file=@invoice.json" http://localhost:5000/upload
```

Expected response:

```json
{"message": "XML invoice passed local checks and is ready for ZATCA."}
```

That's the pipeline working end to end without ZATCA credentials — the local server called the remote for XML, validated it with the SDK, and returned success.

To actually submit to ZATCA, you need a CSID (certificate + secret). See [The pipeline, step by step](#the-pipeline-step-by-step) below.

---

## The pipeline, step by step

If you want to go from "nothing" to "cleared invoice at ZATCA," this is the full sequence. The examples use **Simulation** — ZATCA's pre-production environment. Sandbox uses the same flow with fixed credentials.

### Stage 1 — Generate a CSR and private key

```bash
curl -X POST http://localhost:5000/zatca/onboard/csr \
  -H "Content-Type: application/json" \
  -d '{"env": "simulation", "config": "/app/credentials/csr-config-simulation.properties"}'
```

Returns a `csr_path` and a `key_path`. The route also copies the private key to `/app/credentials/private-key.pem` (the mounted path), so it survives container restarts.

Change `"env"` to `"sandbox"` or `"production"` for those environments. Each uses a different certificate template inside the CSR:

| Environment | CSR template |
|-------------|--------------|
| Sandbox | `TSTZATCA-Code-Signing` |
| Simulation | `PREZATCA-Code-Signing` |
| Production | `ZATCA-Code-Signing` |

### Stage 2 — Exchange CSR + OTP for a Compliance CSID

You need an OTP from the Fatoora portal. Sandbox uses the fixed value `123456`. Simulation and Production require a real OTP from the portal's Onboarding section.

```bash
curl -X POST http://localhost:5000/zatca/onboard/compliance \
  -H "Content-Type: application/json" \
  -d '{"otp": "<YOUR_OTP>", "env": "simulation"}'
```

Returns a `requestID`, a `binarySecurityToken`, and a `secret`. The route saves the whole response to `/app/credentials/compliance_csid.json`.

**The Compliance CSID is valid for 24 hours.** Complete the remaining stages within that window, or the CSID expires and you'll need to request a fresh OTP.

### Stage 3 — Extract the certificate onto the host

ZATCA returns the certificate double-encoded (base64 of base64). Decode it once and save to the mounted `cert.pem`:

```bash
python3 << 'EOF'
import json, base64
d = json.load(open('credentials/compliance_csid.json'))
inner = base64.b64decode(d['binarySecurityToken']).decode('utf-8')
with open('credentials/cert.pem', 'w') as f:
    f.write(inner)
print("cert.pem:", len(inner), "bytes")
EOF
```

The private key was already saved in Stage 1. No further action needed.

> **Don't regenerate the CSR.** The key that pairs with the cert was created in Stage 1. Running Stage 1 again produces a new key and orphans the CSID. The `generate_csr()` function now refuses to run if a CCSID exists, to prevent this.

### Stage 4 — Stage a sample invoice

```bash
curl -X POST -F "file=@invoice.json" http://localhost:5000/upload
```

Expected: `{"message":"XML invoice staged..."}`. The XML is written to `/app/invoice.xml`.

### Stage 5 — Run the six compliance checks

For a new EGS (device) with `csr.invoice.type=1100`, ZATCA requires six compliance checks before issuing a Production CSID:

| # | Scenario | `InvoiceTypeCode` | `InvoiceTypeName` |
|---|----------|-------------------|-------------------|
| 1 | Standard Tax Invoice | `388` | `0100000` |
| 2 | Standard Credit Note | `381` | `0100000` |
| 3 | Standard Debit Note | `383` | `0100000` |
| 4 | Simplified Tax Invoice | `388` | `0200000` |
| 5 | Simplified Credit Note | `381` | `0200000` |
| 6 | Simplified Debit Note | `383` | `0200000` |

For each scenario, edit `invoice.json` to set the two fields, then stage and submit:

```bash
curl -X POST -F "file=@invoice.json" http://localhost:5000/upload
curl -X POST http://localhost:5000/zatca/submit \
  -H "Content-Type: application/json" \
  -d '{"invoiceid": "INV001"}'
```

Expected per submission: `status: "PASS"` with either `clearance: "CLEARED"` (Standard) or `reporting: "REPORTED"` (Simplified).

Credit and Debit notes require `cac:BillingReference` and `cac:PaymentMeans/cbc:InstructionNote` in the XML. The remote generator adds these automatically based on `InvoiceTypeCode`.

`/zatca/submit` automatically uses the Compliance CSID until a Production CSID exists, then switches to the Production CSID. No code change is needed as you move between stages.

### Stage 6 — Request the Production CSID

After all six compliance checks pass:

```bash
curl -X POST http://localhost:5000/zatca/onboard/production \
  -H "Content-Type: application/json" \
  -d '{"env": "simulation"}'
```

Returns the new `binarySecurityToken`, `secret`, and a new `requestID`. Saved to `/app/credentials/production_csid.json`.

The route writes the new cert to `/app/credentials/cert.pem`. The **private key is not touched** — ZATCA issues the Production CSID for the same key pair as the CCSID.

### Stage 7 — Submit with the Production CSID

Now `/zatca/submit` uses the production clearance/reporting endpoints instead of the compliance endpoint. No code change needed — the route detects the PCSID automatically.

```bash
curl -X POST -F "file=@invoice.json" http://localhost:5000/upload
curl -X POST http://localhost:5000/zatca/submit \
  -H "Content-Type: application/json" \
  -d '{"invoiceid": "INV001"}'
```

Every submission is recorded in `SubmissionLog`:

```bash
podman exec -i ktuzatca-mysql-1 mysql -uroot -pTheRoot@Pass -t keytouse_zatca << 'EOF'
SELECT ID, InvoiceID, Environment, HTTPStatus, ZATCAStatus, ClearanceStatus, SubmittedAt
FROM SubmissionLog
ORDER BY ID DESC LIMIT 5;
EOF
```

### Onboarding against Production

Everything above can be run against Simulation without affecting any real tax filing. To onboard against the real Production environment:

1. Repeat Stage 1 with `"env": "production"` — requires a CSR config using the `ZATCA-Code-Signing` template
2. Repeat Stage 2 with a Production OTP
3. Run all six compliance checks — **these become real legal filings**
4. Request the Production CSID — valid for real invoicing
5. Submit real invoices to `/e-invoicing/core/...`

Production onboarding affects the taxpayer's tax record and cannot be undone. It requires their explicit consent.

---

## What's in this repo

| File | Purpose |
|------|---------|
| `app.py` | Flask application — all HTTP routes |
| `zatca_client.py` | SDK + HTTP wrappers: `sign_invoice()`, `build_request()`, `submit()`, and the onboarding functions |
| `InsertIntoDB.py` | Inserts invoice JSON into the local MySQL tables |
| `DeleteInvoice.py` | Deletes invoice rows (per-invoice and delete-all variants) |
| `xmlToSDK.py` | Runs the fatoora CLI to validate XML before submission |
| `required_invoice_elements.json` | The schema — defines which tables and columns each invoice type needs |
| `schema.sql` | MySQL schema — creates all tables including `SubmissionLog` |
| `Dockerfile` | Original image build (SDK + JDK + Python) |
| `Dockerfile.update` | Layers current source over the base image (used for `beta-1.1`) |
| `entrypoint.sh` | Container startup — installs the SDK, then starts Flask |
| `docker-compose.yml` | Two-container stack definition |
| `requirements.txt` | Python dependencies |
| `invoice.json` | Sample invoice payload — used for testing |
| `sample_invoice.json` | Second sample — same structure, used in docs |
| `init_config.json` | Runtime config template |
| `upload.html` | Minimal browser upload form |
| `envVars.env` | Environment variable defaults for the container |

---

## API endpoints

### Invoice handling

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload` | POST | Upload `invoice.json` (multipart form, field `file`) |
| `/zatca/submit` | POST | Sign the staged invoice and submit to ZATCA |
| `/invoiceid?id=INV001` | GET/POST | Retrieve or store invoice data by ID |
| `/deleteinvoice?id=INV001` | DELETE | Remove a specific invoice |
| `/deleteall` | GET | Remove all invoices |

### Onboarding

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/zatca/onboard/csr` | POST | Generate CSR + private key |
| `/zatca/onboard/compliance` | POST | OTP → Compliance CSID |
| `/zatca/onboard/check` | POST | Submit one compliance test invoice |
| `/zatca/onboard/production` | POST | Compliance CSID → Production CSID |

### Diagnostics

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/hi` | GET | Returns `Hello there!` if Flask is alive |
| `/init_config` | GET | Returns the loaded config JSON |
| `/get_flag?name=X` | GET | Returns a single config value |
| `/cat?name=file` | GET | Returns a file's contents (debug only) |

### Request types (all of the above use POST with a JSON body)

The body is a **list** containing one or more request objects:

- `setdata` — upload a full invoice; generates and returns XML
- `getxml` — retrieve the current invoice as XML
- `getsetdata` — run a SQL query (SELECT, INSERT, UPDATE, DELETE, DESCRIBE, SHOW, EXPLAIN)

Example:

```bash
curl -X POST http://localhost:5000/upload \
  -H "Content-Type: application/json" \
  -d '[{"requesttype": "getsetdata", "query": "SELECT * FROM Invoice"}]'
```

---

## What's tested, what isn't

### Working today

- Full local stack: upload → DB insert → remote XML → local validation
- CSR generation and Compliance CSID onboarding
- XAdES-BES signing with a real ZATCA-issued certificate
- Submission to **ZATCA Sandbox** — `clearanceStatus: CLEARED`
- Submission to **ZATCA Simulation** — full onboarding verified end-to-end:
  Compliance CSID obtained, all 6 compliance checks passed, Production CSID
  issued, production clearance endpoint returns `CLEARED`
- Credit Notes (381) and Debit Notes (383) — generated with the required
  `BillingReference` and `PaymentMeans/InstructionNote` elements
- Duplicate invoice response handling (208 / 409)
- Audit log (`SubmissionLog`) with full request/response

### Not yet tested

- Submission to **ZATCA Production** — the real environment. Requires
  onboarding against `/e-invoicing/core` with a fresh OTP and a separate
  Production CSID. The code paths are identical to Simulation; only the
  endpoint URL and certificate differ.
- Real-world invoice variety beyond the sample


---

## What this is not

- **Not a ZATCA SDK replacement.** We use their SDK. The signing, validation, and canonicalisation are theirs.
- **Not a billing system.** No invoicing history beyond the local database.
- **Not a signed-invoice archive.** We don't persist the signed XML after submission.
- **Not multi-tenant.** The remote is single-invoice.
- **Not tied to Saudi Arabia only in design.** The UBL layer is generic; ZATCA-specific rules are what this repo implements.

---
## Environments

All endpoints use **`gw-fatoora.zatca.gov.sa`** — the current domain. The older `gw-apic-gov.gazt.gov.sa` was decommissioned on 14 Sep 2025 and no longer resolves.

| Environment | Base URL | Purpose |
|-------------|----------|---------|
| Sandbox | `https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal` | Fixed OTP (`123456`), demo certs. Educational only — does not validate against real rules. |
| Simulation | `https://gw-fatoora.zatca.gov.sa/e-invoicing/simulation` | Real ZATCA-issued certs. Pre-production rehearsal. Requires a real Taxpayer TIN and portal OTP. |
| Production | `https://gw-fatoora.zatca.gov.sa/e-invoicing/core` | Live invoicing. Requires a Production CSID. |

Each environment exposes the same five endpoints:

```
{base}/compliance                 request a Compliance CSID
{base}/compliance/invoices        run compliance checks
{base}/production/csids           request or renew a Production CSID
{base}/invoices/clearance/single  Clearance API (B2B standard invoices)
{base}/invoices/reporting/single  Reporting API (B2C simplified invoices)
```

Set the target environment with the `ZATCA_ENV` environment variable. See [Configuration](#configuration) below.

### Duplicate invoice responses (208 / 409)

ZATCA added runtime duplicate validation in 2025. Submitting the same invoice hash within 24 hours returns:

| HTTP | Environment | Meaning |
|------|-------------|---------|
| **208** | Clearance (B2B) | Invoice hash previously submitted. Response includes the original cleared invoice with ZATCA's signature and QR. |
| **409** | Reporting (B2C) | Invoice was already reported successfully. |

**Both are success indicators, not failures.** The `reportingStatus: NOT_REPORTED` field in a 409 body is a response artifact — the invoice *was* accepted on the first submission. ZATCA's official guidance:

> "When taxpayers receive 409 response, it is implied that B2C invoice with same hash value was successfully reported in first instance and saved at ZATCA's end."

**Do not resend.** Retrying the same payload triggers the duplicate check again and does not change the outcome. Internally, mark the invoice as `REPORTED` (for 409) or `CLEARED` (for 208).

This implementation classifies these responses as `DUPLICATE_REPORTED` or `DUPLICATE_CLEARED` in `zatca_client.classify_response()`. In `SubmissionLog`:

- 208 is recorded with `clearance_status: CLEARED`
- 409 is recorded with `reporting_status: REPORTED`
- Neither is recorded as an error

The realistic scenario this protects against is a **dropped response**: the ERP submits, ZATCA processes, the response is lost (timeout or connection reset), and the ERP retries. Without this handling, the retry would look like a failure even though the invoice was already accepted.

**Sandbox does not enforce this check.** It only applies to Simulation and Production. Testing against Sandbox will not reproduce these codes.

## Configuration

Environment variables (all optional):

| Variable | Default | Purpose |
|----------|---------|---------|
| `ZATCA_ENV` | `sandbox` | One of `sandbox`, `simulation`, `production` |
| `ZATCA_CSID_PATH` | `/app/credentials/compliance_csid.json` | Where the CSID JSON lives |
| `ZATCA_TIMEOUT` | `30` | HTTP timeout in seconds |

The DB credentials are hardcoded in `app.py`, `InsertIntoDB.py`, and `DeleteInvoice.py` as `root / TheRoot@Pass / ktuzatca-mysql-1 / keytouse_zatca`. Change them in all four places (including `docker-compose.yml`) if you deploy outside a test environment.

---

## Roadmap

- [ ] Automate the 6 compliance test invoices
- [ ] Open-source the remote XML generator
- [ ] In-memory XML generation (no local DB in the hot path)
- [ ] Per-invoice storage on the remote (remove the single-invoice restriction)
- [ ] Country adapters (Finland, Peppol, India GST)
- [ ] Server-side signing without the fatoora CLI

---

## License

MIT — see [LICENSE](LICENSE).

You can use, modify, and redistribute this code for any purpose, including commercially. No attribution required.

---

## Acknowledgements

Built on the official ZATCA E-Invoicing SDK (version 238-R3.3.8). The hard parts — signing, canonicalisation, validation — are theirs. This repo is the plumbing around them.

Hosted remote at [ubl.keytouse.com](https://ubl.keytouse.com). Docker image at [hub.docker.com/r/keytouse/ubl_zatca](https://hub.docker.com/r/keytouse/ubl_zatca).
