# 🧪 Tests - Suite de Tests SAM Backend

## 📋 Vue d'ensemble

La suite de tests SAM couvre quasiment l'intégralité du backend avec des tests unitaires, d'intégration et de performance. Elle utilise pytest comme framework principal avec des fixtures avancées et des mocks pour isoler les composants.

## 🏗️ Architecture

```
tests/
├── conftest.py                 # Configuration globale pytest et fixtures
├── test_routes.py             # Tests des endpoints API
├── test_ors_service.py        # Tests du service OpenRouteService
├── test_ors_config_manager.py # Tests du gestionnaire de configuration ORS
├── test_api_optimization.py   # Tests d'optimisation d'itinéraires
└── __pycache__/              # Cache pytest
```

## 🎯 Objectifs des tests

### **Couverture complète**
- 🔌 **Tests d'API** : Validation des endpoints et réponses
- 🧠 **Tests unitaires** : Composants isolés et logique métier
- 🔗 **Tests d'intégration** : Interaction entre services
- 📊 **Tests de performance** : Métriques et benchmarks

### **Qualité et fiabilité**
- ✅ **Validation** : Contrôles de données et formats
- 🛡️ **Gestion d'erreurs** : Tests des cas d'échec
- 🔄 **Reproductibilité** : Tests déterministes et isolés
- 📈 **Régression** : Détection des régressions

## 🧩 Configuration et fixtures

### **1. conftest.py** - Configuration Globale

Fichier central de configuration pytest avec fixtures partagées.

#### **Configuration actuelle**
```python
import sys
from pathlib import Path

# Ajout du projet au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
```

