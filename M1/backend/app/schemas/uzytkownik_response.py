from pydantic import BaseModel, Field


class UzytkownikResponse(BaseModel):
    id: str
    login: str
    email: str | None = None
    imie: str | None = None
    nazwisko: str | None = None
    role: list[str] = Field(default_factory=list)
