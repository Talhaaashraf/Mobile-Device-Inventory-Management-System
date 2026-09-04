from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, devices, management, users
from app.core.config import settings
from app.db.base import Base
from app.db.migrate_sqlite import ensure_sqlite_device_columns
from app.db.seed import seed_database
from app.db.session import SessionLocal, engine
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        ensure_sqlite_device_columns()
    if settings.SEED_ON_STARTUP:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    yield


app = FastAPI(title="Folio3 Mobile Device IMS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(management.router, prefix="/api")



@app.get("/health")
def health():
    return {"status": "ok"}
