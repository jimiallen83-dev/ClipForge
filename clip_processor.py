"""Process audio/video into scored clips for a project.

Functions:
- process_audio_for_project(audio_path, project_id)

This module uses `transcription.transcribe` (Whisper) and `librosa` for audio features.
"""

from transcription import transcribe
import librosa
import numpy as np
from emotion_classifier import classify
import db


def compute_audio_energy(y):
    # RMS energy
    return float(np.mean(librosa.feature.rms(y=y)))


def detect_speech_markers(y, sr):
    # Use non-silent intervals as speech markers
    intervals = librosa.effects.split(y, top_db=30)
    # return number of voice segments within the clip
    return len(intervals)


def viral_score_calc(emotion_label, audio_energy, speech_markers, duration):
    # Reuse weighted scoring idea — map emotion to weight
    emotion_weights = {
        "funny": 1.2,
        "intense": 1.3,
        "cringe": 0.7,
        "emotional": 1.1,
    }
    e_w = emotion_weights.get(emotion_label, 1.0)
    score = 0
    score += e_w * 0.4
    score += min(audio_energy * 10, 1.0) * 0.3
    score += min(speech_markers / max(1, duration), 1.0) * 0.2
    score += min(duration / 10.0, 1.0) * 0.1
    # Normalize to 0-100
    return round(score * 100, 2)


def process_audio_for_project(audio_path: str, project_id: int):
    # transcribe -> get segments with start/end
    segments = transcribe(audio_path)
    # load audio
    y, sr = librosa.load(audio_path, sr=None)

    session = db.SessionLocal()
    try:
        for i, seg in enumerate(segments):
            start = seg.get("start", 0.0)
            end = seg.get("end", start + 1.0)
            # extract audio slice
            s_frame = int(start * sr)
            e_frame = int(end * sr)
            audio_slice = y[s_frame:e_frame]

            audio_energy = (
                compute_audio_energy(audio_slice) if len(audio_slice) > 0 else 0.0
            )
            speech_markers = (
                detect_speech_markers(audio_slice, sr) if len(audio_slice) > 0 else 0
            )
            emotion = classify(audio_slice, sr) if len(audio_slice) > 0 else "unknown"
            duration = end - start
            score = viral_score_calc(emotion, audio_energy, speech_markers, duration)

            clip_id = f"{project_id}-{i}-{int(start * 1000)}"
            metadata = {
                "text": seg.get("text", ""),
                "audio_energy": audio_energy,
                "speech_markers": speech_markers,
            }
            db.create_clip(
                session, project_id, clip_id, start, end, score, emotion, metadata
            )
    finally:
        session.close()
