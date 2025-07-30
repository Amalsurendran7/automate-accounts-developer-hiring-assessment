from sqlmodel import create_engine, Session
from sqlalchemy.orm import sessionmaker


from core.config import settings

engine = create_engine(url=settings.SQL_CONNECTION, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    with Session(engine) as session:
        yield session



