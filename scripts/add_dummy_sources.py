import os
import sys
import json

# ensure project root is on sys.path for local script imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import SessionLocal, Clip  # noqa: E402


def main():
    s = SessionLocal()
    for clip_id in ["s3", "s4", "s5"]:
        path = os.path.abspath(os.path.join("outputs", f"source_{clip_id}.mp4"))
        open(path, "wb").close()
        c = s.query(Clip).filter_by(clip_id=clip_id).first()
        md = {"source_path": path, "text": f"dummy text for {clip_id}"}
        c.metadata_json = json.dumps(md)
        c.renderer_status = "not_rendered"
        print("updated", clip_id, path)
    s.commit()
    s.close()


if __name__ == "__main__":
    main()
