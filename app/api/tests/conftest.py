import os

# Doit être fait AVANT d'importer l'application : base SQLite en mémoire, sans Redis.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["REDIS_HOST"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402
from app.database import Base, engine  # noqa: E402


class FakeCache:
    """Cache en mémoire pour tester le comportement HIT / MISS sans Redis."""

    def __init__(self):
        self.store = {}

    def get_json(self, key):
        return self.store.get(key)

    def set_json(self, key, value, ttl=0):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def fake_cache(monkeypatch):
    fake = FakeCache()
    monkeypatch.setattr(main, "cache", fake)
    return fake
