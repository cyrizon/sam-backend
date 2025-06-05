import sys
from pathlib import Path

# Ajoute le dossier parent (la racine du projet) au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Compléter ton conftest.py existant avec ces fixtures

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_ors_service():
    """Mock du service ORS pour les tests."""
    mock = MagicMock()
    
    # Réponse standard pour get_base_route
    mock.get_base_route.return_value = {
        "features": [{
            "geometry": {"coordinates": [[7.0, 48.0], [8.0, 49.0]]},
            "properties": {"summary": {"duration": 3600, "distance": 100000}}
        }]
    }
    
    # Réponse standard pour get_route_avoid_tollways
    mock.get_route_avoid_tollways.return_value = {
        "features": [{
            "geometry": {"coordinates": [[7.0, 48.0], [8.0, 49.0]]},
            "properties": {"summary": {"duration": 4200, "distance": 120000}}
        }]
    }
    
    return mock

@pytest.fixture
def sample_coordinates():
    """Coordonnées d'exemple pour les tests."""
    return [[7.0, 48.0], [8.0, 49.0]]

@pytest.fixture
def sample_tolls():
    """Péages d'exemple pour les tests."""
    return [
        {"id": "toll_1", "cost": 2.50, "longitude": 7.5, "latitude": 48.5},
        {"id": "toll_2", "cost": 3.20, "longitude": 7.8, "latitude": 48.8},
        {"id": "toll_open_1_o", "cost": 4.10, "longitude": 7.2, "latitude": 48.2}
    ]