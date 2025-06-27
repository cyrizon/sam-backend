"""
Report Generator Utilities
-------------------------

Utilities for generating OSM/CSV matching reports.
Moved from osm_csv_match_reporter.py
"""

import json
from typing import List, Dict, Optional


def write_osm_csv_match_report(
    toll_stations: List,
    matched_path: str = "osm_csv_toll_matched.json",
    unmatched_path: str = "osm_csv_toll_unmatched.json"
) -> None:
    """
    Génère deux rapports JSON :
    - matched_path : péages OSM matchés avec le CSV
    - unmatched_path : péages OSM non matchés
    
    Args:
        toll_stations: Liste d'objets TollStation (ou dict équivalent)
        matched_path: Chemin du fichier de sortie pour les matchés
        unmatched_path: Chemin du fichier de sortie pour les non matchés
    """
    matched = []
    unmatched = []
    
    for toll in toll_stations:
        entry = {
            "osm_id": getattr(toll, "feature_id", None),
            "osm_name": getattr(toll, "name", None),
            "osm_coordinates": getattr(toll, "coordinates", None),
            "csv_id": None,
            "csv_name": None,
            "csv_role": None,
            "csv_coordinates": None,
            "distance_m": None
        }
        
        csv_match = getattr(toll, "csv_match", None)
        if csv_match:
            entry["csv_id"] = csv_match.get("id")
            entry["csv_name"] = csv_match.get("name")
            entry["csv_role"] = csv_match.get("role")
            entry["csv_coordinates"] = csv_match.get("coordinates")
            entry["distance_m"] = csv_match.get("distance_m")
            matched.append(entry)
        else:
            unmatched.append(entry)
    
    with open(matched_path, "w", encoding="utf-8") as f:
        json.dump(matched, f, ensure_ascii=False, indent=2)
    
    with open(unmatched_path, "w", encoding="utf-8") as f:
        json.dump(unmatched, f, ensure_ascii=False, indent=2)
    
    print(f"📝 Rapport OSM/CSV : {len(matched)} matchés → {matched_path}, "
          f"{len(unmatched)} non-matchés → {unmatched_path}")
