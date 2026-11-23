from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.exceptions import CatalogAPIException
from app.api.router import router

app = FastAPI(title="EduEvent - Catalog Service", version="0.1.0")
app.include_router(router)


@app.exception_handler(CatalogAPIException)
async def catalog_exception_handler(request: Request, exc: CatalogAPIException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
