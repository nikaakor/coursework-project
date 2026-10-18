from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
import database
import models 
from exceptions import DomainError
from routers import catalog, pharmacies, users, orders, admin
from seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(title="PharmPlus API", version="3.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse(config.STATIC_DIR / "index.html")


@app.get("/admin-panel", include_in_schema=False)
def read_admin_panel():
    return FileResponse(config.STATIC_DIR / "admin.html")


for r in (catalog.router, pharmacies.router, users.router, orders.router, admin.router):
    app.include_router(r)
