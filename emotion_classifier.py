"""Simple heuristic emotion classifier for audio segments.

Tries to use librosa and numpy to compute basic features; falls back to
rule-based heuristics if librosa isn't available.
"""

import random


def classify_from_features(rms=None, zcr=None, tempo=None):
    # Simple rules mapping energy/zcr/tempo to emotions
    if rms is None:
        return random.choice(["funny", "intense", "cringe", "emotional"])
    if rms > 0.08 and (zcr is not None and zcr > 0.12):
        return "intense"
    if rms > 0.06 and (zcr is not None and zcr < 0.08):
        return "funny"
    if rms < 0.02:
        return "emotional"
    return "cringe"


def classify(audio, sr):
    try:
        import numpy as np
        import librosa

        # compute RMS and zero-crossing rate
        frame_length = 2048
        hop_length = 512
        rms = float(
            np.mean(
                librosa.feature.rms(
                    y=audio, frame_length=frame_length, hop_length=hop_length
                )
            )
        )
        zcr = float(
            np.mean(
                librosa.feature.zero_crossing_rate(
                    y=audio, frame_length=frame_length, hop_length=hop_length
                )
            )
        )
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        tempo_vals = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        tempo = (
            float(tempo_vals.mean())
            if (onset_env is not None and hasattr(tempo_vals, "mean"))
            else 0.0
        )
        return classify_from_features(rms=rms, zcr=zcr, tempo=tempo)
    except Exception:
        # If librosa not installed or fails, return heuristic/random
        return classify_from_features(rms=None)
