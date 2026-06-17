from fastapi import FastAPI

from app.api.concepts import router as concepts_router
from app.api.wechat import router as wechat_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="微光年轮 MVP：概念管理、年轮记录、时间轴、对比、日历与微信生态接口。",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


app.include_router(concepts_router)
app.include_router(wechat_router)