#### **Configuration étendue recommandée**
```python
import pytest
import tempfile
import os
import shutil
from unittest.mock import MagicMock, patch
from flask import Flask

# Configuration de base
@pytest.fixture(scope="session")
def test_config():
    """Configuration de test globale."""
    return {
        "TESTING": True,
        "DEBUG": False,
        "SECRET_KEY": "test-secret-key",
        "ORS_BASE_URL": "http://mock-ors:8082/ors",
        "CACHE_DIR": None,  # Sera défini par temp_dir
        "DATA_DIR": None,   # Sera défini par temp_dir
        "RATE_LIMIT_ENABLED": False,
        "ENABLE_CACHE": True
    }

@pytest.fixture(scope="session")
def temp_dir():
    """Répertoire temporaire pour les tests."""
    temp_dir = tempfile.mkdtemp(prefix="sam_test_")
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def app(test_config, temp_dir):
    """Application Flask configurée pour les tests."""
    from src import create_app
    
    # Configuration du répertoire temporaire
    test_config["CACHE_DIR"] = os.path.join(temp_dir, "cache")
    test_config["DATA_DIR"] = os.path.join(temp_dir, "data")
    
    # Création des répertoires
    os.makedirs(test_config["CACHE_DIR"], exist_ok=True)
    os.makedirs(test_config["DATA_DIR"], exist_ok=True)
    
    # Création de l'app avec configuration de test
    app = create_app()
    app.config.update(test_config)
    
    # Context de test
    with app.app_context():
        yield app

@pytest.fixture(scope="function")
def client(app):
    """Client de test Flask."""
    return app.test_client()

@pytest.fixture(scope="function")
def runner(app):
    """Runner CLI pour les tests de commandes."""
    return app.test_cli_runner()

# Fixtures de données
@pytest.fixture
def sample_geojson_route():
    """Route GeoJSON d'exemple."""
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [7.448595, 48.262004],  # Sélestat
                    [4.856525, 47.049839],  # Auxerre
                    [3.114432, 45.784832]   # Clermont-Ferrand
                ]
            },
            "properties": {
                "summary": {
                    "distance": 456789.5,
                    "duration": 16420.3
                }
            }
        }]
    }

@pytest.fixture
def sample_toll_booths():
    """Stations de péages d'exemple."""
    return [
        {
            "osm_id": "way/123456789",
            "name": "Péage de Test 1",
            "operator": "ASF",
            "coordinates": [4.8567, 46.7892],
            "toll_type": "O",  # Ouvert
            "properties": {"highway": "toll_booth"}
        },
        {
            "osm_id": "way/987654321", 
            "name": "Péage de Test 2",
            "operator": "APRR",
            "coordinates": [4.8234, 46.2891],
            "toll_type": "F",  # Fermé
            "properties": {"highway": "toll_booth"}
        }
    ]

@pytest.fixture
def sample_optimization_request():
    """Requête d'optimisation d'exemple."""
    return {
        "coordinates": [
            [7.448595, 48.262004],  # Sélestat
            [3.114432, 45.784832]   # Clermont-Ferrand
        ],
        "max_tolls": 2,
        "vehicle_category": "c1"
    }

# Mocks avancés
@pytest.fixture
def mock_cache_manager():
    """Mock du gestionnaire de cache."""
    mock = MagicMock()
    
    # Configuration du mock
    mock.toll_booths = []
    mock.complete_motorway_links = []
    mock.get_available_operators.return_value = ["ASF", "APRR", "SANEF"]
    mock.load_all_including_motorway_linking.return_value = True
    
    return mock

@pytest.fixture
def mock_ors_service_complete():
    """Mock complet du service ORS."""
    mock = MagicMock()
    
    # Réponses standards
    mock.get_base_route.return_value = {
        "features": [{
            "geometry": {
                "type": "LineString",
                "coordinates": [[7.0, 48.0], [8.0, 49.0]]
            },
            "properties": {
                "summary": {
                    "duration": 3600,
                    "distance": 100000
                }
            }
        }]
    }
    
    mock.get_route_avoid_tollways.return_value = {
        "features": [{
            "geometry": {
                "type": "LineString", 
                "coordinates": [[7.0, 48.0], [8.0, 49.0]]
            },
            "properties": {
                "summary": {
                    "duration": 4200,
                    "distance": 120000
                }
            }
        }]
    }
    
    mock.test_all_set.return_value = True
    
    return mock

# Décorateurs de test
@pytest.fixture
def skip_slow_tests():
    """Skip les tests lents sauf si explicitement demandés."""
    import os
    if not os.getenv("RUN_SLOW_TESTS"):
        pytest.skip("Tests lents désactivés (définir RUN_SLOW_TESTS=1)")

@pytest.fixture
def skip_integration_tests():
    """Skip les tests d'intégration sauf si explicitement demandés."""
    import os
    if not os.getenv("RUN_INTEGRATION_TESTS"):
        pytest.skip("Tests d'intégration désactivés (définir RUN_INTEGRATION_TESTS=1)")
```

---

### **2. pytest.ini** - Configuration Pytest

Configuration globale de pytest pour le projet.

#### **Configuration actuelle**
```ini
[pytest]
addopts = -v
testpaths = tests
python_files = test_*.py
```

#### **Configuration étendue recommandée**
```ini
[pytest]
# Options de base
addopts = -v --tb=short --strict-markers --strict-config
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers personnalisés
markers =
    slow: tests lents (nécessitent RUN_SLOW_TESTS=1)
    integration: tests d'intégration (nécessitent RUN_INTEGRATION_TESTS=1)
    unit: tests unitaires rapides
    api: tests d'API
    cache: tests du système de cache
    optimization: tests d'optimisation d'itinéraires
    ors: tests du service OpenRouteService
    performance: tests de performance et benchmarks

# Filtres par défaut
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore:.*urllib3.*:UserWarning

# Configuration de coverage (si installé)
addopts = --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Parallélisation (si pytest-xdist installé)
addopts = -n auto

# Ordre d'exécution (si pytest-order installé)
addopts = --order-scope=module
```

## 🧩 Tests détaillés

### **1. test_routes.py** - Tests des Endpoints API

Tests complets des routes et endpoints de l'API SAM.

#### **Tests actuels**
```python
def test_index(client):
    """Test de l'endpoint racine."""
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.json == {"message": "Welcome to the Flask API!"}

def test_retrieve_tolls_no_data(client):
    """Test sans données."""
    resp = client.post('/api/tolls', json=None)
    assert resp.status_code == 400

def test_retrieve_tolls_options(client):
    """Test des options CORS."""
    resp = client.options('/api/tolls')
    assert resp.status_code == 200
```

