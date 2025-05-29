"""
smart_route.py
--------------

Pipeline complet :

    1.  Appel ORS « rapid »  (tollways extra_info)
    2.  Locate → cost → sélection des péages à éviter
    3.  Construction MultiPolygon
    4.  2ᵉ appel ORS avec `options.avoid_polygons`
    5.  Retourne les deux meilleures solutions :
        • la moins chère
        • la plus rapide
"""
from __future__ import annotations
import requests, os, copy

from src.services.toll_locator import locate_tolls
from src.services.toll_cost import add_marginal_cost, rank_by_saving
from src.utils.poly_utils import avoidance_multipolygon

ORS_URL = f"{os.getenv('ORS_BASE_URL')}/v2/directions/driving-car/geojson"

def _call_ors(payload: dict) -> dict:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
    }
    r = requests.post(ORS_URL, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

# ────────────────────────────────────────────────────────────────────────────
def compute_route_with_toll_limit(
    coordinates: list,
    max_tolls: int,
    veh_class: str = "c1",
    max_loops: int = 5,
):
    # 1) premier appel (rapide)
    base_payload = {
        "coordinates": coordinates,
        "extra_info": ["tollways"],
    }
    base_route = _call_ors(base_payload)

    # 2) Localisation + coûts
    tolls = locate_tolls(base_route, "data/barriers.csv")
    print(tolls)
    add_marginal_cost(tolls, veh_class)
    print('ok')
    to_avoid = rank_by_saving(tolls, max_tolls)

    if not to_avoid:
        return {"fastest": base_route, "cheapest": base_route}

    best_fast, best_cheap = None, None
    seen_polygons = set()

    # 3) Boucle d’évitement progressive
    for i in range(1, max_loops + 1):
        poly = avoidance_multipolygon(to_avoid[:i])
        sig = tuple(sorted(t["id"] for t in to_avoid[:i]))
        if sig in seen_polygons:
            continue
        seen_polygons.add(sig)

        pay = copy.deepcopy(base_payload)
        pay["options"] = {"avoid_polygons": poly}
        try:
            alt_route = _call_ors(pay)
        except requests.HTTPError:
            continue  # ORS n’a pas trouvé d’itinéraire

        # Re-compte des péages
        alt_tolls = locate_tolls(alt_route, "data/barriers.csv")
        if len(alt_tolls) > max_tolls:
            continue  # toujours trop de péages

        add_marginal_cost(alt_tolls, veh_class)
        cost = sum(t["cost"] for t in alt_tolls)
        duration = alt_route["features"][0]["properties"]["summary"]["duration"]

        if best_cheap is None or cost < best_cheap["cost"]:
            best_cheap = {"route": alt_route, "cost": cost, "duration": duration}
        if best_fast is None or duration < best_fast["duration"]:
            best_fast = {"route": alt_route, "cost": cost, "duration": duration}

        # Early-exit : on a déjà ≤ max_tolls et coût min
        if i == len(to_avoid):
            break

    # Fallback si rien trouvé
    if best_fast is None:
        return {"fastest": base_route, "cheapest": base_route}

    return {"fastest": best_fast["route"], "cheapest": best_cheap["route"]}
