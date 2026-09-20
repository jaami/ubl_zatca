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

If you want to go from "nothing" to "cleared invoice at ZATCA," this is the full sequence.

### Stage 1 — Generate a CSR and private key

```bash
curl -X POST http://localhost:5000/zatca/onboard/csr \
  -H "Content-Type: application/json" \
  -d '{"env": "sandbox"}'
```

Returns the path to the generated CSR and the private key. The key is written to `/app/generated-private-key-<timestamp>.key` inside the container.

### Stage 2 — Exchange CSR + OTP for a Compliance CSID

You need an OTP from the Fatoora portal. For sandbox, the fixed OTP is `123456`.

```bash
curl -X POST http://localhost:5000/zatca/onboard/compliance \
  -H "Content-Type: application/json" \
  -d '{"otp": "123456", "env": "sandbox"}'
```

Returns a `requestID`, a `binarySecurityToken`, and a `secret`. The route saves the whole response to `/app/credentials/compliance_csid.json`.

### Stage 3 — Place the cert and key into the mount

The CSID response needs to be extracted into a cert file and paired with the private key from Stage 1:

```bash
# Decode the cert (ZATCA double-encodes it — this is normal)
python3 << 'EOF'
import json, base64
d = json.load(open('credentials/compliance_csid.json'))
inner = base64.b64decode(d['binarySecurityToken']).decode('utf-8')
with open('credentials/cert.pem', 'w') as f:
    f.write(inner)
print("cert.pem:", len(inner), "bytes")
EOF

# Pull the matching private key from the container
KEY=$(podman exec ktuzatca-flask-app ls -t /app/generated-private-key-*.key | head -1)
podman exec ktuzatca-flask-app cat "$KEY" > credentials/private-key.pem
```

### Stage 4 — Submit an invoice

```bash
# Stage an invoice first
curl -X POST -F "file=@invoice.json" http://localhost:5000/upload

# Sign + submit
curl -X POST http://localhost:5000/zatca/submit \
  -H "Content-Type: application/json" \
  -d '{"invoiceid": "INV001"}'
```

On success, the response contains `clearanceStatus: "CLEARED"` and an empty `errorMessages` array.

Every submission is recorded in the `SubmissionLog` table:

```bash
podman exec -i ktuzatca-mysql-1 mysql -uroot -pTheRoot@Pass -t keytouse_zatca << 'EOF'
SELECT ID, InvoiceID, Environment, HTTPStatus, ZATCAStatus, ClearanceStatus, SubmittedAt
FROM SubmissionLog
ORDER BY ID DESC LIMIT 5;
EOF
```

### Optional — Production CSID

If you have a real Taxpayer TIN and access to the Fatoora portal, you can exchange the Compliance CSID for a Production CSID:

```bash
curl -X POST http://localhost:5000/zatca/onboard/production \
  -H "Content-Type: application/json" \
  -d '{"env": "simulation"}'
```

**Note:** the sandbox environment returns a demo certificate for this call, not a real Production CSID. The route detects this and refuses to overwrite your working cert. Real Production CSIDs require simulation or production onboarding with a real TIN.

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
- Submission to the **ZATCA Sandbox** gateway — `clearanceStatus: CLEARED`
- Audit log (`SubmissionLog`) with full request/response

### Not yet tested

- Submission to **Simulation** or **Production** — the code paths are the same, but they require a real Taxpayer TIN, which we don't have for testing
- The 6 mandatory compliance test invoices — the routes exist but currently submit one invoice at a time
- The remote XML generator (not in this repo)

---

## What this is not

- **Not a ZATCA SDK replacement.** We use their SDK. The signing, validation, and canonicalisation are theirs.
- **Not a billing system.** No invoicing history beyond the local database.
- **Not a signed-invoice archive.** We don't persist the signed XML after submission.
- **Not multi-tenant.** The remote is single-invoice.
- **Not tied to Saudi Arabia only in design.** The UBL layer is generic; ZATCA-specific rules are what this repo implements.

---

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
