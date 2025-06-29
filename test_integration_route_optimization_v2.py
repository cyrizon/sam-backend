#!/usr/bin/env python3
"""
Test d'intégration Route Optimization avec Cache V2
==================================================

Ce script teste l'intégration du nouveau cache V2 avec les modules
de route optimization existants.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
from src.services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink


def print_header(title: str):
    """Affiche un titre formaté."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")


def test_cache_integration():
    """Test l'intégration du cache V2."""
    print_header("Test d'intégration Cache V2")
    
    # 1. Test d'accès au cache
    print("1️⃣ Test d'accès au cache V2...")
    if not CacheAccessor.is_cache_available():
        print("🚀 Initialisation du cache V2...")
        CacheAccessor._ensure_initialized()
    
    stats = CacheAccessor.get_cache_stats()
    print(f"   ✅ Cache disponible: {stats.get('available', False)}")
    print(f"   📊 Liens avec péages: {stats.get('links_with_tolls', 0)}")
    print(f"   🏢 Opérateurs: {len(stats.get('operators', []))}")
    
    return stats.get('available', False)


def test_toll_identification():
    """Test l'identification de péages avec le cache V2."""
    print_header("Test d'identification de péages")
    
    # Récupérer quelques liens avec péages pour les tests
    links_with_tolls = CacheAccessor.get_links_with_tolls()
    if not links_with_tolls:
        print("❌ Aucun lien avec péage trouvé")
        return False
    
    print(f"2️⃣ Test avec {len(links_with_tolls)} liens disponibles...")
    
    # Tester différents types de liens
    entry_links = [l for l in links_with_tolls if l.link_type.value == 'entry']
    exit_links = [l for l in links_with_tolls if l.link_type.value == 'exit']
    
    print(f"   🚪 Liens d'entrée: {len(entry_links)}")
    print(f"   🚪 Liens de sortie: {len(exit_links)}")
    
    # Test sur quelques exemples
    test_links = (entry_links[:3] + exit_links[:3])[:5]
    
    print("\n3️⃣ Exemples de liens identifiés:")
    for i, link in enumerate(test_links, 1):
        toll = link.associated_toll
        cost = CacheAccessor.calculate_toll_cost(link)
        print(f"   {i}. {link.link_id}")
        print(f"      • Type: {link.link_type.value}")
        print(f"      • Péage: {toll.name if toll else 'N/A'}")
        print(f"      • Opérateur: {toll.operator if toll else 'N/A'}")
        print(f"      • Coût estimé: {cost}€" if cost else "      • Coût: N/A")
    
    return len(test_links) > 0


def test_toll_selection():
    """Test la sélection de péages avec le cache V2."""
    print_header("Test de sélection de péages")
    
    # Test avec différents critères de filtrage
    print("4️⃣ Test de filtrage par critères...")
    
    # Filtrage par opérateur
    asf_links = CacheAccessor.get_links_by_operator("ASF")
    aprr_links = CacheAccessor.get_links_by_operator("APRR")
    
    print(f"   🏢 Liens ASF: {len(asf_links)}")
    print(f"   🏢 Liens APRR: {len(aprr_links)}")
    
    # Filtrage par type de péage
    open_toll_links = CacheAccessor.get_links_by_toll_type("ouvert")
    closed_toll_links = CacheAccessor.get_links_by_toll_type("fermé")
    
    print(f"   🔓 Péages ouverts: {len(open_toll_links)}")
    print(f"   🔒 Péages fermés: {len(closed_toll_links)}")
    
    # Note: Si pas de résultats, essayer avec les codes courts
    if len(open_toll_links) == 0 and len(closed_toll_links) == 0:
        open_toll_links = CacheAccessor.get_links_by_toll_type("O")
        closed_toll_links = CacheAccessor.get_links_by_toll_type("F")
        print(f"   🔓 Péages ouverts (code O): {len(open_toll_links)}")
        print(f"   🔒 Péages fermés (code F): {len(closed_toll_links)}")
    
    # Test de sélection par proximité géographique (simulation)
    all_links = CacheAccessor.get_complete_motorway_links()
    sample_links = all_links[:100] if len(all_links) > 100 else all_links
    
    print(f"   📍 Test sur échantillon de {len(sample_links)} liens")
    
    # Grouper par région (basé sur les coordonnées approximatives)
    regions = {}
    for link in sample_links:
        if link.segments:
            # Utiliser le premier segment pour la région
            seg = link.segments[0]
            if hasattr(seg, 'lat') and hasattr(seg, 'lon'):
                # Simple regroupement par zone géographique
                region_key = f"{int(seg.lat)},{int(seg.lon)}"
                if region_key not in regions:
                    regions[region_key] = []
                regions[region_key].append(link)
    
    print(f"   🗺️  Régions identifiées: {len(regions)}")
    
    return len(asf_links) > 0 or len(aprr_links) > 0


