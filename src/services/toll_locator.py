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
# Fonction publique
# ────────────────────────────────────────────────────────────────────────────
def locate_tolls(
    ors_geojson: dict,
    csv_path: str | Path = "data/barriers.csv",
    buffer_m: float = 120,
) -> Dict[str, List[Dict]]:
    """
    Renvoie la liste *ordonnée le long de la route* des péages
    rencontrés dans un rayon de `buffer_m` mètres.

    Résultat :  [
        {"id": "APRR_O012", "longitude": 7.21, "latitude": 48.05, "role": "O"},
        ...
    ]
    """
    from shapely.geometry import shape  # import léger

    # 1) Géométrie ORS → LineString WGS84
    route_line = shape(ors_geojson["features"][0]["geometry"])
    # 2) Buffer en Web Mercator
    wgs_to_3857 = Transformer.from_crs(_WGS84, _WEBM, always_xy=True).transform
    route_3857 = LineString([wgs_to_3857(*coord) for coord in route_line.coords])
    buf = route_3857.buffer(buffer_m)

    # 3) Barrières dans la zone
    _ensure_barriers(csv_path)
    hits = _BARRIERS_TREE.query(buf)

    # Filtrage précis : ne garder que les points vraiment dans le buffer
    mask = [_BARRIERS_DF.loc[i, "_geom3857"].within(buf) for i in hits]
    filtered_hits = [i for i, m in zip(hits, mask) if m]

    # Affichage des péages proches (dans un buffer plus large mais hors buffer principal)
    near_buf = route_3857.buffer(500)
    near_hits = _BARRIERS_TREE.query(near_buf)
    near_mask = [
        (_BARRIERS_DF.loc[i, "_geom3857"].within(near_buf) and not _BARRIERS_DF.loc[i, "_geom3857"].within(buf))
        for i in near_hits
    ]
    nearby = [i for i, m in zip(near_hits, near_mask) if m]
    if nearby:
        # Conversion des coordonnées projetées vers WGS84
        to_wgs84 = Transformer.from_crs(_WEBM, _WGS84, always_xy=True).transform
        coords = [
            to_wgs84(geom.x, geom.y)
            for geom in _BARRIERS_DF.loc[nearby, "_geom3857"]
        ]
        df_nearby = _BARRIERS_DF.loc[nearby].copy()
        df_nearby["longitude"], df_nearby["latitude"] = zip(*coords)

    # 4) Tri selon l’avancement sur le tronçon
    project = route_3857.project
    sel = (
        _BARRIERS_DF.loc[filtered_hits]
        .assign(_proj=_BARRIERS_DF.loc[filtered_hits, "_geom3857"].apply(project))
        .sort_values("_proj")
    )

    # Conversion des coordonnées projetées vers WGS84
    to_wgs84 = Transformer.from_crs(_WEBM, _WGS84, always_xy=True).transform
    coords = [
        to_wgs84(geom.x, geom.y)
        for geom in sel["_geom3857"]
    ]
    if coords:
        sel["longitude"], sel["latitude"] = zip(*coords)
    else:
        sel["longitude"], sel["latitude"] = [], []

    # Pour les péages proches (déjà convertis plus haut)
    nearby_list = []
    if nearby:
        df_nearby = _BARRIERS_DF.loc[nearby].copy()
        coords_nearby = [
            to_wgs84(geom.x, geom.y)
            for geom in df_nearby["_geom3857"]
        ]
        if coords_nearby:
            df_nearby["longitude"], df_nearby["latitude"] = zip(*coords_nearby)
        else:
            df_nearby["longitude"], df_nearby["latitude"] = [], []
        nearby_list = df_nearby[["id", "longitude", "latitude", "role"]].to_dict(orient="records")

    return {
        "on_route": sel[["id", "longitude", "latitude", "role"]].to_dict(orient="records"),
        "nearby": nearby_list
    }

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
    import re

    # Charger les données de péages
    _ensure_barriers(csv_path)
    
    # 1) Géométrie ORS → LineString WGS84
    route_line = shape(ors_geojson["features"][0]["geometry"])
    
    # 2) Convertir en Web Mercator pour le calcul de distance
    wgs_to_3857 = Transformer.from_crs(_WGS84, _WEBM, always_xy=True).transform
    route_3857 = LineString([wgs_to_3857(*coord) for coord in route_line.coords])
    
    # 3) Filtrer tous les péages à système ouvert (à partir du nom)
    # On utilise le critère "_o" dans l'ID pour identifier les systèmes ouverts
    open_toll_mask = _BARRIERS_DF['id'].str.contains('_o', case=False, regex=True)
    open_tolls_df = _BARRIERS_DF[open_toll_mask].copy()
    
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
