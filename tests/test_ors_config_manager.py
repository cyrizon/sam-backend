"""
Tests pour ORSConfigManager - Configuration centralisée ORS.
"""
import pytest
from src.services.ors_config_manager import ORSConfigManager


class TestORSConfigManager:
    """Tests pour la configuration ORS."""
    
    def test_validate_coordinates_valid(self):
        """Test validation de coordonnées valides."""
        coordinates = [[7.0, 48.0], [8.0, 49.0]]
        
        assert ORSConfigManager.validate_coordinates(coordinates) is True
    
    def test_validate_coordinates_empty(self):
        """Test validation coordonnées vides."""
        with pytest.raises(ValueError, match="Au moins 2 coordonnées sont requises"):
            ORSConfigManager.validate_coordinates([])
    
    def test_validate_coordinates_single_point(self):
        """Test validation avec un seul point."""
        with pytest.raises(ValueError, match="Au moins 2 coordonnées sont requises"):
            ORSConfigManager.validate_coordinates([[7.0, 48.0]])
    
    def test_validate_coordinates_invalid_format(self):
        """Test validation format invalide."""
        with pytest.raises(ValueError, match="format attendu \\[longitude, latitude\\]"):
            ORSConfigManager.validate_coordinates([[7.0], [8.0, 49.0]])
    
    def test_validate_coordinates_non_numeric(self):
        """Test validation coordonnées non numériques."""
        with pytest.raises(ValueError, match="doivent être numériques"):
            ORSConfigManager.validate_coordinates([["7.0", 48.0], [8.0, 49.0]])
    
    def test_validate_coordinates_longitude_out_of_bounds(self):
        """Test validation longitude hors limites."""
        with pytest.raises(ValueError, match="Longitude .* hors limites"):
            ORSConfigManager.validate_coordinates([[200.0, 48.0], [8.0, 49.0]])
    
    def test_validate_coordinates_latitude_out_of_bounds(self):
        """Test validation latitude hors limites."""
        with pytest.raises(ValueError, match="Latitude .* hors limites"):
            ORSConfigManager.validate_coordinates([[7.0, 100.0], [8.0, 49.0]])
    
    def test_calculate_timeout_base(self):
        """Test calcul timeout de base."""
        payload = {"coordinates": [[7.0, 48.0], [8.0, 49.0]]}
        
        timeout = ORSConfigManager.calculate_timeout(payload)
        
        assert timeout == ORSConfigManager.BASE_TIMEOUT
    
    def test_calculate_timeout_multiple_coordinates(self):
        """Test calcul timeout avec coordonnées multiples."""
        payload = {
            "coordinates": [[7.0, 48.0], [7.5, 48.5], [8.0, 49.0]]  # 3 points
        }
        
        timeout = ORSConfigManager.calculate_timeout(payload)
        
        # BASE_TIMEOUT + (3-2)*2 = 10 + 2 = 12
        assert timeout == ORSConfigManager.BASE_TIMEOUT + 2
    
    def test_calculate_timeout_avoid_polygons(self):
        """Test calcul timeout avec évitement de polygones."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "options": {
                "avoid_polygons": {
                    "coordinates": [[[1, 1], [2, 2]], [[3, 3], [4, 4]]]  # 2 polygones
                }
            }
        }
        
        timeout = ORSConfigManager.calculate_timeout(payload)
        
        # BASE_TIMEOUT + 2*3 = 10 + 6 = 16
        assert timeout == ORSConfigManager.BASE_TIMEOUT + 6
    
    def test_calculate_timeout_avoid_features(self):
        """Test calcul timeout avec évitement de features."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "options": {"avoid_features": ["tollways"]}
        }
        
        timeout = ORSConfigManager.calculate_timeout(payload)
        
        # BASE_TIMEOUT + 5 = 15
        assert timeout == ORSConfigManager.BASE_TIMEOUT + 5
    
    def test_calculate_timeout_extra_info(self):
        """Test calcul timeout avec extra_info."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "extra_info": ["tollways", "surface"]
        }
        
        timeout = ORSConfigManager.calculate_timeout(payload)
        
        # BASE_TIMEOUT + 2*2 = 14
        assert timeout == ORSConfigManager.BASE_TIMEOUT + 4
    
    def test_calculate_timeout_max_cap(self):
        """Test calcul timeout avec cap maximum."""
        payload = {
            "coordinates": [[7.0, 48.0], [7.1, 48.1], [7.2, 48.2], [7.3, 48.3], [8.0, 49.0]],
            "options": {
                "avoid_polygons": {
                    "coordinates": [[[i, i], [i+1, i+1]] for i in range(10)]  # 10 polygones
                },
                "avoid_features": ["tollways"]
            },
            "extra_info": ["tollways", "surface", "waytype"]
        }
        
        timeout = ORSConfigManager.calculate_timeout(payload)
        
        # Devrait être cappé au maximum
        assert timeout == ORSConfigManager.MAX_TIMEOUT
    
    def test_get_operation_name_base(self):
        """Test détermination nom d'opération pour route de base."""
        payload = {"coordinates": [[7.0, 48.0], [8.0, 49.0]]}
        
        name = ORSConfigManager.get_operation_name(payload)
        
        assert name == "ORS_base_route"
    
    def test_get_operation_name_avoid_polygons(self):
        """Test détermination nom d'opération pour évitement polygones."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "options": {"avoid_polygons": {"coordinates": []}}
        }
        
        name = ORSConfigManager.get_operation_name(payload)
        
        assert name == "ORS_alternative_route"
    
    def test_get_operation_name_avoid_features(self):
        """Test détermination nom d'opération pour évitement features."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "options": {"avoid_features": ["tollways"]}
        }
        
        name = ORSConfigManager.get_operation_name(payload)
        
        assert name == "ORS_avoid_tollways"
    
    def test_optimize_payload_add_tollways(self):
        """Test optimisation payload ajoute tollways."""
        payload = {"coordinates": [[7.0, 48.0], [8.0, 49.0]]}
        
        optimized = ORSConfigManager.optimize_payload(payload)
        
        assert "extra_info" in optimized
        assert "tollways" in optimized["extra_info"]
    
    def test_optimize_payload_preserve_existing(self):
        """Test optimisation payload préserve extra_info existant."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "extra_info": ["surface"]
        }
        
        optimized = ORSConfigManager.optimize_payload(payload)
        
        assert "surface" in optimized["extra_info"]
        assert "tollways" in optimized["extra_info"]
    
    def test_optimize_payload_remove_empty_options(self):
        """Test optimisation payload supprime options vides."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "options": {}
        }
        
        optimized = ORSConfigManager.optimize_payload(payload)
        
        assert "options" not in optimized
    
    def test_get_request_priority_high(self):
        """Test priorité haute pour route simple."""
        payload = {"coordinates": [[7.0, 48.0], [8.0, 49.0]]}
        
        priority = ORSConfigManager.get_request_priority(payload)
        
        assert priority == "high"
    
    def test_get_request_priority_medium(self):
        """Test priorité moyenne pour évitement features."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "options": {"avoid_features": ["tollways"]}
        }
        
        priority = ORSConfigManager.get_request_priority(payload)
        
        assert priority == "medium"
    
    def test_get_request_priority_low(self):
        """Test priorité basse pour évitement polygones."""
        payload = {
            "coordinates": [[7.0, 48.0], [8.0, 49.0]],
            "options": {"avoid_polygons": {"coordinates": []}}
        }
        
        priority = ORSConfigManager.get_request_priority(payload)
        
        assert priority == "low"