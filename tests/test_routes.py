import pytest
import json
from flask import Flask
from src.routes import register_routes

@pytest.fixture
def app():
    app = Flask(__name__)
    register_routes(app)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_index(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.json == {"message": "Welcome to the Flask API!"}

def test_moke_route(client):
    resp = client.get('/api/mokeroute')
    assert resp.status_code in (200, 404)

def test_retrieve_tolls_no_data(client):
    resp = client.post('/api/tolls', json=None)
    assert resp.status_code == 400

def test_retrieve_tolls_options(client):
    resp = client.options('/api/tolls')
    assert resp.status_code == 200

def test_api_route_post_missing_params(client):
    resp = client.post('/api/route/')
    assert resp.status_code == 410

def test_api_route_post_missing_coordinates(client):
    resp = client.post('/api/route/', json={'coordinates': []})
    assert resp.status_code == 411

def test_geocode_search_missing_params(client):
    resp = client.get('/api/geocode/search')
    assert resp.status_code == 400

def test_geocode_autocomplete_missing_params(client):
    resp = client.get('/api/geocode/autocomplete')
    assert resp.status_code == 400