import traceback
import os
import json
import sys

# ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import SessionLocal  # noqa: E402
from ai_content import generate_thumbnail  # noqa: E402


def main():
    s = SessionLocal()
    c = s.query(__import__("db").Clip).filter_by(clip_id="s2").first()
    if not c:
        print("clip s2 not found")
        raise SystemExit(1)
    md = json.loads(c.metadata_json or "{}")
    src = md.get("source_path")
    print("source:", src)
    if not src or not os.path.exists(src):
        print("source missing or not found")
        raise SystemExit(1)

    out = os.path.join("outputs", "thumbnails", "s2.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        t = (c.start + c.end) / 2.0
        res = generate_thumbnail(src, t, md.get("text", ""), out)
        print("saved", res)
    except Exception:
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