#### **Tests étendus recommandés**
```python
import pytest
import json
from unittest.mock import patch

class TestApiRoutes:
    """Tests des routes API principales."""
    
    def test_index_endpoint(self, client):
        """Test de l'endpoint racine."""
        response = client.get('/')
        
        assert response.status_code == 200
        assert response.is_json
        
        data = response.get_json()
        assert "message" in data
        assert "Welcome" in data["message"]
    
    def test_health_check(self, client):
        """Test du health check (si implémenté)."""
        response = client.get('/health')
        
        if response.status_code == 200:
            data = response.get_json()
            assert "status" in data
            assert data["status"] == "healthy"
    
    @pytest.mark.api
    def test_tolls_endpoint_post_valid_data(self, client, sample_geojson_route):
        """Test POST /api/tolls avec données valides."""
        response = client.post('/api/tolls', 
                             json=sample_geojson_route,
                             content_type='application/json')
        
        assert response.status_code in [200, 201]
        
        if response.is_json:
            data = response.get_json()
            assert isinstance(data, (dict, list))
    
    def test_tolls_endpoint_invalid_json(self, client):
        """Test POST /api/tolls avec JSON invalide."""
        response = client.post('/api/tolls',
                             data="invalid json",
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_tolls_endpoint_missing_data(self, client):
        """Test POST /api/tolls sans données."""
        response = client.post('/api/tolls', json=None)
        assert response.status_code == 400
    
    def test_cors_preflight(self, client):
        """Test des requêtes CORS preflight."""
        response = client.options('/api/tolls')
        assert response.status_code == 200
        
        # Vérification des headers CORS
        headers = dict(response.headers)
        assert 'Access-Control-Allow-Origin' in headers

class TestOptimizationApi:
    """Tests de l'API d'optimisation."""
    
    @pytest.mark.optimization
    @patch('src.services.smart_route.SmartRouteService')
    def test_smart_route_optimization(self, mock_service, client, sample_optimization_request):
        """Test de l'optimisation intelligente."""
        # Configuration du mock
        mock_service.return_value.optimize_route.return_value = {
            "success": True,
            "found_solution": "optimization_success",
            "total_cost": 15.30,
            "tolls_count": 2
        }
        
        response = client.post('/api/smart-route/tolls',
                             json=sample_optimization_request)
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert "success" in data
        assert "found_solution" in data
        
        if data.get("success"):
            assert "total_cost" in data
            assert "tolls_count" in data

class TestErrorHandling:
    """Tests de gestion d'erreurs."""
    
    def test_404_error(self, client):
        """Test d'endpoint inexistant."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Test de méthode HTTP non autorisée."""
        response = client.delete('/api/tolls')
        assert response.status_code == 405
    
    def test_large_payload(self, client):
        """Test avec payload trop volumineux."""
        large_data = {"data": "x" * 10000}  # 10KB
        response = client.post('/api/tolls', json=large_data)
        
        # Devrait soit accepter soit rejeter proprement
        assert response.status_code in [200, 400, 413]

class TestSecurity:
    """Tests de sécurité de l'API."""
    
    def test_sql_injection_attempt(self, client):
        """Test de tentative d'injection SQL."""
        malicious_data = {
            "coordinates": "'; DROP TABLE users; --"
        }
        
        response = client.post('/api/tolls', json=malicious_data)
        # Devrait rejeter proprement sans erreur interne
        assert response.status_code != 500
    
    def test_xss_attempt(self, client):
        """Test de tentative XSS."""
        malicious_data = {
            "coordinates": "<script>alert('xss')</script>"
        }
        
        response = client.post('/api/tolls', json=malicious_data)
        assert response.status_code != 500
```

---

### **3. test_ors_service.py** - Tests du Service OpenRouteService

Tests du service d'interface avec OpenRouteService.

