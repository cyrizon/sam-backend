"""
tolls_finder.py
===============

Service principal : détecte les gares de péage situées à proximité d’une
route reçue depuis l’API.

Cette version ne contient aucun code « main ».  Le module se contente
d’exposer la fonction `find_tolls_on_route`, que votre route Flask peut
importer directement :

    from src.services.tolls_finder import find_tolls_on_route
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict

import pandas as pd
from shapely.geometry import Point
from pyproj import Transformer

from src.utils.csv_utils import (
    load_tolls_csv,
    find_coord_columns,
    find_info_columns,
)
from src.utils.geojson_utils import route_from_geojson, buffer_route_m


# --------------------------------------------------------------------------- #
# Fonction publique
# --------------------------------------------------------------------------- #

def find_tolls_on_route(
    geojson_data,
    csv_path: str | Path,
    distance_threshold: float = 100,
) -> List[Dict]:
    """
    Identifie les péages situés à moins de *distance_threshold* m du
    tracé GeoJSON.
    """
    # --- 1) Route ----------------------------------------------------------- #
    route_wgs84 = route_from_geojson(geojson_data)
    buffer_m = buffer_route_m(route_wgs84, distance_threshold)

    # --- 2) Données CSV ----------------------------------------------------- #
    df = load_tolls_csv(csv_path)
    lon_col, lat_col, crs_in = find_coord_columns(df)
    name_col, autoroute_col = find_info_columns(df)

    # Conversion chaîne ➜ float (gère la virgule décimale)
    df[lon_col] = df[lon_col].astype(str).str.replace(",", ".").astype(float)
    df[lat_col] = df[lat_col].astype(str).str.replace(",", ".").astype(float)

    # Reprojection éventuelle vers WGS-84
    if crs_in != "EPSG:4326":
        to_wgs = Transformer.from_crs(crs_in, "EPSG:4326", always_xy=True).transform
        lon_lat = map(lambda xy: to_wgs(*xy), zip(df[lon_col], df[lat_col]))
        df["_lon"], df["_lat"] = zip(*lon_lat)
    else:
        df["_lon"] = df[lon_col]
        df["_lat"] = df[lat_col]

    # --- 3) Sélection spatiale --------------------------------------------- #
    to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
    df["_geom_3857"] = [
        Point(*to_3857(lon, lat)) for lon, lat in zip(df["_lon"], df["_lat"])
    ]

    mask = df["_geom_3857"].apply(buffer_m.contains)

    # Optionnel : exclure les gares « côté G »
    if "cote" in df.columns:
        mask &= df["cote"].ne("G")

    selected = df[mask]

    # --- 4) Construction de la réponse ------------------------------------- #
    results: List[Dict] = []
    for _, row in selected.iterrows():
        results.append(
            {
                "id": int(row["id"]),
                "nom": row[name_col] if name_col else "",
                "autoroute": row[autoroute_col] if autoroute_col else "",
                "longitude": float(row["_lon"]),
                "latitude": float(row["_lat"]),
            }
        )

    # Affichage des ids dans results
    print("IDs des péages trouvés :", [toll["id"] for toll in results])

    return results