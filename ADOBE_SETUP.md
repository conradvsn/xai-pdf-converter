# Adobe PDF Services Setup Guide

## Why Adobe PDF Services?

✅ **Industry Standard** - Same technology used by Adobe Acrobat
✅ **Best Quality** - Superior conversion compared to open-source alternatives
✅ **Automatic OCR** - Handles scanned PDFs automatically
✅ **Complex PDFs** - Handles multi-column layouts, forms, tables perfectly
✅ **FREE Tier** - 500 conversions per month at no cost

---

## Quick Setup (3 steps)

### Step 1: Install the SDK

```bash
pip install pdfservices-sdk
```

### Step 2: Get FREE Adobe Credentials

1. Go to: https://acrobatservices.adobe.com/dc-integration-creation-app-cdn/main.html
2. Sign in with your Adobe account (or create one - it's free!)
3. Click **"Create New Credentials"**
4. Select **"PDF Services API"**
5. Copy your **Client ID** and **Client Secret**

### Step 3: Configure Credentials

**Option A: Environment Variables (Recommended)**

```bash
export ADOBE_CLIENT_ID="your_client_id_here"
export ADOBE_CLIENT_SECRET="your_client_secret_here"
```

For permanent setup, add to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export ADOBE_CLIENT_ID="your_client_id"' >> ~/.bashrc
echo 'export ADOBE_CLIENT_SECRET="your_client_secret"' >> ~/.bashrc
source ~/.bashrc
```

**Option B: Credentials File**

Create `pdfservices-api-credentials.json` in the project root:

```json
{
  "client_credentials": {
    "client_id": "your_client_id_here",
    "client_secret": "your_client_secret_here"
  }
}
```

---

## Verify Setup

Run the application:

```bash
python main.py
```

The main menu should show:
```
1. Convert PDF → Word              [✅ Adobe PDF (Premium)]
```

If you see `[⚠️  pdf2docx (Fallback)]`, Adobe is not configured yet.

---

## Free Tier Limits

- **500 conversions/month** for FREE
- No credit card required
- Perfect for personal and small business use
- If you need more, upgrade to paid tier

---

## Troubleshooting

### "Adobe credentials not found"

Make sure your credentials are set correctly:

```bash
# Check environment variables
echo $ADOBE_CLIENT_ID
echo $ADOBE_CLIENT_SECRET

# Or check if credentials file exists
ls -la pdfservices-api-credentials.json
```

### "Adobe conversion failed"

The system will automatically fall back to pdf2docx if Adobe fails.

Check the error message for details (invalid credentials, API limit reached, etc.)

### Need Help?

- Adobe Documentation: https://developer.adobe.com/document-services/docs/overview/
- Support: https://community.adobe.com/

---

**© 2025 Conrad Vaslin - xAI Finance Tutor**
