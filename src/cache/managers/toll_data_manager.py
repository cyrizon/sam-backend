"""
Toll Data Manager
-----------------

Manages toll data cache including barriers.csv and virtual_edges.csv.
Refactored from toll_data_cache.py with <300 lines.
"""

import os
import pandas as pd
from pathlib import Path
from shapely.geometry import Point
from shapely.strtree import STRtree
from pyproj import Transformer


class TollDataManager:
    """
    Cache global pour les données de péages initialisé au démarrage de l'application.
    Résout le problème de rechargement systématique de 305KB.
    """
    
    def __init__(self):
        self._barriers_df = None
        self._virtual_edges_df = None
        self._spatial_index = None
        self._initialized = False
        
        # Transformer pour les projections géographiques
        self._transformer = Transformer.from_crs("EPSG:2154", "EPSG:3857", always_xy=True)
    
    def initialize(self):
        """
        Initialise le cache au démarrage de l'application Flask.
        Une seule fois au startup !
        """
        if self._initialized:
            print("⚠️ Cache Toll Data déjà initialisé, skip...")
            return
            
        print("🚀 Initialisation du cache global des péages...")
        
        try:
            self._load_barriers_data()
            self._load_virtual_edges_data()
            self._create_spatial_index()
            
            self._initialized = True
            print("✅ Cache Toll Data initialisé avec succès!")
            print(f"   - barriers.csv: {len(self._barriers_df)} péages")
            print(f"   - virtual_edges.csv: {len(self._virtual_edges_df)} routes tarifaires")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du cache Toll Data: {e}")
            raise
    
    def _load_barriers_data(self):
        """Charge les données de barriers.csv."""
        barriers_path = os.path.join(os.path.dirname(__file__), '../../../data/barriers.csv')
        self._barriers_df = pd.read_csv(barriers_path)
    
    def _load_virtual_edges_data(self):
        """Charge les données de virtual_edges.csv."""
        edges_path = os.path.join(os.path.dirname(__file__), '../../../data/virtual_edges.csv')
        self._virtual_edges_df = pd.read_csv(edges_path)
        
        # Optimiser l'indexation pour les requêtes de coût
        price_cols = ['c1', 'c2', 'c3', 'c4', 'c5']
        self._virtual_edges_df = self._virtual_edges_df.set_index(["entree", "sortie"])[price_cols]
    
    def _create_spatial_index(self):
        """Crée l'index spatial pour les péages."""
        # Créer les géométries pour l'index spatial
        self._barriers_df["_geom3857"] = [
            Point(*self._transformer.transform(x, y)) 
            for x, y in zip(self._barriers_df["x"], self._barriers_df["y"])
        ]
        self._spatial_index = STRtree(self._barriers_df["_geom3857"].tolist())
    
    @property
    def barriers_df(self):
        """Accès aux données de barriers.csv"""
        if not self._initialized:
            raise RuntimeError("Cache Toll Data non initialisé ! Appelez initialize() d'abord.")
        return self._barriers_df
    
    @property
    def spatial_index(self):
        """Accès à l'index spatial des péages"""
        if not self._initialized:
            raise RuntimeError("Cache Toll Data non initialisé ! Appelez initialize() d'abord.")
        return self._spatial_index
    
    @property
    def virtual_edges_df(self):
        """Accès aux données de virtual_edges.csv"""
        if not self._initialized:
            raise RuntimeError("Cache Toll Data non initialisé ! Appelez initialize() d'abord.")
        return self._virtual_edges_df
    
    def get_stats(self):
        """Statistiques du cache"""
        if not self._initialized:
            return {"status": "non_initialized"}
        
        return {
            "status": "initialized",
            "barriers_count": len(self._barriers_df),
            "virtual_edges_count": len(self._virtual_edges_df),
            "memory_saved_kb": 305  # virtual_edges.csv économisé
        }
    
    def is_initialized(self) -> bool:
        """Retourne True si le cache est initialisé."""
        return self._initialized