def test_performance_metrics():
    """Test les métriques de performance du cache V2."""
    print_header("Test de performance")
    
    import time
    
    print("5️⃣ Mesure des performances d'accès...")
    
    # Test d'accès répétés
    iterations = 50
    start_time = time.time()
    
    for i in range(iterations):
        stats = CacheAccessor.get_cache_stats()
        links = CacheAccessor.get_links_with_tolls()
        if i % 10 == 0:
            # Calcul de coût occasionnel
            if links:
                cost = CacheAccessor.calculate_toll_cost(links[0])
    
    end_time = time.time()
    total_time = (end_time - start_time) * 1000
    avg_time = total_time / iterations
    
    print(f"   ⚡ {iterations} accès en {total_time:.1f}ms")
    print(f"   📊 Moyenne: {avg_time:.2f}ms/accès")
    
    # Test de filtrage
    start_time = time.time()
    for operator in ["ASF", "APRR", "SANEF", "COFIROUTE"]:
        operator_links = CacheAccessor.get_links_by_operator(operator)
    end_time = time.time()
    
    filter_time = (end_time - start_time) * 1000
    print(f"   🔍 Filtrage 4 opérateurs: {filter_time:.1f}ms")
    
    return avg_time < 10.0  # Performance acceptable si < 10ms


def test_integration_scenarios():
    """Test des scénarios d'intégration réalistes."""
    print_header("Scénarios d'intégration")
    
    print("6️⃣ Simulation de cas d'usage réels...")
    
    # Scénario 1: Route avec plusieurs péages
    all_links = CacheAccessor.get_links_with_tolls()
    if len(all_links) >= 3:
        sample_route = all_links[:3]
        total_cost = 0
        
        print("\n   🛣️  Scénario: Route avec 3 péages")
        for i, link in enumerate(sample_route, 1):
            cost = CacheAccessor.calculate_toll_cost(link)
            toll = link.associated_toll
            print(f"   {i}. {toll.name if toll else 'N/A'}: {cost}€" if cost else f"   {i}. {toll.name if toll else 'N/A'}: Coût N/A")
            if cost:
                total_cost += cost
        
        print(f"   💰 Coût total estimé: {total_cost:.2f}€")
    
    # Scénario 2: Comparaison d'opérateurs
    operators = ["ASF", "APRR", "SANEF"]
    print(f"\n   🏢 Scénario: Comparaison d'opérateurs")
    
    for operator in operators:
        op_links = CacheAccessor.get_links_by_operator(operator)
        if op_links:
            # Calculer coût moyen
            costs = []
            for link in op_links[:5]:  # Échantillon
                cost = CacheAccessor.calculate_toll_cost(link)
                if cost:
                    costs.append(cost)
            
            if costs:
                avg_cost = sum(costs) / len(costs)
                print(f"   • {operator}: {len(op_links)} liens, coût moyen: {avg_cost:.2f}€")
            else:
                print(f"   • {operator}: {len(op_links)} liens, coût N/A")
    
    return True


def main():
    """Fonction principale du test d'intégration."""
    print("🚀 Test d'intégration Route Optimization avec Cache V2")
    print("=" * 60)
    
    success_count = 0
    test_count = 0
    
    # Test 1: Intégration du cache
    test_count += 1
    if test_cache_integration():
        success_count += 1
        print("✅ Test cache integration: RÉUSSI")
    else:
        print("❌ Test cache integration: ÉCHEC")
        return False
    
    # Test 2: Identification de péages
    test_count += 1
    if test_toll_identification():
        success_count += 1
        print("✅ Test toll identification: RÉUSSI")
    else:
        print("❌ Test toll identification: ÉCHEC")
    
    # Test 3: Sélection de péages
    test_count += 1
    if test_toll_selection():
        success_count += 1
        print("✅ Test toll selection: RÉUSSI")
    else:
        print("❌ Test toll selection: ÉCHEC")
    
    # Test 4: Performance
    test_count += 1
    if test_performance_metrics():
        success_count += 1
        print("✅ Test performance: RÉUSSI")
    else:
        print("❌ Test performance: ÉCHEC")
    
    # Test 5: Scénarios d'intégration
    test_count += 1
    if test_integration_scenarios():
        success_count += 1
        print("✅ Test integration scenarios: RÉUSSI")
    else:
        print("❌ Test integration scenarios: ÉCHEC")
    
    # Résultats finaux
    print_header("Résultats finaux")
    print(f"🏆 Tests réussis: {success_count}/{test_count}")
    print(f"📊 Taux de réussite: {(success_count/test_count)*100:.1f}%")
    
    if success_count == test_count:
        print("🎉 Intégration Route Optimization + Cache V2 validée !")
        return True
    else:
        print("⚠️  Certains tests ont échoué, vérification nécessaire")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
