import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.database import engine


@pytest.fixture(autouse=True)
def reset_db():
    """
    Runs before every test to ensure a clean database state.
    This prevents tests from interfering with each other (409 conflicts).
    """
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE bookings, clientes RESTART IDENTITY CASCADE"))
        conn.commit()


@pytest.fixture()
def client():
    return TestClient(app)