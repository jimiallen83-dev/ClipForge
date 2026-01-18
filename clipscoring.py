def score_clip(clip):
    score = 0
    score += clip.get("emotion", 0) * 0.3
    score += clip.get("audio_energy", 0) * 0.25
    score += clip.get("speech_markers", 0) * 0.15
    score += clip.get("context_score", 0) * 0.15
    score += clip.get("pacing", 0) * 0.15
    return round(score * 100)
