"""
toll_locator.py
---------------

Détecte les gares de péage croisées par une géométrie GeoJSON renvoyée
par OpenRouteService.  Inspiré du module `tolls_finder.py`, mais
optimisé : STRtree + reprojection unique + ordre le long de l’axe.

© SAM PEAGE ET COUT 2025
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict

import pandas as pd
from shapely.geometry import Point, LineString
from shapely.strtree import STRtree
from pyproj import Transformer
import unicodedata
from flask import current_app

# ────────────────────────────────────────────────────────────────────────────
# Préparation des données (barriers.csv)
# ────────────────────────────────────────────────────────────────────────────
_WGS84 = "EPSG:4326"
_SRC  = "EPSG:2154"
_WEBM = "EPSG:3857"

def _load_barriers(csv_path: Path | str):
    df = pd.read_csv(csv_path)
    # Colonnes x, y WGS84 (déjà converties par build_toll_datasets.py)
    l93_to_3857 = Transformer.from_crs(_SRC, _WEBM, always_xy=True).transform
    df["_geom3857"] = [Point(*l93_to_3857(x, y)) for x, y in zip(df["x"], df["y"])]
    return df

# Chargement unique au premier import :
_BARRIERS_DF = None
_BARRIERS_TREE = None
def _ensure_barriers(csv_path):
    global _BARRIERS_DF, _BARRIERS_TREE
    if _BARRIERS_DF is None:
        _BARRIERS_DF = _load_barriers(csv_path)
        _BARRIERS_TREE = STRtree(_BARRIERS_DF["_geom3857"].tolist())

# ────────────────────────────────────────────────────────────────────────────
# Utilisation du cache global (VERSION OPTIMISÉE)
# ────────────────────────────────────────────────────────────────────────────

def _get_barriers_from_cache():
    """Récupère les barrières depuis le cache global"""
    from src.cache import toll_data_cache
    return toll_data_cache.barriers_df, toll_data_cache.spatial_index

def _normalize_name(name):
    # Normalisation simple pour le fallback par nom
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    return name.replace('-', ' ').replace('_', ' ').strip()

# ────────────────────────────────────────────────────────────────────────────
# Fonction publique
# ────────────────────────────────────────────────────────────────────────────
def locate_tolls(
    ors_geojson: dict,
    buffer_m: float = 1.0,  # <1m strict
    veh_class: str = None,  # Optionnel : si fourni, ajoute le coût
) -> Dict[str, List[Dict]]:
    """
    Renvoie la liste ordonnée des péages OSM croisés par la route (distance point-segment <1m).
    Fallback par nom si aucun péage détecté par coordonnées.
    Enrichit chaque péage avec csv_id et csv_role si possible (pour calcul coût).
    Si veh_class est fourni, ajoute le champ cost à chaque péage.
    """
    from shapely.geometry import shape
    # 1) Géométrie ORS → LineString WGS84
    route_line = shape(ors_geojson["features"][0]["geometry"])
    # 2) Charger les péages OSM depuis le cache global (déjà initialisé)
    from src.cache import osm_data_cache
    tolls = osm_data_cache.toll_stations
    # 3) Calculer la distance point-segment pour chaque péage
    detected = []
    for toll in tolls:
        # Supporte TollStation (objet) ou dict
        if hasattr(toll, "coordinates"):
            lon, lat = toll.coordinates
            name = getattr(toll, "name", "")
            role = getattr(toll, "toll_type", getattr(toll, "role", ""))
            id_ = getattr(toll, "feature_id", getattr(toll, "id", "osm"))
            # --- Enrichissement OSM→CSV ---
            csv_id = None
            csv_role = None
            if hasattr(toll, "csv_match") and toll.csv_match:
                csv_id = toll.csv_match.get("id")
                csv_role = toll.csv_match.get("role")
            else:
                csv_id = getattr(toll, "csv_id", None)
                csv_role = getattr(toll, "csv_role", None)
        else:
            lon = toll.get("lon")
            lat = toll.get("lat")
            name = toll.get("name", "")
            role = toll.get("role", "")
            id_ = toll.get("id", "osm")
            csv_id = toll.get("csv_id")
            csv_role = toll.get("csv_role")
        pt = Point(lon, lat)
        dist = route_line.distance(pt)
        if dist < buffer_m / 111139:  # 1m en degrés approx.
            toll_dict = {
                "id": id_,
                "longitude": lon,
                "latitude": lat,
                "name": name,
                "role": role,
                "csv_id": csv_id,
                "csv_role": csv_role,
                "distance": dist * 111139
            }
            print(f"[TOLL DEBUG] {toll_dict}")
            detected.append(toll_dict)
    # 4) Fallback par nom si aucun péage détecté
    if not detected:
        route_names = set()
        for toll in tolls:
            if hasattr(toll, "name"):
                route_names.add(_normalize_name(getattr(toll, "name", "")))
            elif isinstance(toll, dict) and "name" in toll:
                route_names.add(_normalize_name(toll["name"]))
        for toll in tolls:
            if hasattr(toll, "name"):
                name = getattr(toll, "name", "")
                lon, lat = toll.coordinates
                role = getattr(toll, "toll_type", getattr(toll, "role", ""))
                id_ = getattr(toll, "feature_id", getattr(toll, "id", "osm"))
                csv_id = getattr(toll, "csv_id", None)
                csv_role = getattr(toll, "csv_role", None)
                if _normalize_name(name) in route_names:
                    detected.append({
                        "id": id_,
                        "longitude": lon,
                        "latitude": lat,
                        "name": name,
                        "role": role,
                        "csv_id": csv_id,
                        "csv_role": csv_role,
                        "distance": None
                    })
            elif isinstance(toll, dict):
                name = toll.get("name", "")
                lon = toll.get("lon")
                lat = toll.get("lat")
                role = toll.get("role", "")
                id_ = toll.get("id", "osm")
                csv_id = toll.get("csv_id")
                csv_role = toll.get("csv_role")
                if _normalize_name(name) in route_names:
                    detected.append({
                        "id": id_,
                        "longitude": lon,
                        "latitude": lat,
                        "name": name,
                        "role": role,
                        "csv_id": csv_id,
                        "csv_role": csv_role,
                        "distance": None
                    })
    # 5) Tri par avancement sur la route
    def project(toll):
        pt = Point(toll["longitude"], toll["latitude"])
        return route_line.project(pt)
    detected = sorted(detected, key=project)
    # 6) Ajout du coût si demandé
    if veh_class:
        from src.services.toll_cost import add_marginal_cost
        detected = add_marginal_cost(detected, veh_class)
    
    # Déduplication par csv_id (ou id si pas de csv_id)
    unique = {}
    for toll in detected:
        key = toll["csv_id"] if toll["csv_id"] else toll["id"]
        if key not in unique:
            # Met à jour le champ role avec csv_role si présent
            toll["role"] = toll["csv_role"] if toll["csv_role"] else toll["role"]
            unique[key] = toll
    detected = list(unique.values())
    
    print(
        [{"id": t["id"], "name": t["name"], "cost": t.get("cost")} for t in detected]
    )
    return {"on_route": detected, "nearby": []}

def get_all_open_tolls_by_proximity(
    ors_geojson: dict,
    csv_path: str | Path = "data/barriers.csv",
    max_distance_m: float = 100000,  # 100 km par défaut
) -> List[Dict]:
    """
    Renvoie tous les péages à système ouvert, triés par proximité avec l'itinéraire.
    Utilise la distance minimale du péage à la ligne de l'itinéraire pour déterminer sa proximité.
    
    Args:
        ors_geojson: Géométrie de l'itinéraire au format GeoJSON
        csv_path: Chemin vers le fichier CSV des barrières de péage
        max_distance_m: Distance maximale (en mètres) entre le péage et l'itinéraire
        
    Returns:
        List[Dict]: Liste des péages ouverts triés par proximité, à moins de max_distance_m mètres
    """
    from shapely.geometry import shape  # import léger
    import re    # Charger les données de péages - VERSION OPTIMISÉE avec cache global
    barriers_df, barriers_tree = _get_barriers_from_cache()
    
    # 1) Géométrie ORS → LineString WGS84
    route_line = shape(ors_geojson["features"][0]["geometry"])
    
    # 2) Convertir en Web Mercator pour le calcul de distance
    wgs_to_3857 = Transformer.from_crs(_WGS84, _WEBM, always_xy=True).transform
    route_3857 = LineString([wgs_to_3857(*coord) for coord in route_line.coords])
      # 3) Filtrer tous les péages à système ouvert (à partir du nom)
    # On utilise le critère "_o" dans l'ID pour identifier les systèmes ouverts
    open_toll_mask = barriers_df['id'].str.contains('_o', case=False, regex=True)
    open_tolls_df = barriers_df[open_toll_mask].copy()
    
    if len(open_tolls_df) == 0:
        return []
    
    # 4) Calcul des distances à l'itinéraire
    open_tolls_df['distance_to_route'] = open_tolls_df['_geom3857'].apply(
        lambda p: p.distance(route_3857)
    )
    
    # 5) Appliquer la limite de distance (filtre sur max_distance_m)
    open_tolls_df = open_tolls_df[open_tolls_df['distance_to_route'] <= max_distance_m]
    
    # Si aucun péage n'est dans le rayon, retourner une liste vide
    if len(open_tolls_df) == 0:
        print(f"Aucun péage à système ouvert trouvé dans un rayon de {max_distance_m/1000:.1f} km")
        return []
    
    # 6) Tri par distance croissante
    open_tolls_df = open_tolls_df.sort_values('distance_to_route')
    
    print(f"Trouvé {len(open_tolls_df)} péages à système ouvert dans un rayon de {max_distance_m/1000:.1f} km")
    
    # 7) Conversion des coordonnées en WGS84 pour le résultat
    to_wgs84 = Transformer.from_crs(_WEBM, _WGS84, always_xy=True).transform
    coords = [
        to_wgs84(geom.x, geom.y)
        for geom in open_tolls_df["_geom3857"]
    ]
    open_tolls_df["longitude"], open_tolls_df["latitude"] = zip(*coords)
    
    # 8) Retourner le résultat sous forme de liste de dictionnaires
    return open_tolls_df[["id", "longitude", "latitude", "role", "distance_to_route"]].to_dict(orient="records")
