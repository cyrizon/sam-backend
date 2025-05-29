"""
toll_cost.py
------------

Calcule le *surcoût marginal* (classe véhicule c1…c5) apporté par
chaque péage de la séquence retournée par `locate_tolls`.

Hypothèse : on paie
  • les gares 'O' à coût fixe (ligne entree_id==sortie_id dans virtual_edges)
  • les gares 'S' (sortie) – tarif (entrée précédente ➜ cette sortie)
Les gares 'E' ne déclenchent pas de paiement.

On retourne la séquence assortie du champ `cost`, puis un tri décroissant.
"""
from __future__ import annotations
from typing import List, Dict

import pandas as pd

def _load_edges(csv_path: str | None = "data/virtual_edges.csv"):
    df = pd.read_csv(csv_path)
    price_cols = [c for c in df.columns if c.startswith("c")]
    return df.set_index(["entree_id", "sortie_id"])[price_cols]

_EDGES = _load_edges()

def add_marginal_cost(
    tolls: List[Dict],
    veh_class: str = "c1",
) -> List[Dict]:
    """
    Ajoute le champ `cost` à chaque dict.

    Retourne **la même liste modifiée** (convenant donc à locate_tolls()).
    """
    prev_entry = None
    for t in tolls:
        rid = t["id"]
        role = t["role"]
        cost = 0.0
        if role == "O":
            # Open : entree_id == sortie_id
            cost = _EDGES.loc[(rid, rid)][veh_class]
            prev_entry = None   # On repart de zéro
        elif role == "E":
            prev_entry = rid
        elif role == "S" and prev_entry:
            cost = _EDGES.loc[(prev_entry, rid)][veh_class]
            prev_entry = None
        t["cost"] = float(cost)
    return tolls

def rank_by_saving(
    tolls: List[Dict],
    max_keep: int,
) -> List[Dict]:
    """
    Renvoie la *liste des péages à éviter* pour respecter max_keep,
    triée par coût décroissant (ceux-là rapportent le plus à éviter).
    """
    excess = max(0, len(tolls) - max_keep)
    if excess == 0:
        return []
    sorted_tolls = sorted(
        [t for t in tolls if t["cost"] > 0], key=lambda d: d["cost"], reverse=True
    )
    return sorted_tolls[:excess]
