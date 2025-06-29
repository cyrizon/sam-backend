"""
Test Final - Architecture Route Optimization V2
===============================================

Test complet de l'architecture refactorisée.
"""

def test_architecture_integration():
    """Test d'intégration de toute l'architecture."""
    print("🧪 Test d'intégration de l'architecture V2...")
    
    # Test des imports principaux
    try:
        print("📦 Test des imports...")
        
        # Cache et utils
        from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
        print("   ✅ CacheAccessor importé")
        
        # Index spatiaux
        from src.services.toll.route_optimization.toll_analysis.spatial.unified_spatial_manager import UnifiedSpatialIndexManager
        print("   ✅ UnifiedSpatialIndexManager importé")
        
        # Modules principaux
        from src.services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier
        from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
        from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
        print("   ✅ Modules principaux importés")
        
        # Test d'initialisation
        print("\n🚀 Test d'initialisation...")
        
        # Mock du service ORS
        class MockORS:
            pass
        
        mock_ors = MockORS()
        
        # Test TollIdentifier
        toll_identifier = TollIdentifier()
        print("   ✅ TollIdentifier initialisé")
        
        # Test TollSelector  
        toll_selector = TollSelector()
        print("   ✅ TollSelector initialisé")
        
        # Test IntelligentOptimizer
        optimizer = IntelligentOptimizer(mock_ors)
        print("   ✅ IntelligentOptimizer initialisé")
        
        # Test des statistiques
        print("\n📊 Test des statistiques...")
        
        cache_stats = CacheAccessor.get_cache_stats()
        print(f"   Cache V2: {cache_stats['complete_links']} liens, {cache_stats['toll_stations']} péages")
        
        optimizer_stats = optimizer.get_optimizer_stats()
        print(f"   Optimizer: {len(optimizer_stats['modules_loaded'])} modules chargés")
        
        # Test index spatial
        spatial_manager = UnifiedSpatialIndexManager()
        spatial_stats = spatial_manager.get_unified_stats()
        print(f"   Index spatial: {spatial_stats['toll_index']['total_tolls']} péages indexés")
        
        print("\n✅ Architecture V2 complètement fonctionnelle !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_file_sizes():
    """Vérifie que tous les fichiers respectent la contrainte de taille."""
    import os
    
    print("\n📏 Vérification des tailles de fichiers...")
    
    route_opt_path = "src/services/toll/route_optimization"
    oversized_files = []
    
    for root, dirs, files in os.walk(route_opt_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                    
                    if lines > 300:
                        oversized_files.append((file_path, lines))
                    
                except Exception as e:
                    print(f"   ⚠️ Erreur lecture {file_path}: {e}")
    
    if oversized_files:
        print("❌ Fichiers dépassant 300 lignes:")
        for file_path, lines in oversized_files:
            print(f"   • {file_path}: {lines} lignes")
        return False
    else:
        print("✅ Tous les fichiers respectent la contrainte (<300 lignes)")
        return True


if __name__ == "__main__":
    print("🎯 TEST FINAL DE L'ARCHITECTURE V2")
    print("=" * 50)
    
    # Test des tailles
    size_ok = check_file_sizes()
    
    # Test d'intégration
    integration_ok = test_architecture_integration()
    
    print("\n" + "=" * 50)
    if size_ok and integration_ok:
        print("🎉 ARCHITECTURE V2 VALIDÉE !")
        print("✅ Contraintes respectées")
        print("✅ Intégration fonctionnelle") 
        print("✅ Cache V2 intégré")
        print("✅ Index spatiaux opérationnels")
    else:
        print("❌ Problèmes détectés dans l'architecture")
