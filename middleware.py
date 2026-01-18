from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import db
import datetime


class QuotaMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, free_limit_per_day=10):
        super().__init__(app)
        self.free_limit_per_day = free_limit_per_day

    async def dispatch(self, request: Request, call_next):
        # simple quota: if X-User-Id header maps to free tier and they have created too many clips today, block
        user_id = request.headers.get("X-User-Id")
        if user_id:
            session = db.SessionLocal()
            try:
                user = session.query(db.User).filter_by(id=int(user_id)).first()
                if user and user.tier == "free":
                    # count events of type clip_created today
                    today = datetime.datetime.utcnow().date()
                    from sqlalchemy import func

                    start = datetime.datetime(today.year, today.month, today.day)
                    cnt = (
                        session.query(func.count(db.Event.id))
                        .filter(
                            db.Event.user_id == user.id,
                            db.Event.event_type == "clip_created",
                            db.Event.created_at >= start,
                        )
                        .scalar()
                        or 0
                    )
                    if cnt >= self.free_limit_per_day:
                        raise HTTPException(
                            status_code=429,
                            detail="Free tier daily clip creation limit reached",
                        )
            finally:
                session.close()
        return await call_next(request)
