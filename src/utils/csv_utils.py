"""
csv_utils.py
============

Fonctions utilitaires pour la lecture et l’analyse du fichier CSV qui
répertorie les gares de péage.

Toutes les fonctions sont pures : elles ne produisent aucun effet de bord
et n’accèdent jamais au système de fichiers en dehors de la lecture.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


# --------------------------------------------------------------------------- #
# Normalisation de texte
# --------------------------------------------------------------------------- #

def normalize(text: str) -> str:
    """
    Normalise une chaîne :

    * passage en ASCII (suppression des accents) ;
    * capitalisation ;
    * remplacement des espaces par « _ ».

    >>> normalize("Nom de colonne")
    'NOM_DE_COLONNE'
    """
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode()
        .strip()
        .upper()
        .replace(" ", "_")
    )


# --------------------------------------------------------------------------- #
# Détection de colonnes dans le CSV
# --------------------------------------------------------------------------- #

def find_coord_columns(df: pd.DataFrame) -> Tuple[str, str, str]:
    """
    Détecte automatiquement les colonnes de coordonnées - et leur CRS :

    * **WGS-84** : colonnes « longitude » / « latitude » ;
    * **Lambert-93** : colonnes « x » / « y » (ou « coord_x » / « coord_y »).

    Returns
    -------
    lon_col : str
        Nom de la colonne longitude ou X.
    lat_col : str
        Nom de la colonne latitude ou Y.
    crs_in  : str
        EPSG de la projection d’origine (« EPSG:4326 » ou « EPSG:2154 »).

    Raises
    ------
    ValueError
        Si aucune combinaison reconnue n’est trouvée.
    """
    lower = [normalize(c) for c in df.columns]

    # Cas WGS-84
    if {"LONGITUDE", "LATITUDE"}.issubset(lower):
        lon_col = df.columns[lower.index("LONGITUDE")]
        lat_col = df.columns[lower.index("LATITUDE")]
        crs_in = "EPSG:4326"

    # Cas Lambert-93
    elif {"X", "Y"}.issubset(lower) or {"COORD_X", "COORD_Y"}.issubset(lower):
        lon_col = next(c for c in df.columns if normalize(c).startswith("X"))
        lat_col = next(c for c in df.columns if normalize(c).startswith("Y"))
        crs_in = "EPSG:2154"

    else:
        raise ValueError("Impossible de trouver les colonnes de coordonnées.")

    return lon_col, lat_col, crs_in


def find_info_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    Recherche les colonnes *nom du péage* et *autoroute* de façon robuste.

    Elles sont optionnelles : la fonction peut retourner `None`.

    Returns
    -------
    name_col : str | None
    autoroute_col : str | None
    """
    norm = {normalize(c): c for c in df.columns}

    name_col = next(
        (
            orig
            for n, orig in norm.items()
            if "NOM" in n and ("PEAGE" in n or "GARE" in n or n.startswith("NOM"))
        ),
        None,
    )

    autoroute_col = next(
        (orig for n, orig in norm.items() if "AUTOR" in n or "ROUTE" in n),
        None,
    )

    return name_col, autoroute_col


# --------------------------------------------------------------------------- #
# Lecture du CSV
# --------------------------------------------------------------------------- #

def load_tolls_csv(csv_path: str | Path) -> pd.DataFrame:
    """
    Charge le fichier CSV en détectant automatiquement le séparateur.

    La plupart des jeux de données IGN utilisent le point-virgule, mais
    certains utilitaires produisent de la virgule – on laisse donc Pandas
    choisir avec `sep=None, engine="python"`.

    Parameters
    ----------
    csv_path : str | Path
        Chemin vers le fichier.

    Returns
    -------
    pandas.DataFrame
    """
    return pd.read_csv(csv_path, sep=None, engine="python")
