OAuth setup for ClipForge (YouTube)

This document shows the exact steps to create Google OAuth credentials, place the JSON into the repo, and run the authorize flow. It also explains where to take screenshots so I can guide you visually.

1) Install required libraries in your venv

```powershell
.\.venv\Scripts\Activate.ps1
pip install google-auth google-auth-oauthlib google-api-python-client isodate
```

2) Create Google Cloud credentials
- Open: https://console.cloud.google.com/apis/credentials
- Create or select a Project.
- In "APIs & Services -> Library" enable **YouTube Data API v3**.
- Go to "Credentials" -> Create Credentials -> OAuth client ID.
  - Application type: Web application
  - Name: ClipForge Local
  - Authorized redirect URIs: `http://localhost:8000/youtube/oauth2callback`
- Download the JSON and save it to the project root as `client_secrets.json`.

3) What to screenshot (if you want a guided walkthrough)
- Screenshot A: the APIs & Services -> Library page showing "YouTube Data API v3 enabled" (so I can confirm the API is enabled).
- Screenshot B: the Create OAuth Client dialog showing the redirect URI field and the chosen values.
- Screenshot C: the downloaded `client_secrets.json` file open (redact client_secret if you paste it here; you can paste the JSON structure with the secret value replaced by `REDACTED`).

4) Run the app and start the authorize flow

```powershell
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
# in browser open:
http://127.0.0.1:8000/youtube/authorize
```

- Follow the Google consent screen. After consent Google will redirect back to `http://localhost:8000/youtube/oauth2callback` and the server will exchange the code and fetch videos.

5) Troubleshooting
- "Create OAuth client secrets JSON at client_secrets.json": make sure the downloaded JSON filename is exactly `client_secrets.json` and in the repository root where you run the server.
- Redirect mismatch errors: ensure the exact redirect URI (including scheme and port) is registered in the Google Cloud Console.
- Missing libraries: run step (1).

6) Next steps I can do for you
- Walk you through the Google Console with screenshots (you provide the screenshots, I’ll point where to click). I can prepare annotated screenshot instructions if you prefer.
- Adjust scopes or request additional YouTube permissions if you want upload or content management beyond readonly/upload.


