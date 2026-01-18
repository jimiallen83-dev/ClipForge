from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
import json
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import urljoin
import os
import db as _db
import youtube_oauth as _oauth

router = APIRouter(prefix="/youtube")


@router.get("/authorize")
def authorize(request: Request):
    """Start OAuth flow: redirect user to Google consent screen."""
    # allow forcing the OAuth host via environment, otherwise normalize 127.0.0.1 -> localhost
    forced = os.environ.get("OAUTH_REDIRECT_HOST")
    if forced:
        host_name = forced
    else:
        host_name = request.url.hostname
        if host_name == "127.0.0.1":
            host_name = "localhost"
    port = request.url.port
    host = (
        f"{request.url.scheme}://{host_name}:{port}"
        if port
        else f"{request.url.scheme}://{host_name}"
    )
    redirect_uri = urljoin(host, "/youtube/oauth2callback")
    try:
        auth_url, state = _oauth.build_authorize_url(redirect_uri)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(auth_url)


@router.get("/oauth2callback")
async def oauth2callback(request: Request):
    """Exchange authorization code for credentials and save channel credentials."""
    forced = os.environ.get("OAUTH_REDIRECT_HOST")
    if forced:
        host_name = forced
    else:
        host_name = request.url.hostname
        if host_name == "127.0.0.1":
            host_name = "localhost"
    port = request.url.port
    host = (
        f"{request.url.scheme}://{host_name}:{port}"
        if port
        else f"{request.url.scheme}://{host_name}"
    )
    redirect_uri = urljoin(host, "/youtube/oauth2callback")
    # Build full URL that Google redirected to
    full_url = str(request.url)
    try:
        creds = _oauth.exchange_code_for_credentials(
            redirect_uri, {"full_url": full_url}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {e}")

    # Fetch channel videos (and channel info)
    try:
        detailed, channel_info = _oauth.fetch_channel_videos(creds)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch channel videos: {e}"
        )

    # Save credentials and channel
    session = _db.SessionLocal()
    try:
        _db.save_credentials(
            session,
            channel_info["channel_id"],
            channel_info.get("title"),
            creds.to_json(),
        )
        # Upsert videos
        for v in detailed:
            _db.upsert_video(session, v)

    finally:
        session.close()
    return JSONResponse(
        {"message": "Channel authorized and videos fetched", "channel": channel_info}
    )


def _process_job(job_id: int):
    session = _db.SessionLocal()
    try:
        job = session.query(_db.Job).filter_by(id=job_id).first()
        if not job:
            return
        job.status = "processing"
        job.started_at = __import__("datetime").datetime.utcnow()
        session.commit()

        # Placeholder processing logic: here you'd download video, transcribe, etc.
        import time

        time.sleep(1)

        job.status = "completed"
        job.finished_at = __import__("datetime").datetime.utcnow()
        session.commit()
    finally:
        session.close()


@router.post("/scan")
def scan_channel(background_tasks: BackgroundTasks):
    """Scan stored channels, fetch videos, store them, and enqueue a job per video."""
    session = _db.SessionLocal()
    try:
        channels = session.query(_db.Channel).all()
        if not channels:
            raise HTTPException(
                status_code=400,
                detail="No channels authorized. Visit /youtube/authorize first.",
            )

        jobs = []
        for ch in channels:
            creds = (
                _oauth.Credentials.from_authorized_user_info
                if hasattr(_oauth, "Credentials")
                else None
            )
            # we stored raw JSON; recreate credentials
            try:
                from google.oauth2.credentials import Credentials as _Creds

                creds = _Creds.from_authorized_user_info(json.loads(ch.credentials))
            except Exception:
                # try loading as JSON string of token fields
                try:
                    import json as _json

                    creds = _Creds.from_authorized_user_info(
                        _json.loads(ch.credentials)
                    )
                except Exception:
                    raise HTTPException(
                        status_code=500, detail="Invalid stored credentials"
                    )

            detailed, channel_info = _oauth.fetch_channel_videos(creds)
            for v in detailed:
                _db.upsert_video(session, v)
                job = _db.create_job(session, v["video_id"])
                jobs.append(job.id)
                background_tasks.add_task(_process_job, job.id)

        return {"message": "Scan started", "jobs_created": len(jobs)}
    finally:
        session.close()
