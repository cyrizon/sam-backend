"""
Test de déduplication des péages
==============================

Test spécifique pour valider la logique de déduplication basée sur la proximité
et la similarité sémantique.
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from src.services.toll.route_optimization.toll_analysis.core_identifier import CoreTollIdentifier


class MockToll:
    """Mock toll pour les tests."""
    
    def __init__(self, osm_id, nom, operator, autoroute, lat, lon, is_open_toll=False):
        self.osm_id = osm_id
        self.nom = nom
        self.operator = operator
        self.autoroute = autoroute
        self.latitude = lat
        self.longitude = lon
        self.is_open_toll = is_open_toll
    
    def get_coordinates(self):
        return [self.longitude, self.latitude]


def test_toll_deduplication():
    """Test de déduplication des péages."""
    print("🧪 Test de déduplication des péages")
    
    identifier = CoreTollIdentifier()
    
    # Créer des péages de test avec des doublons
    toll1 = MockToll(
        osm_id=123456,
        nom="Péage de Paris",
        operator="APRR",
        autoroute="A6",
        lat=48.8566,
        lon=2.3522,
        is_open_toll=False
    )
    
    # Doublon très proche (même lieu physique)
    toll2 = MockToll(
        osm_id=123457,
        nom="Péage de Paris",
        operator="APRR", 
        autoroute="A6",
        lat=48.8566001,  # Différence de ~0.1m
        lon=2.3522001,
        is_open_toll=False
    )
    
    # Péage différent (plus loin)
    toll3 = MockToll(
        osm_id=123458,
        nom="Péage de Lyon",
        operator="APRR",
        autoroute="A6",
        lat=48.8570,  # Différence de ~400m
        lon=2.3530,
        is_open_toll=False
    )
    
    # Créer des données de péages formatées
    toll_data_list = [
        {
            'toll': toll1,
            'coordinates': toll1.get_coordinates(),
            'min_distance_m': 10.0,
            'is_on_route': True,
            'toll_type': 'fermé',
            'operator': 'APRR'
        },
        {
            'toll': toll2,
            'coordinates': toll2.get_coordinates(),
            'min_distance_m': 12.0,
            'is_on_route': True,
            'toll_type': 'fermé',
            'operator': 'APRR'
        },
        {
            'toll': toll3,
            'coordinates': toll3.get_coordinates(),
            'min_distance_m': 15.0,
            'is_on_route': True,
            'toll_type': 'fermé',
            'operator': 'APRR'
        }
    ]
    
    print(f"📊 Péages avant déduplication : {len(toll_data_list)}")
    
    # Test de déduplication
    deduplicated = identifier._deduplicate_toll_list(toll_data_list)
    
    print(f"📊 Péages après déduplication : {len(deduplicated)}")
    
    # Vérifications
    assert len(deduplicated) == 2, f"Attendu 2 péages, obtenu {len(deduplicated)}"
    
    # Vérifier que le meilleur candidat a été conservé (distance minimale)
    paris_tolls = [t for t in deduplicated if "Paris" in t['toll'].nom]
    assert len(paris_tolls) == 1, "Un seul péage de Paris devrait rester"
    assert paris_tolls[0]['min_distance_m'] == 10.0, "Le péage avec la distance minimale devrait être conservé"
    
    print("✅ Test de déduplication réussi")


def test_distance_calculation():
    """Test du calcul de distance entre points."""
    print("\n🧪 Test de calcul de distance")
    
    identifier = CoreTollIdentifier()
    
    # Points très proches (même lieu)
    coords1 = [2.3522, 48.8566]
    coords2 = [2.3522001, 48.8566001]
    
    distance = identifier._calculate_distance_between_points(coords1, coords2)
    print(f"📏 Distance entre points très proches : {distance:.2f}m")
    
    assert distance < 1.0, f"Distance attendue < 1m, obtenue {distance:.2f}m"
    
    # Points plus éloignés
    coords3 = [2.3530, 48.8570]
    distance2 = identifier._calculate_distance_between_points(coords1, coords3)
    print(f"📏 Distance entre points éloignés : {distance2:.2f}m")
    
    assert distance2 > 1.0, f"Distance attendue > 1m, obtenue {distance2:.2f}m"
    
    print("✅ Test de calcul de distance réussi")


def test_semantic_similarity():
    """Test de similarité sémantique."""
    print("\n🧪 Test de similarité sémantique")
    
    identifier = CoreTollIdentifier()
    
    # Péages similaires
    toll1 = MockToll(123456, "Péage de Paris", "APRR", "A6", 48.8566, 2.3522)
    toll2 = MockToll(123457, "Péage de Paris", "APRR", "A6", 48.8566, 2.3522)
    
    similar = identifier._are_semantically_similar(toll1, toll2)
    assert similar, "Les péages identiques devraient être similaires"
    
    # Péages différents (opérateurs différents)
    toll3 = MockToll(123458, "Péage de Paris", "SANEF", "A6", 48.8566, 2.3522)
    not_similar = identifier._are_semantically_similar(toll1, toll3)
    assert not not_similar, "Les péages avec opérateurs différents ne devraient pas être similaires"
    
    # Péages différents (autoroutes différentes)
    toll4 = MockToll(123459, "Péage de Paris", "APRR", "A1", 48.8566, 2.3522)
    not_similar2 = identifier._are_semantically_similar(toll1, toll4)
    assert not not_similar2, "Les péages sur autoroutes différentes ne devraient pas être similaires"
    
    print("✅ Test de similarité sémantique réussi")


def test_best_candidate_selection():
    """Test de sélection du meilleur candidat."""
    print("\n🧪 Test de sélection du meilleur candidat")
    
    identifier = CoreTollIdentifier()
    
    # Candidats avec différentes distances et complétudes
    toll1 = MockToll(123456, "Péage", "APRR", "A6", 48.8566, 2.3522)
    toll2 = MockToll(123457, "Péage de Paris Centre", "APRR", "A6", 48.8566, 2.3522)
    toll3 = MockToll(123458, "", "", "", 48.8566, 2.3522)
    
    candidates = [
        {
            'toll': toll1,
            'coordinates': toll1.get_coordinates(),
            'min_distance_m': 15.0,
            'is_on_route': True,
            'toll_type': 'fermé',
            'operator': 'APRR'
        },
        {
            'toll': toll2,
            'coordinates': toll2.get_coordinates(),
            'min_distance_m': 10.0,  # Distance plus faible
            'is_on_route': True,
            'toll_type': 'fermé',
            'operator': 'APRR'
        },
        {
            'toll': toll3,
            'coordinates': toll3.get_coordinates(),
            'min_distance_m': 8.0,  # Distance encore plus faible mais infos incomplètes
            'is_on_route': True,
            'toll_type': 'fermé',
            'operator': 'Inconnu'
        }
    ]
    
    best = identifier._select_best_toll_candidate(candidates)
    
    # Le candidat avec la distance minimale devrait être sélectionné
    assert best['min_distance_m'] == 8.0, "Le candidat avec la distance minimale devrait être sélectionné"
    assert best['toll'].osm_id == 123458, "Le bon candidat devrait être sélectionné"
    
    print("✅ Test de sélection du meilleur candidat réussi")


if __name__ == "__main__":
    print("🚀 Démarrage des tests de déduplication des péages\n")
    
    try:
        test_distance_calculation()
        test_semantic_similarity()
        test_best_candidate_selection()
        test_toll_deduplication()
        
        print("\n🎉 Tous les tests de déduplication ont réussi !")
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests : {e}")
        import traceback
        traceback.print_exc()
