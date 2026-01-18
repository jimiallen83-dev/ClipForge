from fastapi import FastAPI
from sqlalchemy import text
import logging
import db
from fastapi.staticfiles import StaticFiles
from middleware import QuotaMiddleware

app = FastAPI(title="ClipForge API")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(QuotaMiddleware, free_limit_per_day=10)


def _try_include(module_name, attr_name="router"):
    try:
        mod = __import__(module_name, fromlist=[attr_name])
        router = getattr(mod, attr_name)
        app.include_router(router)
    except Exception:
        logging.exception(
            f"Failed to include router from {module_name}; continuing without it."
        )


# include routers safely so missing optional deps don't stop the app
_try_include("youtube")
_try_include("projects")
_try_include("auth")
_try_include("payments")
_try_include("jobs")


@app.get("/health")
def health():
    # quick DB connectivity check
    try:
        session = db.SessionLocal()
        session.execute(text("SELECT 1"))
        session.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/")
def index():
    return {"service": "ClipForge", "status": "running"}


@app.on_event("startup")
def startup():
    db.init_db()
