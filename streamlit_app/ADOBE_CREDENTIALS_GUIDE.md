# 🔑 Adobe API Credentials Setup Guide

## Where to Add Credentials

Adobe API credentials can be added in **2 ways**:

### Method 1: Via Streamlit Settings Page ✅ Recommended

1. Launch the Streamlit app:
   ```bash
   cd streamlit_app
   ./run.sh
   ```

2. Go to **⚙️ Settings** page (in sidebar)

3. Scroll to **🔑 Adobe PDF Services API** section

4. Click **➕ Add New Adobe API Key**

5. Choose upload method:
   - **Upload JSON file**: Drag and drop your `pdfservices-api-credentials.json`
   - **Paste JSON content**: Copy/paste the JSON directly

6. Click **💾 Save Credentials**

7. Restart the app for changes to take effect

### Method 2: Create JSON File Manually

1. Create a file at: `/Users/conrad/Downloads/xAI/adobe_credentials.json`

2. Add your credentials in this format:

```json
[
  {
    "client_credentials": {
      "client_id": "YOUR_CLIENT_ID_HERE",
      "client_secret": "YOUR_CLIENT_SECRET_HERE"
    },
    "service_principal_credentials": {
      "organization_id": "YOUR_ORG_ID_HERE",
      "account_id": "YOUR_ACCOUNT_ID_HERE",
      "private_key_file": "private.key"
    }
  }
]
```

Or for multiple credentials:

```json
[
  {
    "client_id": "client_id_1",
    "client_secret": "secret_1"
  },
  {
    "client_id": "client_id_2",
    "client_secret": "secret_2"
  }
]
```

3. The app will automatically load them on startup

---

## How to Get Adobe API Credentials

### 1. Go to Adobe Developer Console

Visit: https://developer.adobe.com/console

### 2. Create or Select Project

- Click **Create new project** or select existing
- Give it a name like "xAI PDF Converter"

### 3. Add PDF Services API

- Click **Add API**
- Select **PDF Services API**
- Click **Next**

### 4. Create Credentials

- Choose **Service Account (JWT)** or **OAuth Server-to-Server**
- Generate key pair
- Download credentials

### 5. Download JSON

- Download the `pdfservices-api-credentials.json` file
- This contains all necessary credentials

---

## Credential File Structure

The Adobe credentials JSON should look like this:

```json
{
  "client_credentials": {
    "client_id": "abc123...",
    "client_secret": "p8e-xyz..."
  },
  "service_principal_credentials": {
    "organization_id": "org123...",
    "account_id": "acc456...",
    "private_key_file": "private.key"
  }
}
```

---

## Security Notes

⚠️ **IMPORTANT**:
- Never commit `adobe_credentials.json` to git
- The file is already in `.gitignore`
- Keep your credentials secret
- Don't share credentials publicly

✅ **Safe**:
- Store in `adobe_credentials.json` locally
- Add via Settings page in Streamlit
- Credentials are saved locally only

---

## Verifying Credentials

After adding credentials:

1. Go to **🏠 Home** page
2. Check **System Status** section
3. You should see: **✅ Adobe API: N key(s)**

If you see **⚠️ Adobe API: Not configured**, check:
- File exists at `/Users/conrad/Downloads/xAI/adobe_credentials.json`
- JSON format is correct
- Restart the Streamlit app

---

## Troubleshooting

### "Adobe API not configured" warning

**Solution**: Add credentials using Method 1 or 2 above

### "Invalid JSON" error

**Solution**:
- Check JSON syntax (use https://jsonlint.com/)
- Ensure quotes are correct
- No trailing commas

### Credentials not loading

**Solution**:
- Restart Streamlit app
- Check file path is correct
- Verify file permissions (should be readable)

### Multiple credentials not working

**Solution**:
- Ensure JSON is an array: `[{}, {}]`
- Each credential object must be valid
- Check for duplicate keys

---

## Example Files

### Single Credential

```json
[
  {
    "client_id": "1a2b3c4d5e6f7g8h",
    "client_secret": "p8e-abc123xyz789"
  }
]
```

### Multiple Credentials

```json
[
  {
    "client_id": "credential_set_1",
    "client_secret": "secret_1"
  },
  {
    "client_id": "credential_set_2",
    "client_secret": "secret_2"
  },
  {
    "client_id": "credential_set_3",
    "client_secret": "secret_3"
  }
]
```

The app will rotate through multiple credentials automatically!

---

## Need Help?

1. Check Adobe documentation: https://developer.adobe.com/document-services/docs/
2. Verify credentials in Adobe Console
3. Test credentials with Adobe SDK examples
4. Check Streamlit app logs for errors

---

**Remember**: Without Adobe credentials, you can still use **"Analyze Only"** mode which doesn't require conversion! ✨
