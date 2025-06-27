"""
Test Architecture Route Optimization
====================================

Test rapide de la nouvelle architecture modulaire.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_import_modules():
    """Test des imports des modules principaux."""
    print("🧪 Test des imports de l'architecture...")
    
    try:
        # Test imports utils d'abord
        from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
        from src.services.toll.route_optimization.utils.distance_calculator import DistanceCalculator
        from src.services.toll.route_optimization.utils.route_extractor import RouteExtractor
        print("✅ Import utils réussi")
        
        # Test import route handling
        from src.services.toll.route_optimization.route_handling.base_route_provider import BaseRouteProvider
        from src.services.toll.route_optimization.route_handling.tollway_processor import TollwayProcessor
        print("✅ Import route_handling réussi")
        
        # Test import spatial
        from src.services.toll.route_optimization.toll_analysis.spatial.spatial_index import SpatialIndexManager
        print("✅ Import spatial réussi")
        
        # Test import detection
        from src.services.toll.route_optimization.toll_analysis.detection.distance_calculator import OptimizedDistanceCalculator
        from src.services.toll.route_optimization.toll_analysis.detection.toll_classifier import TollClassifier
        print("✅ Import detection réussi")
        
        # Test import toll analysis
        from src.services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier
        from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
        print("✅ Import toll_analysis réussi")
        
        # Test import segmentation
        from src.services.toll.route_optimization.segmentation.segment_creator import SegmentCreator
        from src.services.toll.route_optimization.segmentation.segment_calculator import SegmentCalculator
        print("✅ Import segmentation réussi")
        
        # Test import assembly
        from src.services.toll.route_optimization.assembly.route_assembler import RouteAssembler
        print("✅ Import assembly réussi")
        
        # Test import principal (en dernier)
        from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
        print("✅ Import IntelligentOptimizer réussi")
        
        print("🎉 Tous les imports réussis !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur import : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_access():
    """Test d'accès au cache."""
    print("\n🧪 Test d'accès au cache...")
    
    try:
        from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
        
        # Test statistiques cache
        stats = CacheAccessor.get_cache_stats()
        print(f"📊 Statistiques cache : {stats}")
        
        if stats['available']:
            print("✅ Cache disponible et accessible")
        else:
            print("⚠️ Cache non disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur accès cache : {e}")
        return False

def test_spatial_index():
    """Test de l'index spatial."""
    print("\n🧪 Test de l'index spatial...")
    
    try:
        from src.services.toll.route_optimization.toll_analysis.spatial.spatial_index import SpatialIndexManager
        
        # Initialiser l'index
        spatial_manager = SpatialIndexManager()
        
        # Test statistiques
        stats = spatial_manager.get_index_stats()
        print(f"🗂️ Statistiques index spatial : {stats}")
        
        if stats['index_available']:
            print("✅ Index spatial construit avec succès")
        else:
            print("⚠️ Index spatial non disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur index spatial : {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test de l'architecture Route Optimization")
    print("=" * 50)
    
    success = True
    success &= test_import_modules()
    success &= test_cache_access()
    success &= test_spatial_index()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Architecture fonctionnelle !")
    else:
        print("❌ Problèmes détectés dans l'architecture")
