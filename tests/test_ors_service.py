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