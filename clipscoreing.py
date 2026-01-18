def score_clip(clip):
    score = 0
    score += clip["emotion"] * 0.3
    score += clip["audio_energy"] * 0.25
    score += clip["speech_markers"] * 0.15
    score += clip["context_score"] * 0.15
    score += clip["pacing"] * 0.15
    return round(score * 100)
