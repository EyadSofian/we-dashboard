import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .db import init_db
from .scheduler import start_scheduler, stop_scheduler
from .routers import auth as auth_router
from .routers import accounts as accounts_router
from .routers import quota as quota_router
from .routers import alerts as alerts_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(accounts_router.router)
app.include_router(quota_router.router)
app.include_router(alerts_router.router)


@app.get("/api/health")
async def health():
    return {"ok": True, "app": settings.APP_NAME}


# Serve built frontend (SPA) from /
if settings.SERVE_FRONTEND and os.path.isdir(settings.FRONTEND_DIST):
    assets_dir = os.path.join(settings.FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        # Let API routes 404 naturally; this handler is only matched for non-/api paths
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        index = os.path.join(settings.FRONTEND_DIST, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return {"detail": "Frontend not built"}
