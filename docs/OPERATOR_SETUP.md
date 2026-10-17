# FraudLens operator setup

This file separates what works without credentials from integrations that require an account,
consent, hardware, or a commercial agreement. Put secrets in the repository root `.env` only.
Never commit `.env`.

## Available without a key

- **ICANN RDAP domain facts**: open **Public intelligence** in the sidebar and enter a domain.
  FraudLens stores the public response URL, provider, facts, and fetch timestamp. Registration
  metadata is context and never becomes a fraud verdict by itself.
- **Deterministic email/document/URL rules**: upload supported evidence to a case.
- **PDF, DOCX, TXT extraction**: built in.
- **Analyst case disposition**: Confirmed fraud, False positive, or Inconclusive plus notes.

The default `demo` tenant contains sample records, including the 92-risk case. The dashboard now
labels these records `DEMO DATASET`. They are not public intelligence.

## Values you must create

### Groq narrative generation (optional)

1. Create a key in the Groq console.
2. Add to root `.env`:

   ```dotenv
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_key
   GROQ_BASE_URL=https://api.groq.com/openai/v1
   GROQ_MODEL=openai/gpt-oss-20b
   ```

The LLM writes a cited narrative only. It cannot change the deterministic score.

### Gmail connector (not yet implemented)

Create a Google Cloud project, enable Gmail API, configure the OAuth consent screen, and create a
Web application OAuth client. For local development, register this redirect URI:

`http://localhost:8000/api/v1/connectors/google/callback`

Planned root `.env` entries:

```dotenv
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/connectors/google/callback
```

Use minimum read-only scopes and a dedicated test mailbox first. Do not provide your password.

### Microsoft 365 / Outlook connector (not yet implemented)

Create an app registration in Microsoft Entra ID, add Microsoft Graph delegated `Mail.Read`, and
register this local redirect URI:

`http://localhost:8000/api/v1/connectors/microsoft/callback`

Planned root `.env` entries:

```dotenv
MICROSOFT_TENANT_ID=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/connectors/microsoft/callback
```

### URLhaus malware-URL feed (not yet implemented)

Create a free URLhaus Auth-Key and add `URLHAUS_AUTH_KEY=` to root `.env`. URLhaus is malware URL
intelligence, not a complete phishing verdict. Review its fair-use/commercial terms before launch.

### Local OCR

Install Tesseract 5 and language packs on the API/worker host. No API key is needed. Tell the team
the executable path and languages required. OCR output is extracted text, not tamper proof.

### Malware scanning

Run ClamAV/clamd and add:

```dotenv
CLAMAV_ENABLED=true
CLAMAV_REQUIRED=true
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
```

### Video/audio authenticity

For experimental local evaluation, provide the GPU model and VRAM. DeepfakeBench and AASIST can
be evaluated locally, but their model/dataset licences and out-of-domain accuracy must be approved
before a production claim. Production identity verification normally requires a contracted vendor.

## Apply this release

From the actual project directory:

```powershell
cd C:\Users\DELL\Documents\Projects\AgenticAI\fraudlens-ai
.\.venv\Scripts\Activate.ps1
pip install -e ".\apps\api[dev]"
alembic -c apps/api/alembic.ini upgrade head
uvicorn fraudlens.main:app --app-dir apps/api/src --reload
```

In a second terminal:

```powershell
cd C:\Users\DELL\Documents\Projects\AgenticAI\fraudlens-ai
npm install
npm run dev
```

Then open `http://localhost:3000/intelligence`. If an old 92-style component remains after the new
`DEMO DATASET` label should be visible, stop the old Node process, restart from this exact directory,
and use Ctrl+F5.

## Next implementation order

1. Finding-level feedback and recalibration dataset.
2. Gmail and Microsoft OAuth connectors with encrypted token storage.
3. Supplier master and historical IBAN comparison.
4. Safe video URL/upload intake with SSRF, size, duration, MIME, and malware controls.
5. Tesseract worker and OCR confidence reporting.
6. DNS/email authentication and URLhaus enrichment.
7. Validated deepfake/audio/identity adapters after licence and accuracy approval.
