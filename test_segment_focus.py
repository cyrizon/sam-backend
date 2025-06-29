#!/usr/bin/env python3
"""
Test ciblé pour analyser uniquement le segment way/657897788
"""
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cache.v2.managers.osm_data_manager_v2 import OSMDataManagerV2

def analyze_specific_segment():
    """Analyse spécifique du segment way/657897788"""
    
    target_segment = "way/657897788"
    print(f"🎯 ANALYSE CIBLÉE DU SEGMENT: {target_segment}")
    print("=" * 60)
    
    # Configuration des sources de données
    data_sources = {
        'toll_booths': 'data/osm/toll_booths.geojson',
        'entries': 'data/osm/motorway_entries.geojson', 
        'exits': 'data/osm/motorway_exits.geojson',
        'indeterminate': 'data/osm/motorway_indeterminate.geojson'
    }
    
    print("📂 Initialisation du gestionnaire...")
    manager = OSMDataManagerV2(cache_dir="osm_cache_v2_test")
    
    # Utiliser le cache existant (pas de force_rebuild)
    success = manager.initialize(data_sources, force_rebuild=False)
    
    if not success:
        print("❌ Échec de l'initialisation")
        return
    
    print("✅ Gestionnaire initialisé avec succès")
    print()
    
    # Accéder aux données parsées correctement
    print("🔍 ÉTAPE 1: Recherche dans les données parsées")
    print("-" * 40)
    
    if hasattr(manager, '_data') and manager._data and hasattr(manager._data, 'parsed_data'):
        parsed_data = manager._data.parsed_data
        print(f"   ✅ Données parsées trouvées")
        print(f"   📋 Type: {type(parsed_data)}")
        
        # Rechercher le segment dans les données
        found_segment = False
        segment_info = {}
        
        # Vérifier dans toll_booths
        if hasattr(parsed_data, 'toll_booths'):
            print(f"   🏪 Toll booths: {len(parsed_data.toll_booths)}")
        
        # Vérifier dans entry_links
        if hasattr(parsed_data, 'entry_links'):
            print(f"   🛣️ Entry links: {len(parsed_data.entry_links)}")
            for link in parsed_data.entry_links:
                if hasattr(link, 'osm_id') and link.osm_id == target_segment:
                    print(f"   ✅ TROUVÉ dans entry_links!")
                    print(f"      • OSM ID: {link.osm_id}")
                    print(f"      • Type: {link.link_type}")
                    print(f"      • Coordinates: {len(link.coordinates)} points")
                    print(f"      • Start point: {link.start_point}")
                    print(f"      • End point: {link.end_point}")
                    found_segment = True
                    segment_info = {
                        'type': 'entry',
                        'link': link,
                        'start_point': link.start_point,
                        'end_point': link.end_point
                    }
                    break
        
        # Vérifier dans exit_links
        if hasattr(parsed_data, 'exit_links') and not found_segment:
            print(f"   🛣️ Exit links: {len(parsed_data.exit_links)}")
            for link in parsed_data.exit_links:
                if hasattr(link, 'osm_id') and link.osm_id == target_segment:
                    print(f"   ✅ TROUVÉ dans exit_links!")
                    print(f"      • OSM ID: {link.osm_id}")
                    print(f"      • Type: {link.link_type}")
                    print(f"      • Coordinates: {len(link.coordinates)} points")
                    print(f"      • Start point: {link.start_point}")
                    print(f"      • End point: {link.end_point}")
                    found_segment = True
                    segment_info = {
                        'type': 'exit',
                        'link': link,
                        'start_point': link.start_point,
                        'end_point': link.end_point
                    }
                    break
        
        # Vérifier dans indeterminate_links
        if hasattr(parsed_data, 'indeterminate_links') and not found_segment:
            print(f"   🛣️ Indeterminate links: {len(parsed_data.indeterminate_links)}")
            for link in parsed_data.indeterminate_links:
                if hasattr(link, 'osm_id') and link.osm_id == target_segment:
                    print(f"   ✅ TROUVÉ dans indeterminate_links!")
                    print(f"      • OSM ID: {link.osm_id}")
                    print(f"      • Type: {link.link_type}")
                    print(f"      • Coordinates: {len(link.coordinates)} points")
                    print(f"      • Start point: {link.start_point}")
                    print(f"      • End point: {link.end_point}")
                    found_segment = True
                    segment_info = {
                        'type': 'indeterminate',
                        'link': link,
                        'start_point': link.start_point,
                        'end_point': link.end_point
                    }
                    break
        
        if not found_segment:
            print(f"   ❌ Segment {target_segment} non trouvé dans les données parsées")
            return
        
    else:
        print("   ❌ Impossible d'accéder aux données parsées")
        return
    
    print()
    
    # Recherche dans les résultats de liaison
    print("🔗 ÉTAPE 2: Recherche dans les résultats de liaison")
    print("-" * 40)
    
    if hasattr(manager, '_data') and manager._data and hasattr(manager._data, 'linking_result'):
        linking_result = manager._data.linking_result
        print(f"   ✅ Résultats de liaison trouvés")
        print(f"   📋 Type: {type(linking_result)}")
        
        # Rechercher dans les liens complets
        found_in_complete = False
        complete_link_info = {}
        
        if hasattr(linking_result, 'complete_entry_links'):
            print(f"   🔗 Complete entry links: {len(linking_result.complete_entry_links)}")
            for complete_link in linking_result.complete_entry_links:
                if hasattr(complete_link, 'all_segment_ids') and target_segment in complete_link.all_segment_ids:
                    print(f"   ✅ TROUVÉ dans complete_entry_links!")
                    print(f"      • ID principal: {complete_link.main_link_id}")
                    print(f"      • Nombre de liens chainés: {len(complete_link.links)}")
                    print(f"      • Longueur totale: {complete_link.total_length:.2f}m")
                    print(f"      • Position du segment: {complete_link.all_segment_ids.index(target_segment)}")
                    print(f"      • Séquence complète: {complete_link.all_segment_ids}")
                    
                    # Vérifier la séquence recherchée
                    expected_sequence = ["way/657897788", "way/126357480", "way/1298540619", "way/1298540620"]
                    sequence_found = all(seg in complete_link.all_segment_ids for seg in expected_sequence)
                    print(f"      • Séquence complète présente: {'✅ OUI' if sequence_found else '❌ NON'}")
                    
                    if sequence_found:
                        print(f"      • Positions dans la séquence:")
                        for seg in expected_sequence:
                            try:
                                pos = complete_link.all_segment_ids.index(seg)
                                print(f"         - {seg}: position {pos}")
                            except ValueError:
                                print(f"         - {seg}: NON TROUVÉ")
                    
                    complete_link_info = {
                        'type': 'entry',
                        'complete_link': complete_link,
                        'position': complete_link.all_segment_ids.index(target_segment)
                    }
                    found_in_complete = True
                    break
        
        if hasattr(linking_result, 'complete_exit_links') and not found_in_complete:
            print(f"   🔗 Complete exit links: {len(linking_result.complete_exit_links)}")
            for complete_link in linking_result.complete_exit_links:
                if hasattr(complete_link, 'all_segment_ids') and target_segment in complete_link.all_segment_ids:
                    print(f"   ✅ TROUVÉ dans complete_exit_links!")
                    print(f"      • ID principal: {complete_link.main_link_id}")
                    print(f"      • Nombre de liens chainés: {len(complete_link.links)}")
                    print(f"      • Longueur totale: {complete_link.total_length:.2f}m")
                    print(f"      • Position du segment: {complete_link.all_segment_ids.index(target_segment)}")
                    print(f"      • Séquence complète: {complete_link.all_segment_ids}")
                    
                    # Vérifier la séquence recherchée
                    expected_sequence = ["way/657897788", "way/126357480", "way/1298540619", "way/1298540620"]
                    sequence_found = all(seg in complete_link.all_segment_ids for seg in expected_sequence)
                    print(f"      • Séquence complète présente: {'✅ OUI' if sequence_found else '❌ NON'}")
                    
                    if sequence_found:
                        print(f"      • Positions dans la séquence:")
                        for seg in expected_sequence:
                            try:
                                pos = complete_link.all_segment_ids.index(seg)
                                print(f"         - {seg}: position {pos}")
                            except ValueError:
                                print(f"         - {seg}: NON TROUVÉ")
                    
                    complete_link_info = {
                        'type': 'exit',
                        'complete_link': complete_link,
                        'position': complete_link.all_segment_ids.index(target_segment)
                    }
                    found_in_complete = True
                    break
        
        if not found_in_complete:
            print(f"   ❌ Segment {target_segment} non trouvé dans les liens complets")
            # Le segment existe mais n'a pas été lié - vérifier pourquoi
            print(f"   💡 Le segment existe dans les données parsées ({segment_info['type']}) mais n'a pas été lié")
            print(f"   🔍 Raisons possibles:")
            print(f"      • Distance > 2m avec les segments voisins")
            print(f"      • Problème dans l'algorithme de chaînage")
            print(f"      • Segment isolé géographiquement")
        
    else:
        print("   ❌ Impossible d'accéder aux résultats de liaison")
    
    print()
    
    # Recherche dans les associations de péages
    print("🛣️ ÉTAPE 3: Recherche dans les associations de péages")
    print("-" * 40)
    
    if hasattr(manager, '_data') and manager._data and hasattr(manager._data, 'toll_detection_result'):
        toll_result = manager._data.toll_detection_result
        print(f"   ✅ Résultats de détection de péages trouvés")
        print(f"   📋 Type: {type(toll_result)}")
        
        # Rechercher dans les associations
        if hasattr(toll_result, 'toll_associations'):
            associations = toll_result.toll_associations
            print(f"   🏪 Associations de péages: {len(associations)}")
            
            found_in_tolls = False
            for toll_id, toll_info in associations.items():
                complete_link = toll_info['complete_link']
                if hasattr(complete_link, 'all_segment_ids') and target_segment in complete_link.all_segment_ids:
                    toll_station = toll_info['toll_station']
                    print(f"   ✅ TROUVÉ associé à un péage!")
                    print(f"      • Péage ID: {toll_id}")
                    print(f"      • Nom du péage: {toll_station.name}")
                    print(f"      • Distance au péage: {toll_info['distance']:.2f}m")
                    print(f"      • Coordonnées péage: {toll_station.coordinates}")
                    print(f"      • Lien complet: {complete_link.main_link_id}")
                    print(f"      • Position du segment: {complete_link.all_segment_ids.index(target_segment)}")
                    print(f"      • Séquence complète: {complete_link.all_segment_ids}")
                    found_in_tolls = True
                    break
            
            if not found_in_tolls:
                if found_in_complete:
                    print(f"   💡 Segment trouvé dans un lien complet mais pas associé à un péage")
                    print(f"   🔍 Le lien complet n'a pas de péage à proximité (seuil: 2m)")
                else:
                    print(f"   ❌ Segment non associé à un péage (pas de lien complet)")
        
    else:
        print("   ❌ Impossible d'accéder aux associations de péages")
    
    print()
    
    # Résumé final
    print("📋 RÉSUMÉ FINAL")
    print("-" * 40)
    print(f"Segment analysé: {target_segment}")
    if found_segment:
        print(f"• Type de données parsées: {segment_info['type']}")
        print(f"• Point de départ: {segment_info['start_point']}")
        print(f"• Point d'arrivée: {segment_info['end_point']}")
    
    print(f"• Présent dans les données parsées: {'✅ OUI' if found_segment else '❌ NON'}")
    print(f"• Présent dans les liens complets: {'✅ OUI' if found_in_complete else '❌ NON'}")
    print(f"• Associé à un péage: {'✅ OUI' if found_in_tolls else '❌ NON'}")
