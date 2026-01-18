from fastapi import APIRouter, HTTPException
import db
from fastapi import BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
import json
from ffmpeg_renderer import render_short
from srt_util import segments_to_srt
from longform_builder import arrange_for_longform
from ffmpeg_renderer import assemble_from_segments
from ai_content import (
    generate_titles_from_text,
    generate_thumbnail,
    generate_script_from_text,
    generate_tts_from_script,
)
from db import get_user_analytics
from redis import Redis
from rq import Queue

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)
rq_queue = Queue(connection=redis_conn)

templates = Jinja2Templates(directory="templates")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs", "shorts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

router = APIRouter(prefix="/projects")


@router.get("/{project_id}/clips")
def list_clips(project_id: int, limit: int = 100):
    session = db.SessionLocal()
    try:
        proj = session.query(db.Project).filter_by(id=project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        clips = db.get_clips_for_project(session, project_id, limit=limit)
        out = []
        for c in clips:
            out.append(
                {
                    "clip_id": c.clip_id,
                    "start": c.start,
                    "end": c.end,
                    "duration": c.duration,
                    "score": c.score,
                    "emotion": c.emotion,
                    "metadata": c.metadata_json,
                }
            )
        return {"project": proj.name, "clips": out}
    finally:
        session.close()


@router.get("/{project_id}/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, project_id: int):
    session = db.SessionLocal()
    try:
        proj = session.query(db.Project).filter_by(id=project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        clips = db.get_clips_for_project(session, project_id, limit=200)
        # analytics for project owner if available
        owner_analytics = None
        if proj.owner_id:
            owner_analytics = get_user_analytics(session, proj.owner_id)
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "project": proj,
                "clips": clips,
                "analytics": owner_analytics,
            },
        )
    finally:
        session.close()


@router.post("/{project_id}/clips/{clip_id}/approve")
def approve_clip(project_id: int, clip_id: str):
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            raise HTTPException(status_code=404)
        c.approved = "approved"
        session.commit()
        return {"status": "approved"}
    finally:
        session.close()


@router.post("/{project_id}/clips/{clip_id}/reject")
def reject_clip(project_id: int, clip_id: str):
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            raise HTTPException(status_code=404)
        c.approved = "rejected"
        session.commit()
        return {"status": "rejected"}
    finally:
        session.close()


def _render_and_update(clip_id, project_id):
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            return
        metadata = json.loads(c.metadata_json or "{}")
        source = metadata.get("source_path")
        if not source or not os.path.exists(source):
            c.renderer_status = "missing_source"
            session.commit()
            return

        # recreate srt from stored text if available
        segments = [{"start": c.start, "end": c.end, "text": metadata.get("text", "")}]
        srt_path = os.path.join(OUTPUT_DIR, f"{clip_id}.srt")
        segments_to_srt(segments, srt_path)
        out_path = os.path.join(OUTPUT_DIR, f"{clip_id}.mp4")
        c.renderer_status = "rendering"
        session.commit()
        render_short(source, c.start, c.end, srt_path, out_path)
        c.output_path = out_path
        c.renderer_status = "rendered"
        session.commit()
    finally:
        session.close()


@router.post("/{project_id}/clips/{clip_id}/render")
def render_clip(project_id: int, clip_id: str, background_tasks: BackgroundTasks):
    # enqueue rendering
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            raise HTTPException(status_code=404)
        # enqueue via RQ so workers can process
        try:
            job = rq_queue.enqueue(_render_and_update, clip_id, project_id)
            queued = True
            job_id = job.get_id()
        except Exception:
            # fallback to background tasks
            background_tasks.add_task(_render_and_update, clip_id, project_id)
            queued = False
            job_id = None
        return {"status": "queued", "via_rq": queued, "job_id": job_id}
    finally:
        session.close()


@router.post("/{project_id}/clips/render_batch")
def render_batch(project_id: int, background_tasks: BackgroundTasks):
    session = db.SessionLocal()
    try:
        clips = (
            session.query(db.Clip)
            .filter_by(project_id=project_id, approved="approved")
            .all()
        )
        if not clips:
            raise HTTPException(status_code=400, detail="No approved clips")
        ids = []
        for c in clips:
            ids.append(c.clip_id)
            try:
                rq_queue.enqueue(_render_and_update, c.clip_id, project_id)
            except Exception:
                background_tasks.add_task(_render_and_update, c.clip_id, project_id)
        return {"queued": len(ids)}
    finally:
        session.close()


@router.get("/{project_id}/timeline")
def timeline_preview(project_id: int):
    session = db.SessionLocal()
    try:
        clips = (
            session.query(db.Clip)
            .filter_by(project_id=project_id)
            .order_by(db.Clip.score.desc())
            .all()
        )
        # return minimal timeline info
        out = []
        for c in clips:
            md = json.loads(c.metadata_json or "{}")
            out.append(
                {
                    "clip_id": c.clip_id,
                    "start": c.start,
                    "end": c.end,
                    "duration": c.duration,
                    "score": c.score,
                    "emotion": c.emotion,
                    "text": md.get("text"),
                }
            )
        return {"timeline": out}
    finally:
        session.close()


@router.post("/{project_id}/assemble")
def assemble_longform(
    project_id: int,
    target_minutes: int = 12,
    music_file: str = None,
    background_tasks: BackgroundTasks = None,
):
    session = db.SessionLocal()
    try:
        clips = (
            session.query(db.Clip)
            .filter_by(project_id=project_id, approved="approved")
            .all()
        )
        if not clips:
            raise HTTPException(status_code=400, detail="No approved clips to assemble")
        # prepare segment dicts for arrangement
        segs = []
        for c in clips:
            md = json.loads(c.metadata_json or "{}")
            segs.append(
                {
                    "clip_id": c.clip_id,
                    "source_path": md.get("source_path"),
                    "start": c.start,
                    "end": c.end,
                    "duration": c.duration,
                    "score": c.score,
                    "emotion": c.emotion,
                    "title": md.get("text", ""),
                }
            )

        timeline = arrange_for_longform(segs, target_minutes=target_minutes)

        out_dir = os.path.join(os.path.dirname(__file__), "outputs")
        out_path = os.path.join(out_dir, f"longform_project_{project_id}.mp4")
        os.makedirs(out_dir, exist_ok=True)

        if background_tasks:
            background_tasks.add_task(
                assemble_from_segments,
                timeline,
                music_file,
                out_path,
            )
            return {
                "status": "assembling_in_background",
                "out": out_path,
            }
        else:
            assemble_from_segments(timeline, music_file, out_path)
            return {"status": "done", "out": out_path}
    finally:
        session.close()


@router.post("/{project_id}/clips/{clip_id}/generate_titles")
def generate_titles(project_id: int, clip_id: str, count: int = 5):
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            raise HTTPException(status_code=404)
        md = json.loads(c.metadata_json or "{}")
        text = md.get("text", "")
        titles = generate_titles_from_text(text, n=count)
        c.title_suggestions = json.dumps(titles)
        session.commit()
        return {"titles": titles}
    finally:
        session.close()


@router.post("/{project_id}/clips/{clip_id}/generate_thumbnail")
def generate_thumb(project_id: int, clip_id: str):
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            raise HTTPException(status_code=404)
        md = json.loads(c.metadata_json or "{}")
        src = md.get("source_path")
        if not src or not os.path.exists(src):
            raise HTTPException(
                status_code=400, detail="source_path missing or not found in metadata"
            )
        # choose frame: middle of clip
        t = (c.start + c.end) / 2.0
        out_dir = os.path.join(os.path.dirname(__file__), "outputs", "thumbnails")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, f"{clip_id}.jpg")
        overlay = (json.loads(c.metadata_json or "{}")).get("text", "")
        generate_thumbnail(src, t, overlay, out)
        c.thumbnail_path = out
        session.commit()
        return {"thumbnail": out}
    finally:
        session.close()