#### **Tests étendus**
```python
import pytest
from unittest.mock import patch, MagicMock
import requests

class TestORSService:
    """Tests du service OpenRouteService."""
    
    def test_initialization_with_env(self, monkeypatch):
        """Test d'initialisation avec variables d'environnement."""
        monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
        
        from src.services.ors_service import ORSService
        ors = ORSService()
        
        assert ors.test_all_set() is True
        assert "localhost" in ors.base_url
    
    def test_initialization_without_env(self, monkeypatch):
        """Test d'initialisation sans variables d'environnement."""
        monkeypatch.delenv("ORS_BASE_URL", raising=False)
        
        from src.services.ors_service import ORSService
        ors = ORSService()
        
        assert ors.test_all_set() is False
    
    @patch("src.services.ors_service.requests.get")
    def test_get_route_success(self, mock_get, monkeypatch):
        """Test de récupération de route réussie."""
        monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
        
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "features": [{
                "geometry": {
                    "coordinates": [[7.0, 48.0], [8.0, 49.0]]
                },
                "properties": {
                    "summary": {
                        "distance": 100000,
                        "duration": 3600
                    }
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        from src.services.ors_service import ORSService
        ors = ORSService()
        
        result = ors.get_route([7.0, 48.0], [8.0, 49.0])
        
        assert "features" in result
        assert len(result["features"]) > 0
        mock_get.assert_called_once()
    
    @patch("src.services.ors_service.requests.get")
    def test_get_route_network_error(self, mock_get, monkeypatch):
        """Test d'erreur réseau."""
        monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
        
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        
        from src.services.ors_service import ORSService
        ors = ORSService()
        
        result = ors.get_route([7.0, 48.0], [8.0, 49.0])
        
        assert "error" in result
        assert "Connection failed" in result["error"]
    
    @patch("src.services.ors_service.requests.get")
    def test_get_route_timeout(self, mock_get, monkeypatch):
        """Test de timeout."""
        monkeypatch.setenv("ORS_BASE_URL", "http://localhost:8082/ors")
        
        mock_get.side_effect = requests.Timeout("Request timeout")
        
        from src.services.ors_service import ORSService
        ors = ORSService()
        
        result = ors.get_route([7.0, 48.0], [8.0, 49.0])
        
        assert "error" in result
        assert "timeout" in result["error"].lower()
    
    @pytest.mark.integration
    def test_real_ors_call(self):
        """Test d'appel réel à ORS (nécessite instance ORS active)."""
        import os
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            pytest.skip("Tests d'intégration désactivés")
        
        from src.services.ors_service import ORSService
        ors = ORSService()
        
        if not ors.test_all_set():
            pytest.skip("Configuration ORS manquante")
        
        # Test avec coordonnées réelles
        result = ors.get_route([7.448595, 48.262004], [3.114432, 45.784832])
        
        if "error" not in result:
            assert "features" in result
            assert len(result["features"]) > 0

class TestORSIntegration:
    """Tests d'intégration avec ORS."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_multiple_route_requests(self):
        """Test de requêtes multiples pour détecter les fuites."""
        from src.services.ors_service import ORSService
        
        ors = ORSService()
        if not ors.test_all_set():
            pytest.skip("Configuration ORS manquante")
        
        coordinates_pairs = [
            ([7.0, 48.0], [8.0, 49.0]),
            ([4.8, 46.7], [5.2, 47.1]),
            ([3.1, 45.8], [3.5, 46.0])
        ]
        
        results = []
        for start, end in coordinates_pairs:
            result = ors.get_route(start, end)
            results.append(result)
        
        # Vérification que toutes les requêtes ont abouti
        successful_results = [r for r in results if "error" not in r]
        assert len(successful_results) >= len(coordinates_pairs) * 0.8  # 80% de succès minimum
```

---

### **4. test_api_optimization.py** - Tests d'Optimisation

Tests des algorithmes d'optimisation d'itinéraires.

