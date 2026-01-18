Summary of local fixes and how to run ClipForge locally

- Files changed to improve local dev startup:
  - `app.py`: guard router imports so missing optional packages don't stop startup; added root `/` endpoint and safe include helper.
  - `transcription.py`: guarded against missing `whisper` so import won't fail. (removed duplicate misspelled file)
  - `projects.py`: fixed remaining references to `metadata_json` to match DB schema.

Quick run steps (Windows / PowerShell):

1. Activate the venv (already in this repo):

```powershell
& .\.venv\Scripts\Activate.ps1
```

2. Start the server in foreground (keeps logs visible):

```powershell
.\restart_uvicorn.ps1
# wait for: "Uvicorn running on http://127.0.0.1:8000"
```

3. Open the app in your browser:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/health

Notes on optional ML dependencies:
- Heavy packages like `whisper`, `torch`, `whisperx`, `ctranslate2` are optional for basic web preview. Install them only if you need transcription or advanced processing (prefer a Conda env for GPU support).

If you want, I can prepare a git commit message for these changes — tell me how you'd like the commit titled.
