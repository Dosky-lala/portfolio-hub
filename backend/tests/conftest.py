import os

import pytest

# SAFETY GUARD: these tests DROP ALL TABLES between tests.
# Refuse to run unless DATABASE_URL clearly points at a test database.
_url = os.environ.get("DATABASE_URL", "")
if "test" not in _url:
    raise RuntimeError(
        "Refusing to run: DATABASE_URL must point at a TEST database "
        f"(got: {_url.split('@')[-1] if _url else 'nothing'})"
    )

from fastapi.testclient import TestClient  # noqa: E402  (imports after the guard on purpose)

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """A fresh, empty database for every single test."""
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # "with" runs the app's startup, which creates the tables
        yield c
    Base.metadata.drop_all(bind=engine)
