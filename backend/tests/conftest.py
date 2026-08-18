import os
import pytest

os.environ['SECRET_KEY'] = 'test-only-secret-that-is-not-a-production-secret'
os.environ['DATABASE_URL'] = 'sqlite:///./test_nyaya_setu.db'

from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def token(client):
    client.post('/api/v1/auth/register', json={'email': 'citizen@example.com', 'password': 'secure-pass-123'})
    return client.post('/api/v1/auth/login', json={'email': 'citizen@example.com', 'password': 'secure-pass-123'}).json()['access_token']


@pytest.fixture
def headers(token):
    return {'Authorization': f'Bearer {token}'}