#### **Structure de test recommandée**
```python
import pytest
import requests
from unittest.mock import patch, MagicMock

class TestOptimizationAlgorithms:
    """Tests des algorithmes d'optimisation."""
    
    @pytest.mark.optimization
    def test_zero_toll_optimization(self, client):
        """Test d'optimisation sans péage."""
        payload = {
            "coordinates": [
                [7.448595, 48.262004],  # Sélestat
                [3.114432, 45.784832]   # Clermont-Ferrand
            ],
            "max_tolls": 0
        }
        
        response = client.post('/api/smart-route/tolls', json=payload)
        
        assert response.status_code == 200
        data = response.get_json()
        
        if data.get("success"):
            assert data.get("tolls_count", 0) == 0
    
    @pytest.mark.optimization
    def test_single_toll_optimization(self, client):
        """Test d'optimisation avec un péage."""
        payload = {
            "coordinates": [
                [7.448595, 48.262004],
                [3.114432, 45.784832]
            ],
            "max_tolls": 1
        }
        
        response = client.post('/api/smart-route/tolls', json=payload)
        
        assert response.status_code == 200
        data = response.get_json()
        
        if data.get("success"):
            assert data.get("tolls_count", 0) <= 1
    
    @pytest.mark.optimization
    @pytest.mark.slow
    def test_complex_route_optimization(self, client):
        """Test d'optimisation sur route complexe."""
        payload = {
            "coordinates": [
                [2.3522, 48.8566],   # Paris
                [5.3698, 43.2965],   # Marseille
                [2.1204, 41.3851]    # Barcelone (international)
            ],
            "max_tolls": 3
        }
        
        response = client.post('/api/smart-route/tolls', json=payload)
        
        # Le service peut retourner une erreur pour les routes internationales
        assert response.status_code in [200, 400]

class TestOptimizationPerformance:
    """Tests de performance de l'optimisation."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_optimization_response_time(self, client):
        """Test du temps de réponse de l'optimisation."""
        import time
        
        payload = {
            "coordinates": [
                [7.448595, 48.262004],
                [3.114432, 45.784832]
            ],
            "max_tolls": 2
        }
        
        start_time = time.time()
        response = client.post('/api/smart-route/tolls', json=payload)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # L'optimisation ne devrait pas prendre plus de 30 secondes
        assert response_time < 30.0
        assert response.status_code == 200

class TestOptimizationEdgeCases:
    """Tests des cas limites d'optimisation."""
    
    def test_same_start_end_coordinates(self, client):
        """Test avec coordonnées identiques début/fin."""
        payload = {
            "coordinates": [
                [7.448595, 48.262004],
                [7.448595, 48.262004]  # Même point
            ],
            "max_tolls": 1
        }
        
        response = client.post('/api/smart-route/tolls', json=payload)
        
        # Devrait retourner une erreur ou route de distance 0
        assert response.status_code in [200, 400]
    
    def test_invalid_coordinates(self, client):
        """Test avec coordonnées invalides."""
        payload = {
            "coordinates": [
                [200.0, 100.0],  # Coordonnées invalides
                [3.114432, 45.784832]
            ],
            "max_tolls": 1
        }
        
        response = client.post('/api/smart-route/tolls', json=payload)
        assert response.status_code == 400
    
    def test_negative_max_tolls(self, client):
        """Test avec nombre de péages négatif."""
        payload = {
            "coordinates": [
                [7.448595, 48.262004],
                [3.114432, 45.784832]
            ],
            "max_tolls": -1
        }
        
        response = client.post('/api/smart-route/tolls', json=payload)
        assert response.status_code == 400
```

## 🔧 Outils et utilitaires de test

### **Commandes de test**
```bash
# Tests de base
pytest

# Tests avec coverage
pytest --cov=src --cov-report=html

# Tests spécifiques
pytest tests/test_routes.py
pytest -k "test_optimization"
pytest -m "unit"  # Tests unitaires seulement
pytest -m "not slow"  # Exclure les tests lents

# Tests avec logs détaillés
pytest -v -s

# Tests parallèles
pytest -n auto

# Tests d'intégration
RUN_INTEGRATION_TESTS=1 pytest -m integration

# Tests lents
RUN_SLOW_TESTS=1 pytest -m slow
```

