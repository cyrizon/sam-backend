# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\tests\test_routes.py
import pytest
from src import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {"message": "Welcome to the Flask API!"}