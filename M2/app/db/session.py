import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@lru_cache(maxsize=1)
def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Ustaw DATABASE_URL zgodnie z M2/.env.example")
    return create_engine(url, pool_pre_ping=True)


def get_db():
    with Session(get_engine()) as session:
        yield session