### **Fixtures avancées**
```python
# fixtures/database.py
@pytest.fixture(scope="session")
def database_setup():
    """Setup de base de données pour les tests."""
    # Création de DB temporaire
    db_path = tempfile.mktemp(suffix=".db")
    
    # Migration et données de test
    setup_test_database(db_path)
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)

# fixtures/performance.py
@pytest.fixture
def performance_monitor():
    """Monitor de performance pour les tests."""
    import time
    import psutil
    
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    yield
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss
    
    duration = end_time - start_time
    memory_delta = end_memory - start_memory
    
    print(f"⏱️ Test duration: {duration:.3f}s")
    print(f"💾 Memory delta: {memory_delta / 1024 / 1024:.1f}MB")

# fixtures/mocks.py
@pytest.fixture
def mock_external_services():
    """Mock de tous les services externes."""
    with patch('src.services.ors_service.ORSService') as mock_ors, \
         patch('requests.get') as mock_requests:
        
        # Configuration des mocks
        mock_ors.return_value.test_all_set.return_value = True
        mock_requests.return_value.json.return_value = {"status": "ok"}
        
        yield {
            'ors': mock_ors,
            'requests': mock_requests
        }
```

### **Helpers de test**
```python
# helpers/assertions.py
def assert_valid_geojson(data):
    """Vérifie qu'un objet est un GeoJSON valide."""
    assert isinstance(data, dict)
    assert "type" in data
    assert data["type"] in ["Feature", "FeatureCollection"]
    
    if data["type"] == "FeatureCollection":
        assert "features" in data
        assert isinstance(data["features"], list)

def assert_valid_coordinates(coords):
    """Vérifie la validité des coordonnées."""
    assert isinstance(coords, list)
    assert len(coords) == 2
    
    lon, lat = coords
    assert -180 <= lon <= 180
    assert -90 <= lat <= 90

def assert_optimization_result(result):
    """Vérifie la structure d'un résultat d'optimisation."""
    assert isinstance(result, dict)
    
    required_fields = ["success", "found_solution"]
    for field in required_fields:
        assert field in result
    
    if result.get("success"):
        assert "total_cost" in result
        assert "tolls_count" in result
        assert isinstance(result["total_cost"], (int, float))
        assert isinstance(result["tolls_count"], int)

# helpers/test_data.py
def create_test_toll_booth(osm_id="test_toll", name="Test Toll", operator="TEST"):
    """Crée une station de péage de test."""
    return {
        "osm_id": osm_id,
        "name": name,
        "operator": operator,
        "coordinates": [4.8567, 46.7892],
        "toll_type": "O",
        "properties": {"highway": "toll_booth"}
    }

def create_test_route(start_coords=None, end_coords=None):
    """Crée une route de test."""
    if start_coords is None:
        start_coords = [7.448595, 48.262004]
    if end_coords is None:
        end_coords = [3.114432, 45.784832]
    
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [start_coords, end_coords]
            },
            "properties": {
                "summary": {
                    "distance": 456789,
                    "duration": 16420
                }
            }
        }]
    }
```

## 📊 Métriques et reporting

### **Coverage et métriques**
```python
# conftest.py - Configuration coverage
def pytest_configure(config):
    """Configuration personnalisée de pytest."""
    config.addinivalue_line(
        "markers", "unit: tests unitaires rapides"
    )
    config.addinivalue_line(
        "markers", "integration: tests d'intégration"
    )

def pytest_collection_modifyitems(config, items):
    """Modification des items collectés."""
    for item in items:
        # Auto-marquage basé sur le nom du fichier
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)

# Reporting personnalisé
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Résumé personnalisé en fin de tests."""
    if hasattr(terminalreporter, 'stats'):
        passed = len(terminalreporter.stats.get('passed', []))
        failed = len(terminalreporter.stats.get('failed', []))
        skipped = len(terminalreporter.stats.get('skipped', []))
        
        total = passed + failed + skipped
        if total > 0:
            success_rate = (passed / total) * 100
            terminalreporter.write_line(f"\n📊 Taux de réussite: {success_rate:.1f}%")
```
