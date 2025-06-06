"""
Tests pour RouteValidator - Validation centralisée des contraintes.
"""
import pytest
from src.services.toll.route_validator import RouteValidator
from src.services.toll.exceptions import (
    MaxTollsExceededError, AvoidedTollsStillPresentError, TargetTollMissingError
)


class TestRouteValidator:
    """Tests pour la validation des routes."""
    
    def test_validate_max_tolls_valid(self):
        """Test validation nombre de péages valide."""
        assert RouteValidator.validate_max_tolls(2, 3, "test_op") is True
        assert RouteValidator.validate_max_tolls(3, 3, "test_op") is True
    
    def test_validate_max_tolls_invalid(self, capsys):
        """Test validation nombre de péages invalide."""
        result = RouteValidator.validate_max_tolls(4, 3, "test_op")
        
        assert result is False
        captured = capsys.readouterr()
        assert "4 péages > max_tolls=3" in captured.out
        assert "pour test_op" in captured.out
    
    def test_validate_avoided_tolls_none(self):
        """Test validation avec aucun péage à éviter."""
        route_tolls = [{"id": "toll_1"}, {"id": "toll_2"}]
        
        assert RouteValidator.validate_avoided_tolls(route_tolls, None) is True
        assert RouteValidator.validate_avoided_tolls(route_tolls, []) is True
    
    def test_validate_avoided_tolls_success(self):
        """Test validation péages évités avec succès."""
        route_tolls = [{"id": "toll_1"}, {"id": "toll_2"}]
        avoided_tolls = [{"id": "toll_3"}, {"id": "toll_4"}]
        
        assert RouteValidator.validate_avoided_tolls(route_tolls, avoided_tolls) is True
    
    def test_validate_avoided_tolls_failure(self, capsys):
        """Test validation péages évités échoue."""
        route_tolls = [{"id": "toll_1"}, {"id": "toll_2"}]
        avoided_tolls = [{"id": "toll_1"}, {"id": "toll_3"}]  # toll_1 présent
        
        result = RouteValidator.validate_avoided_tolls(route_tolls, avoided_tolls, "test_op")
        
        assert result is False
        captured = capsys.readouterr()
        assert "péages à éviter sont toujours présents" in captured.out
    
    def test_validate_target_toll_present_success(self):
        """Test validation péage cible présent."""
        route_tolls = [{"id": "toll_1"}, {"id": "toll_2"}]
        
        assert RouteValidator.validate_target_toll_present(route_tolls, "toll_1") is True
    
    def test_validate_target_toll_present_failure(self, capsys):
        """Test validation péage cible absent."""
        route_tolls = [{"id": "toll_1"}, {"id": "toll_2"}]
        
        result = RouteValidator.validate_target_toll_present(route_tolls, "toll_3", "test_op")
        
        assert result is False
        captured = capsys.readouterr()
        assert "toll_3 n'est pas présent" in captured.out
    
    def test_validate_unwanted_tolls_avoided_success(self):
        """Test validation péages indésirables évités."""
        route_tolls = [{"id": "target_toll"}]
        
        assert RouteValidator.validate_unwanted_tolls_avoided(
            route_tolls, "target_toll", "part1"
        ) is True
    
    def test_validate_unwanted_tolls_avoided_failure(self, capsys):
        """Test validation péages indésirables présents."""
        route_tolls = [{"id": "target_toll"}, {"id": "unwanted_toll"}]
        
        result = RouteValidator.validate_unwanted_tolls_avoided(
            route_tolls, "target_toll", "part1"
        )
        
        assert result is False
        captured = capsys.readouterr()
        assert "Impossible d'éviter les péages indésirables" in captured.out
    
    def test_validate_all_constraints_success(self):
        """Test validation complète réussie."""
        route_tolls = [{"id": "toll_1"}]
        
        result = RouteValidator.validate_all_constraints(
            route_tolls=route_tolls,
            toll_count=1,
            max_tolls=2,
            avoided_tolls=[{"id": "toll_2"}],
            target_toll_id="toll_1",
            operation_name="test_op"
        )
        
        assert result is True
    
    def test_validate_all_constraints_failure_max_tolls(self, capsys):
        """Test validation complète échoue sur max_tolls."""
        route_tolls = [{"id": "toll_1"}, {"id": "toll_2"}]
        
        result = RouteValidator.validate_all_constraints(
            route_tolls=route_tolls,
            toll_count=2,
            max_tolls=1,
            operation_name="test_op"
        )
        
        assert result is False
    
    def test_validate_max_tolls_strict_success(self):
        """Test validation stricte max_tolls réussie."""
        RouteValidator.validate_max_tolls_strict(2, 3, "test_op")  # Ne lève pas d'exception
    
    def test_validate_max_tolls_strict_failure(self):
        """Test validation stricte max_tolls échoue."""
        with pytest.raises(MaxTollsExceededError) as exc_info:
            RouteValidator.validate_max_tolls_strict(4, 3, "test_op")
        
        assert exc_info.value.found_tolls == 4
        assert exc_info.value.max_tolls == 3
        assert "pour test_op" in str(exc_info.value)
    
    def test_validate_avoided_tolls_strict_failure(self):
        """Test validation stricte péages évités échoue."""
        route_tolls = [{"id": "toll_1"}]
        avoided_tolls = [{"id": "toll_1"}]
        
        with pytest.raises(AvoidedTollsStillPresentError) as exc_info:
            RouteValidator.validate_avoided_tolls_strict(route_tolls, avoided_tolls, "test_op")
        
        assert "toll_1" in str(exc_info.value.present_tolls)
    
    def test_validate_target_toll_present_strict_failure(self):
        """Test validation stricte péage cible échoue."""
        route_tolls = [{"id": "toll_1"}]
        
        with pytest.raises(TargetTollMissingError) as exc_info:
            RouteValidator.validate_target_toll_present_strict(route_tolls, "toll_2", "test_op")
        
        assert exc_info.value.toll_id == "toll_2"
        assert exc_info.value.operation_name == "test_op"
    
    def test_validate_all_constraints_strict_success(self):
        """Test validation stricte complète réussie."""
        route_tolls = [{"id": "toll_1"}]
        
        RouteValidator.validate_all_constraints_strict(
            route_tolls=route_tolls,
            toll_count=1,
            max_tolls=2,
            target_toll_id="toll_1",
            operation_name="test_op"
        )  # Ne lève pas d'exception