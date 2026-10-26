import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Fail fast: a missing DATABASE_URL crashes at startup with a clear error,
# instead of failing mysteriously on the first request.
DATABASE_URL = os.environ["DATABASE_URL"]

# pool_pre_ping tests each pooled connection before use, so a database
# restart doesn't cause errors on the next request.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """One database session per request, always closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
