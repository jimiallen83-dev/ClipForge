def _fmt_time(seconds: float) -> str:
    # Format seconds to SRT timestamp: HH:MM:SS,mmm
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_to_srt(segments, path):
    """Write Whisper-like segments (list with start,end,text) to SRT file."""
    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = seg.get("start", 0.0)
            end = seg.get("end", start + 1.0)
            text = seg.get("text", "")
            f.write(f"{i}\n")
            f.write(f"{_fmt_time(start)} --> {_fmt_time(end)}\n")
            f.write(text.strip() + "\n\n")
