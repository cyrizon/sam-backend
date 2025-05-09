"""
geojson_utils.py
================

Outils dédiés au traitement du GeoJSON reçu depuis le frontend :
extraction du tracé et opérations géométriques de base.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from shapely.geometry import LineString
from shapely.ops import transform
from pyproj import Transformer

# Transformer permanent WGS-84 ➜ Web-Mercator (mètres)
_TO_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
__all__ = ["route_from_geojson", "buffer_route_m"]


# --------------------------------------------------------------------------- #
# Lecture / extraction
# --------------------------------------------------------------------------- #

def route_from_geojson(data: Union[dict, str, Path]) -> LineString:
    """
    Extrait un ``LineString`` WGS-84 du GeoJSON *data* (fichier ou objet déjà chargé).

    Seul le **premier** feature est considéré – conforme à l’implémentation
    d’origine où un seul itinéraire est attendu.
    """
    if not isinstance(data, dict):
        with Path(data).expanduser().open(encoding="utf-8") as f:
            data = json.load(f)

    try:
        coords = data["features"][0]["geometry"]["coordinates"]
    except (KeyError, IndexError) as exc:
        raise ValueError("Structure GeoJSON invalide – impossible de lire les coordonnées.") from exc

    # On ignore l’altitude (qui suit le lat dans certains exports)
    return LineString([(lon, lat) for lon, lat, *_ in coords])


# --------------------------------------------------------------------------- #
# Géométrie
# --------------------------------------------------------------------------- #

def buffer_route_m(route_wgs84: LineString, distance_m: float):
    """
    Retourne un *buffer* en mètres autour du tracé.

    Le route est reprojeté temporairement en EPSG:3857, puis élargi de
    ``distance_m`` mètres. Le polygone retourné est **également** en EPSG:3857.
    """
    return transform(_TO_3857, route_wgs84).buffer(distance_m)
