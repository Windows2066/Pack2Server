from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_search import router as search_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_uploads import router as uploads_router
from app.core.logging import configure_logging
from app.core.paths import ensure_data_dirs
from app.db.session import init_db


def create_app() -> FastAPI:
    configure_logging()
    ensure_data_dirs()
    init_db()
    app = FastAPI(title="Minecraft 服务端整合包制作应用 API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(tasks_router)
    app.include_router(uploads_router)
    app.include_router(search_router)
    return app


app = create_app()
