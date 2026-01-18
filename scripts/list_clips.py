import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import SessionLocal, Clip  # noqa: E402


def main():
    s = SessionLocal()
    clips = s.query(Clip).filter_by(project_id=1).all()
    for c in clips:
        print(
            c.clip_id,
            "approved=",
            c.approved,
            "renderer_status=",
            getattr(c, "renderer_status", None),
        )
    s.close()


if __name__ == "__main__":
    main()
