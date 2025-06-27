#!/usr/bin/env python3
"""
Test de la détection des péages fermés vs ouverts
"""

from src.services.toll.new_segmentation.hybrid_strategy.tollways_analyzer import TollwaysAnalyzer
from src.cache.models.matched_toll import MatchedToll

def test_closed_system_detection():
    """Test de la détection des systèmes fermés vs ouverts."""
    analyzer = TollwaysAnalyzer()
    
    # Créer des péages test avec différents csv_role
    peages_test = [
        # Péage fermé
        MatchedToll(
            osm_id="way/123",
            osm_name="Saint-Maurice",
            osm_coordinates=[2.4, 48.8],
            csv_id="SM01",
            csv_name="Saint-Maurice",
            csv_role="F",  # Fermé
            csv_coordinates=[2.4, 48.8],
            distance_m=50.0,
            confidence=0.9
        ),
        # Péage ouvert
        MatchedToll(
            osm_id="way/456",
            osm_name="Roissy",
            osm_coordinates=[2.5, 48.9],
            csv_id="RO01",
            csv_name="Roissy",
            csv_role="O",  # Ouvert
            csv_coordinates=[2.5, 48.9],
            distance_m=30.0,
            confidence=0.95
        ),
        # Péage sans csv_role (fallback)
        MatchedToll(
            osm_id="way/789",
            osm_name="Péage Inconnu",
            osm_coordinates=[2.6, 49.0],
            csv_id=None,
            csv_name=None,
            csv_role=None,  # Pas de role
            csv_coordinates=None,
            distance_m=0.0,
            confidence=0.0
        )
    ]
    
    print("🧪 Test de détection des systèmes fermés/ouverts :")
    print("=" * 60)
    
    for peage in peages_test:
        is_closed = analyzer._is_closed_system_toll(peage)
        system_type = "FERMÉ" if is_closed else "OUVERT"
        role = peage.csv_role or "N/A"
        
        print(f"📍 {peage.effective_name}")
        print(f"   csv_role: {role}")
        print(f"   Détecté comme: {system_type}")
        print(f"   is_open_system: {peage.is_open_system}")
        print()
    
    # Test avec faux segments gratuits
    print("🕵️ Test détection faux segments gratuits :")
    print("=" * 60)
    
    # Ajouter un deuxième péage fermé pour le test
    peage_ferme_2 = MatchedToll(
        osm_id="way/999",
        osm_name="Senlis",
        osm_coordinates=[2.7, 49.1],
        csv_id="SE01",
        csv_name="Senlis",
        csv_role="F",  # Fermé aussi
        csv_coordinates=[2.7, 49.1],
        distance_m=40.0,
        confidence=0.85
    )
    
    # Simulation d'une analyse de segments avec deux péages fermés
    analysis = {
        'segments_with_tolls': [
            {
                'segment_index': 0,
                'tolls': [peages_test[0]]  # Péage fermé Saint-Maurice
            },
            {
                'segment_index': 2,
                'tolls': [peage_ferme_2]  # Péage fermé Senlis
            }
        ],
        'free_segments': [
            {
                'segment_index': 1  # Segment gratuit entre les deux péages fermés
            }
        ]
    }
    
    print("Configuration test :")
    print(f"   Segment 0: {peages_test[0].effective_name} (FERMÉ)")
    print(f"   Segment 1: GRATUIT")
    print(f"   Segment 2: {peage_ferme_2.effective_name} (FERMÉ)")
    print()
    
    fake_segments = analyzer._detect_fake_free_segments(analysis, peages_test)
    
    print(f"Segments faux gratuits détectés : {len(fake_segments)}")
    for fake in fake_segments:
        print(f"   ⚠️ Segment gratuit index {fake['segment']['segment_index']}")
        print(f"      Entre {fake['peage_before'].effective_name} et {fake['peage_after'].effective_name}")

if __name__ == "__main__":
    test_closed_system_detection()
