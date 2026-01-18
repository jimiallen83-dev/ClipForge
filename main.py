from clipscoring import score_clip
from longform_builder import build_longform


def make_sample_clips():
    clips = [
        {
            "id": "a",
            "duration": 10,
            "emotion": 0.8,
            "audio_energy": 0.6,
            "speech_markers": 0.5,
            "context_score": 0.7,
            "pacing": 0.6,
        },
        {
            "id": "b",
            "duration": 20,
            "emotion": 0.4,
            "audio_energy": 0.7,
            "speech_markers": 0.6,
            "context_score": 0.5,
            "pacing": 0.4,
        },
    ]
    for c in clips:
        c["score"] = score_clip(c)
    return clips


def main():
    clips = make_sample_clips()
    timeline = build_longform(clips, target_minutes=1)
    print("Sample clips with scores:")
    for c in clips:
        print(f"- {c['id']}: score={c['score']}, duration={c['duration']}")
    print("\nBuilt timeline (first items up to target duration):")
    for t in timeline:
        print(f"- {t['id']} (duration {t['duration']})")


if __name__ == "__main__":
    main()