@router.post("/{project_id}/clips/{clip_id}/generate_script")
def generate_script(project_id: int, clip_id: str, tone: str = "energetic"):
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            raise HTTPException(status_code=404)
        md = json.loads(c.metadata_json or "{}")
        text = md.get("text", "")
        script = generate_script_from_text(
            text, tone=tone, target_seconds=int(c.duration)
        )
        c.script = script
        session.commit()
        return {"script": script}
    finally:
        session.close()


@router.post("/{project_id}/clips/{clip_id}/generate_tts")
def generate_tts(project_id: int, clip_id: str):
    session = db.SessionLocal()
    try:
        c = (
            session.query(db.Clip)
            .filter_by(clip_id=clip_id, project_id=project_id)
            .first()
        )
        if not c:
            raise HTTPException(status_code=404)
        if not c.script:
            raise HTTPException(
                status_code=400, detail="No script available. Generate script first."
            )
        out_dir = os.path.join(os.path.dirname(__file__), "outputs", "tts")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, f"{clip_id}.mp3")
        res = generate_tts_from_script(c.script, out)
        if not res:
            raise HTTPException(
                status_code=500, detail="TTS generation failed (gTTS missing or error)"
            )
        c.tts_path = out
        session.commit()
        return {"tts": out}
    finally:
        session.close()
