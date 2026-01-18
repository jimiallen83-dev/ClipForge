"""Export historical clip dataset for fine-tuning.

Produces a `dataset/manifest.jsonl` file with lines like:
  {"audio_path": "...", "text": "...", "emotion": "funny", "clip_id": "..."}

It will copy source files into `dataset/media/` if `metadata.source_path` is present.
"""

import os
import json
import shutil
from pathlib import Path
import db


def export_dataset(out_dir="dataset"):
    os.makedirs(out_dir, exist_ok=True)
    media_dir = os.path.join(out_dir, "media")
    os.makedirs(media_dir, exist_ok=True)
    manifest_path = os.path.join(out_dir, "manifest.jsonl")

    session = db.SessionLocal()
    try:
        clips = session.query(db.Clip).all()
        with open(manifest_path, "w", encoding="utf-8") as mf:
            for c in clips:
                md = json.loads(c.metadata_json or "{}")
                src = md.get("source_path")
                dest = None
                if src and os.path.exists(src):
                    ext = Path(src).suffix
                    dest_name = f"{c.clip_id}{ext}"
                    dest = os.path.join("media", dest_name)
                    dest_full = os.path.join(media_dir, dest_name)
                    try:
                        shutil.copy2(src, dest_full)
                    except Exception:
                        dest = None

                rec = {
                    "clip_id": c.clip_id,
                    "start": c.start,
                    "end": c.end,
                    "duration": c.duration,
                    "text": md.get("text"),
                    "emotion": c.emotion,
                }
                if dest:
                    rec["media_path"] = dest
                mf.write(json.dumps(rec, ensure_ascii=False) + "\n")

    finally:
        session.close()

    print(f"Exported manifest to {manifest_path}")


if __name__ == "__main__":
    export_dataset()
