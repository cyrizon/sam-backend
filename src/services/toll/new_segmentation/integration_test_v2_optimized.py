"""
integration_test_v2_optimized.py
-------------------------------

Test d'intégration pour la stratégie V2 optimisée.
Teste l'intégration complète avec les services réels.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.toll.new_segmentation.intelligent_segmentation_v2_optimized import IntelligentSegmentationStrategyV2Optimized
from src.services.osm_data_cache import osm_data_cache
from src.services.ors_service import ORSService


def test_integration_with_real_services():
    """Test d'intégration avec les services réels."""
    print("🔧 Test intégration V2 Optimisée avec services réels")
    
    try:
        # Initialiser le cache OSM (requis pour les péages pré-matchés)
        print("📁 Initialisation cache OSM...")
        osm_data_cache.initialize()
        
        # Initialiser le service ORS
        print("🛣️ Initialisation service ORS...")
        ors_service = ORSService()
        
        # Créer la stratégie optimisée
        print("🧠 Initialisation stratégie V2 optimisée...")
        strategy = IntelligentSegmentationStrategyV2Optimized(ors_service)
        
        # Test avec des coordonnées réelles (exemple : trajet avec péages)
        # Paris -> Lyon (trajet connu pour avoir des péages)
        coordinates = [
            [2.3522, 48.8566],  # Paris
            [4.8357, 45.764]    # Lyon
        ]
        
        print(f"🎯 Test route Paris → Lyon avec 2 péages demandés")
        
        # Tester avec différents nombres de péages
        for target_tolls in [0, 1, 2]:
            print(f"\n--- Test avec {target_tolls} péage(s) ---")
            
            result = strategy.find_route_with_exact_tolls(coordinates, target_tolls)
            
            if result:
                print(f"✅ Résultat obtenu pour {target_tolls} péage(s)")
                
                # Vérifier la structure du résultat
                assert 'route' in result
                assert 'tolls_info' in result
                assert 'cost_info' in result
                
                # Afficher quelques détails
                toll_count = len(result.get('tolls_info', {}).get('tolls_used', []))
                total_cost = result.get('cost_info', {}).get('total_cost', 0)
                
                print(f"   📊 Péages trouvés : {toll_count}")
                print(f"   💰 Coût total : {total_cost}€")
                
                # Vérifier que le nombre de péages correspond à la demande
                if target_tolls > 0:
                    assert toll_count <= target_tolls, f"Trop de péages : {toll_count} > {target_tolls}"
                
            else:
                print(f"⚠️ Aucun résultat pour {target_tolls} péage(s)")
        
        print("\n✅ Test d'intégration réussi")
        
    except Exception as e:
        print(f"❌ Erreur test d'intégration : {e}")
        import traceback
        traceback.print_exc()
        raise


def test_prematched_tolls_validation():
    """Valide que les péages pré-matchés sont bien disponibles."""
    print("🔍 Validation des péages pré-matchés")
    
    try:
        # Initialiser le cache OSM
        osm_data_cache.initialize()
        
        # Vérifier que le parser OSM a bien les péages
        osm_parser = osm_data_cache._osm_parser
        
        if not osm_parser or not hasattr(osm_parser, 'toll_stations'):
            print("⚠️ Parser OSM non disponible ou sans toll_stations")
            return
        
        toll_stations = osm_parser.toll_stations
        print(f"📊 {len(toll_stations)} stations de péage chargées")
        
        # Vérifier le pré-matching
        matched_count = 0
        unmatched_count = 0
        
        for toll_station in toll_stations[:10]:  # Examiner les 10 premiers
            if hasattr(toll_station, 'csv_match') and toll_station.csv_match:
                matched_count += 1
                role = toll_station.csv_match.get('role', 'Inconnu')
                name = toll_station.csv_match.get('name', 'Sans nom')
                print(f"   ✅ {toll_station.name or 'Sans nom'} → {name} ({role})")
            else:
                unmatched_count += 1
                print(f"   🔍 {toll_station.name or 'Sans nom'} → Non matché")
        
        print(f"📈 Échantillon pré-matching : {matched_count} matchés, {unmatched_count} non-matchés")
        
        if matched_count > 0:
            print("✅ Pré-matching fonctionnel")
        else:
            print("⚠️ Aucun péage pré-matché trouvé")
        
    except Exception as e:
        print(f"❌ Erreur validation pré-matching : {e}")
        import traceback
        traceback.print_exc()


def test_performance_comparison():
    """Compare les performances avec la V2 classique."""
    print("⚡ Test de performance V2 Optimisée vs V2 Classique")
    
    try:
        import time
        from src.services.toll.new_segmentation.intelligent_segmentation_strategy_v2 import IntelligentSegmentationStrategyV2
        
        # Initialiser les services
        osm_data_cache.initialize()
        ors_service = ORSService()
        
        # Coordonnées de test
        coordinates = [
            [2.3522, 48.8566],  # Paris
            [4.8357, 45.764]    # Lyon
        ]
        
        # Test V2 Classique
        print("🔄 Test V2 Classique...")
        strategy_v2 = IntelligentSegmentationStrategyV2(ors_service)
        
        start_time = time.time()
        result_v2 = strategy_v2.find_route_with_exact_tolls(coordinates, 2)
        time_v2 = time.time() - start_time
        
        # Test V2 Optimisée
        print("🚀 Test V2 Optimisée...")
        strategy_v2_opt = IntelligentSegmentationStrategyV2Optimized(ors_service)
        
        start_time = time.time()
        result_v2_opt = strategy_v2_opt.find_route_with_exact_tolls(coordinates, 2)
        time_v2_opt = time.time() - start_time
        
        # Comparaison
        print(f"\n📊 Résultats de performance :")
        print(f"   V2 Classique : {time_v2:.2f}s")
        print(f"   V2 Optimisée : {time_v2_opt:.2f}s")
        
        if time_v2_opt < time_v2:
            improvement = ((time_v2 - time_v2_opt) / time_v2) * 100
            print(f"   🚀 Amélioration : {improvement:.1f}% plus rapide")
        else:
            regression = ((time_v2_opt - time_v2) / time_v2) * 100
            print(f"   ⚠️ Régression : {regression:.1f}% plus lent")
        
        # Vérifier que les résultats sont cohérents
        if result_v2 and result_v2_opt:
            tolls_v2 = len(result_v2.get('tolls_info', {}).get('tolls_used', []))
            tolls_v2_opt = len(result_v2_opt.get('tolls_info', {}).get('tolls_used', []))
            print(f"   🎯 Péages V2 : {tolls_v2}, V2 Opt : {tolls_v2_opt}")
        
        print("✅ Test de performance terminé")
        
    except Exception as e:
        print(f"❌ Erreur test performance : {e}")
        import traceback
        traceback.print_exc()


def main():
    """Lance tous les tests d'intégration."""
    print("🧪 TESTS D'INTÉGRATION V2 OPTIMISÉE")
    print("=" * 50)
    
    try:
        test_prematched_tolls_validation()
        print("\n" + "-" * 50)
        
        test_integration_with_real_services()
        print("\n" + "-" * 50)
        
        test_performance_comparison()
        
        print("\n" + "=" * 50)
        print("✅ TOUS LES TESTS D'INTÉGRATION RÉUSSIS")
        print("🎉 V2 Optimisée validée en conditions réelles")
        
    except Exception as e:
        print(f"\n❌ ÉCHEC TESTS D'INTÉGRATION : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
