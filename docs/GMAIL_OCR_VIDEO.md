# Gmail, OCR, and video inference

## Gmail

The Google OAuth client must register exactly:

`http://localhost:8000/api/v1/connectors/google/callback`

Set the four `GOOGLE_*` OAuth values in root `.env`. Also set a dedicated Fernet key:

```powershell
.\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy its output into `GOOGLE_TOKEN_ENCRYPTION_KEY`. Never commit `.env`. Apply migrations, start
both services, open `/connectors`, and choose **Connect Gmail**. The integration requests read-only
access, stores only an encrypted refresh token, validates single-use OAuth state, supports explicit
label/sender/date/attachment filters, and imports into an existing case. Disconnect revokes the
Google grant and deletes the local connection.

## OCR

Windows defaults:

```dotenv
OCR_ENABLED=true
OCR_LANGUAGES=eng+deu+spa+ita+urd+fra+ara
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
TESSDATA_PREFIX=C:\Users\DELL\Documents\Projects\AgenticAI\fraudlens-ai\.data\tessdata
POPPLER_PATH=C:\Program Files\poppler\Library\bin
```

Install Tesseract 5, the listed `tessdata_fast` language files, and Poppler for scanned PDFs.
Docker installs Tesseract, all seven languages, and Poppler. OCR produces page text, average word
confidence, selected languages/script, status, and errors. It never verifies authenticity.

## Video preparation

`fraudlens.video.VideoInferenceAdapter` defines the optional contract. Disabled and HTTP adapters
return explicit unknown/failed results, model version, uncertainty, frame/face counts, and audit
metadata. No weights or datasets are bundled. RetinaFace, SBI/Xception, and FTCN remain experimental;
approve the licences of code, weights, and training data before commercial use.

The `deploy/` examples describe a private `europe-west4` Cloud Run service with one NVIDIA L4,
minimum zero, maximum one, and a same-region Cloud Storage input bucket with lifecycle retention.
They are examples only and execute no deployment or billing action.
