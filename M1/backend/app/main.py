from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin_api, user_api
from app.config import settings
from app.exceptions import KeycloakBlad, Konflikt, NieprawidlowaRola, NieZnaleziono

app = FastAPI(
    title="EduEvent - moduł Użytkownicy i autoryzacja",
    swagger_ui_init_oauth={
        "clientId": settings.keycloak_client_id,
        "usePkceWithAuthorizationCodeGrant": True,
        "additionalQueryStringParams": {"prompt": "login"},
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_api.router)
app.include_router(admin_api.router)


@app.get("/health", tags=["Systemowe"])
def health():
    """Endpoint publiczny."""
    return {"status": "ok"}


def _blad(status_code: int, komunikat: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": komunikat})


@app.exception_handler(NieZnaleziono)
async def _nie_znaleziono(_: Request, __: NieZnaleziono):
    return _blad(404, "Nie znaleziono użytkownika lub roli")


@app.exception_handler(NieprawidlowaRola)
async def _nieprawidlowa_rola(_: Request, e: NieprawidlowaRola):
    return _blad(400, str(e))


@app.exception_handler(Konflikt)
async def _konflikt(_: Request, e: Konflikt):
    return _blad(409, str(e))


@app.exception_handler(KeycloakBlad)
async def _keycloak_blad(_: Request, e: KeycloakBlad):
    return _blad(502, str(e))
