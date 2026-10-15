from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend import __version__
from backend.api import api_router
from backend.config import settings
from backend.startup import initialize_application

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_application(); yield

app=FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)
app.include_router(api_router, prefix="/api")
assets=settings.frontend_path / "assets"
if assets.is_dir(): app.mount("/assets", StaticFiles(directory=assets), name="assets")

@app.get("/healthz", tags=["Health"])
def healthz(): return {"status":"ok","name":settings.app_name,"version":__version__}

@app.get("/", include_in_schema=False)
def index():
    target=settings.frontend_path / "index.html"
    return FileResponse(target) if target.is_file() else {"name":settings.app_name,"docs":"/docs"}
