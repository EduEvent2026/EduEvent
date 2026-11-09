from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="EduEvent – Moduł 2", version="0.1.0")
app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok", "module": "M2"}
