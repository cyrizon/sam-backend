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
from itertools import combinations

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
    max_comb_size: int = 2,  # Limite la taille des combinaisons pour éviter l'explosion combinatoire
):
    # 1) premier appel (rapide)
    base_payload = {
        "coordinates": coordinates,
        "extra_info": ["tollways"],
    }
    base_route = _call_ors(base_payload)

    # 2) Localisation + coûts
    tolls_dict = locate_tolls(base_route, "data/barriers.csv")
    tolls_on_route = tolls_dict["on_route"]
    tolls_nearby = tolls_dict["nearby"]
    print("Péages sur la route :")
    print(tolls_on_route)
    print("Péages proches :")
    print(tolls_nearby)

    # On fusionne les deux listes pour générer toutes les combinaisons
    all_tolls = tolls_on_route + tolls_nearby
    add_marginal_cost(all_tolls, veh_class)

    # On trie par coût décroissant pour prioriser les plus chers
    all_tolls_sorted = sorted(all_tolls, key=lambda t: t.get("cost", 0), reverse=True)

    # Si aucun péage, on retourne la route de base
    if not all_tolls_sorted:
        return {"fastest": base_route, "cheapest": base_route}

    best_fast, best_cheap = None, None
    seen_polygons = set()

    # 3) Génère toutes les combinaisons de péages à éviter (taille 1 à max_comb_size)
    for k in range(1, min(len(all_tolls_sorted), max_comb_size) + 1):
        for to_avoid in combinations(all_tolls_sorted, k):
            sig = tuple(sorted(t["id"] for t in to_avoid))
            if sig in seen_polygons:
                continue
            seen_polygons.add(sig)

            poly = avoidance_multipolygon(to_avoid)
            pay = copy.deepcopy(base_payload)
            pay["options"] = {"avoid_polygons": poly}
            print(f"Test combinaison évitement : {sig}")
            try:
                alt_route = _call_ors(pay)
            except requests.HTTPError:
                continue  # ORS n’a pas trouvé d’itinéraire

            alt_tolls_dict = locate_tolls(alt_route, "data/barriers.csv")
            alt_tolls_on_route = alt_tolls_dict["on_route"]
            add_marginal_cost(alt_tolls_on_route, veh_class)
            cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
            duration = alt_route["features"][0]["properties"]["summary"]["duration"]

            if best_cheap is None or cost < best_cheap["cost"]:
                best_cheap = {"route": alt_route, "cost": cost, "duration": duration}
            if best_fast is None or duration < best_fast["duration"]:
                best_fast = {"route": alt_route, "cost": cost, "duration": duration}

    # Fallback si rien trouvé
    if best_fast is None:
        return {"fastest": base_route, "cheapest": base_route}

    return {"fastest": best_fast["route"], "cheapest": best_cheap["route"]}
