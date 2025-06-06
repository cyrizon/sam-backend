"""
Tests pour les exceptions personnalisées.
"""
import pytest
from src.services.toll.exceptions import (
    TollOptimizationError, ORSConnectionError, NoTollRouteError,
    MaxTollsExceededError, TargetTollMissingError, AvoidedTollsStillPresentError
)
from src.services.toll.constants import TollOptimizationConfig as Config


class TestTollOptimizationError:
    """Tests pour l'exception de base."""
    
    def test_basic_exception(self):
        """Test exception de base."""
        error = TollOptimizationError("Test message", "TEST_STATUS", "test_operation")
        
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.status_code == "TEST_STATUS"
        assert error.operation_name == "test_operation"
    
    def test_to_dict(self):
        """Test conversion en dictionnaire."""
        error = TollOptimizationError("Test message", "TEST_STATUS", "test_operation")
        
        error_dict = error.to_dict()
        
        assert error_dict["error"] == "TollOptimizationError"
        assert error_dict["message"] == "Test message"
        assert error_dict["status_code"] == "TEST_STATUS"
        assert error_dict["operation"] == "test_operation"


class TestORSConnectionError:
    """Tests pour les erreurs de connexion ORS."""
    
    def test_ors_connection_error(self):
        """Test erreur de connexion ORS."""
        original = Exception("Connection timeout")
        error = ORSConnectionError("ORS connection failed", original)
        
        assert "ORS connection failed" in str(error)
        assert error.status_code == Config.StatusCodes.ORS_CONNECTION_ERROR
        assert error.operation_name == "ORS_API_CALL"
        assert error.original_exception == original


class TestNoTollRouteError:
    """Tests pour les erreurs de route sans péage."""
    
    def test_no_toll_route_error_default(self):
        """Test erreur route sans péage avec message par défaut."""
        error = NoTollRouteError()
        
        assert "Impossible de trouver un itinéraire sans péage" in str(error)
        assert error.max_tolls == 0
        assert error.status_code == Config.StatusCodes.NO_TOLL_ROUTE_NOT_POSSIBLE
    
    def test_no_toll_route_error_custom(self):
        """Test erreur route sans péage avec message personnalisé."""
        error = NoTollRouteError("Message personnalisé")
        
        assert str(error) == "Message personnalisé"
        assert error.max_tolls == 0


class TestMaxTollsExceededError:
    """Tests pour les erreurs de dépassement de péages."""
    
    def test_max_tolls_exceeded_basic(self):
        """Test erreur dépassement péages basique."""
        error = MaxTollsExceededError(5, 3)
        
        assert "5 péages > max_tolls=3" in str(error)
        assert error.found_tolls == 5
        assert error.max_tolls == 3
    
    def test_max_tolls_exceeded_with_operation(self):
        """Test erreur dépassement péages avec opération."""
        error = MaxTollsExceededError(4, 2, "test_operation")
        
        assert "4 péages > max_tolls=2" in str(error)
        assert "pour test_operation" in str(error)
        assert error.operation_name == "test_operation"


class TestTargetTollMissingError:
    """Tests pour les erreurs de péage cible manquant."""
    
    def test_target_toll_missing_basic(self):
        """Test erreur péage cible manquant basique."""
        error = TargetTollMissingError("toll_123")
        
        assert "toll_123 n'est pas présent dans l'itinéraire final" in str(error)
        assert error.toll_id == "toll_123"
        assert error.validation_type == "target_toll_missing"
    
    def test_target_toll_missing_with_operation(self):
        """Test erreur péage cible manquant avec opération."""
        error = TargetTollMissingError("toll_456", "test_operation")
        
        assert "toll_456" in str(error)
        assert "pour test_operation" in str(error)
        assert error.operation_name == "test_operation"


class TestAvoidedTollsStillPresentError:
    """Tests pour les erreurs de péages évités toujours présents."""
    
    def test_avoided_tolls_still_present_basic(self):
        """Test erreur péages évités présents basique."""
        present_tolls = {"toll_1", "toll_2"}
        error = AvoidedTollsStillPresentError(present_tolls)
        
        assert "péages à éviter sont toujours présents" in str(error)
        assert error.present_tolls == present_tolls
        assert error.validation_type == "avoided_tolls"
    
    def test_avoided_tolls_still_present_with_operation(self):
        """Test erreur péages évités présents avec opération."""
        present_tolls = {"toll_3"}
        error = AvoidedTollsStillPresentError(present_tolls, "test_operation")
        
        assert "toll_3" in str(error)
        assert "pour test_operation" in str(error)
        assert error.operation_name == "test_operation"