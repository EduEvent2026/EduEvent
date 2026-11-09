from app.db.models import Base
from app.db.session import get_engine


if __name__ == "__main__":
    Base.metadata.create_all(bind=get_engine())
    print("Tabele M2 są gotowe: categories, events")
