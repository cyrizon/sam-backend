import os
import pytest
from unittest.mock import patch, MagicMock
from src.services.ors_service import ORSService

def test_test_all_set_env(monkeypatch):
    monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
    ors = ORSService()
    assert ors.test_all_set() is True

def test_test_all_set_env_missing(monkeypatch):
    monkeypatch.delenv("ORS_BASE_URL", raising=False)
    ors = ORSService()
    assert ors.test_all_set() is False

@patch("src.services.ors_service.requests.get")
def test_get_route_success(mock_get, monkeypatch):
    monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
    mock_response = MagicMock()
    mock_response.json.return_value = {"routes": ["fake_route"]}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    ors = ORSService()
    result = ors.get_route([8.681495, 49.41461], [8.687872, 49.420318])
    assert result == {"routes": ["fake_route"]}
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "http://localhost:8082/ors/v2/directions/driving-car" in args

@patch("src.services.ors_service.requests.get")
def test_get_route_error(mock_get, monkeypatch):
    monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
    mock_get.side_effect = Exception("Connection error")
    ors = ORSService()
    result = ors.get_route([8.681495, 49.41461], [8.687872, 49.420318])
    assert "error" in result
    assert "Connection error" in result["error"]

@patch("src.services.ors_service.requests.post")
def test_call_ors_success(mock_post, monkeypatch):
    """Test appel ORS personnalisé réussi."""
    monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"routes": ["fake_route"]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    ors = ORSService()
    payload = {
        "coordinates": [[7.0, 48.0], [8.0, 49.0]],
        "extra_info": ["tollways"]
    }
    
    result = ors.call_ors(payload)
    
    assert result == {"routes": ["fake_route"]}
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"] == payload
    assert kwargs["timeout"] >= 10  # Timeout par défaut

@patch("src.services.ors_service.requests.post")
def test_get_base_route_success(mock_post, monkeypatch):
    """Test récupération route de base."""
    monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": [{"properties": {"summary": {}}}]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    ors = ORSService()
    coordinates = [[7.0, 48.0], [8.0, 49.0]]
    
    result = ors.get_base_route(coordinates)
    
    assert "features" in result
    # Vérifier que le payload contient tollways par défaut
    call_args = mock_post.call_args
    payload = call_args[1]["json"]
    assert "tollways" in payload["extra_info"]

@patch("src.services.ors_service.requests.post")
def test_get_route_avoid_tollways_success(mock_post, monkeypatch):
    """Test récupération route évitant les péages."""
    monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": [{"properties": {"summary": {}}}]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    ors = ORSService()
    coordinates = [[7.0, 48.0], [8.0, 49.0]]
    
    result = ors.get_route_avoid_tollways(coordinates)
    
    assert "features" in result
    # Vérifier que le payload contient avoid_features
    call_args = mock_post.call_args
    payload = call_args[1]["json"]
    assert "avoid_features" in payload["options"]
    assert "tollways" in payload["options"]["avoid_features"]