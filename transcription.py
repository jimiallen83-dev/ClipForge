try:
    import whisper

    _whisper_model = whisper.load_model("base")

    def transcribe(audio_path: str):
        result = _whisper_model.transcribe(audio_path)
        return result.get("segments", [])
except Exception:

    def transcribe(audio_path: str):
        # Fallback stub if whisper isn't installed or fails to load.
        return [
            {
                "start": 0.0,
                "end": 0.0,
                "text": "(transcription unavailable - install whisper)",
            }
        ]
