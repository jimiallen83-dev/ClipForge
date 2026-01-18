import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import json

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///clipforge.db")

# If using SQLite, enable check_same_thread; otherwise leave default for Postgres
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String, unique=True, index=True)
    title = Column(String)
    credentials = Column(Text)  # JSON


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    duration = Column(Float)
    privacy = Column(String)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, index=True, nullable=True)


class Clip(Base):
    __tablename__ = "clips"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    clip_id = Column(String, unique=True, index=True)
    start = Column(Float)
    end = Column(Float)
    duration = Column(Float)
    score = Column(Float, default=0.0)
    emotion = Column(String)
    # older migrations created the column named 'metadata'; keep attribute name
    # `metadata_json` for clarity but map it to the existing DB column 'metadata'
    metadata_json = Column("metadata", Text)
    approved = Column(String, default="pending")  # pending/approved/rejected
    renderer_status = Column(String, default="not_rendered")
    output_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    title_suggestions = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    tts_path = Column(String, nullable=True)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, index=True)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    tier = Column(String, default="free")
    api_key = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tier = Column(String)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    active = Column(String, default="true")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    clip_id = Column(String, index=True, nullable=True)
    event_type = Column(String, index=True)
    value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def save_credentials(session, channel_id, title, credentials_dict):
    creds_json = json.dumps(credentials_dict)
    ch = session.query(Channel).filter_by(channel_id=channel_id).first()
    if not ch:
        ch = Channel(channel_id=channel_id, title=title, credentials=creds_json)
        session.add(ch)
    else:
        ch.credentials = creds_json
        ch.title = title
    session.commit()
    return ch


def upsert_video(session, video):
    v = session.query(Video).filter_by(video_id=video["video_id"]).first()
    if not v:
        v = Video(
            video_id=video["video_id"],
            title=video.get("title"),
            description=video.get("description"),
            duration=video.get("duration", 0),
            privacy=video.get("privacy", "unknown"),
        )
        session.add(v)
    else:
        v.title = video.get("title")
        v.description = video.get("description")
        v.duration = video.get("duration", 0)
        v.privacy = video.get("privacy", "unknown")
    session.commit()
    return v


def create_job(session, video_id):
    job = Job(video_id=video_id, status="queued")
    session.add(job)
    session.commit()
    return job


def create_project(session, name, description=None):
    p = session.query(Project).filter_by(name=name).first()
    if not p:
        p = Project(name=name, description=description)
        session.add(p)
        session.commit()
    return p


def create_user(session, email, name=None, tier="free", api_key=None):
    u = session.query(User).filter_by(email=email).first()
    if not u:
        u = User(email=email, name=name, tier=tier, api_key=api_key)
        session.add(u)
        session.commit()
    return u


def record_event(session, user_id=None, clip_id=None, event_type="generic", value=None):
    e = Event(
        user_id=user_id,
        clip_id=clip_id,
        event_type=event_type,
        value=value,
    )
    session.add(e)
    session.commit()
    return e


def get_user_analytics(session, user_id):
    # simple aggregation: counts and sum of watch_time
    from sqlalchemy import func

    total_clips = (
        session.query(func.count(Event.id))
        .filter(Event.user_id == user_id, Event.event_type == "clip_created")
        .scalar()
    )
    watch_time = (
        session.query(func.sum(Event.value))
        .filter(Event.user_id == user_id, Event.event_type == "watch_time")
        .scalar()
        or 0
    )
    return {
        "clips_created": int(total_clips or 0),
        "watch_time_seconds": float(watch_time),
    }


def create_clip(
    session, project_id, clip_id, start, end, score, emotion, metadata=None
):
    duration = end - start
    c = session.query(Clip).filter_by(clip_id=clip_id).first()
    if not c:
        c = Clip(
            project_id=project_id,
            clip_id=clip_id,
            start=start,
            end=end,
            duration=duration,
            score=score,
            emotion=emotion,
            metadata_json=json.dumps(metadata or {}),
            approved="pending",
            renderer_status="not_rendered",
        )
        session.add(c)
    else:
        c.start = start
        c.end = end
        c.duration = duration
        c.score = score
        c.emotion = emotion
        c.metadata_json = json.dumps(metadata or {})
    session.commit()
    return c


def get_clips_for_project(session, project_id, limit=100):
    return (
        session.query(Clip)
        .filter_by(project_id=project_id)
        .order_by(Clip.score.desc())
        .limit(limit)
        .all()
    )
