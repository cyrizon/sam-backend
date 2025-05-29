"""
poly_utils.py
-------------

Construction d’un MultiPolygon GeoJSON de petits disques (~200 m)
centrés sur les péages à éviter.
"""
from typing import List, Dict
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

def avoidance_multipolygon(
    tolls_to_avoid: List[Dict],
    radius_m: float = 200,
) -> dict:
    polys = [
        Point(t["longitude"], t["latitude"]).buffer(radius_m / 111120)  # ≈ m ➜ °(lat)
        for t in tolls_to_avoid
    ]
    union = unary_union(polys)
    return mapping(union)  # GeoJSON-ready
