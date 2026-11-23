from pydantic import BaseModel, Field


class EdycjaProfiluRequest(BaseModel):
    #Wszystkie są opcjonalne

    email: str | None = Field(
        default=None,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    imie: str | None = Field(default=None, min_length=1, max_length=100)
    nazwisko: str | None = Field(default=None, min_length=1, max_length=100)
