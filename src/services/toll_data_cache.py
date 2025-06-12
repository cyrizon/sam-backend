"""
toll_data_cache.py
-----------------

Cache global pour toutes les données de péages au démarrage de l'application.
VOTRE IDÉE : Charger une seule fois au startup au lieu de recharger 305KB systématiquement.
"""

import pandas as pd
from pathlib import Path
from shapely.geometry import Point
from shapely.strtree import STRtree
from pyproj import Transformer
import os


class GlobalTollDataCache:
    """
    Cache global pour les données de péages initialisé au démarrage de Flask.
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
        VOTRE IDÉE : Une seule fois au startup !
        """
        if self._initialized:
            print("⚠️ Cache déjà initialisé, skip...")
            return
            
        print("🚀 Initialisation du cache global des péages...")
        
        try:            # 1. Charger barriers.csv (5.83KB - déjà optimisé mais on centralise)
            barriers_path = os.path.join(os.path.dirname(__file__), '../../data/barriers.csv')
            self._barriers_df = pd.read_csv(barriers_path)
            
            # Créer les géométries pour l'index spatial
            self._barriers_df["_geom3857"] = [
                Point(*self._transformer.transform(x, y)) 
                for x, y in zip(self._barriers_df["x"], self._barriers_df["y"])
            ]
            self._spatial_index = STRtree(self._barriers_df["_geom3857"].tolist())
            
            # 2. Charger virtual_edges.csv (305KB - PROBLÈME RÉSOLU !)
            edges_path = os.path.join(os.path.dirname(__file__), '../../data/virtual_edges.csv')
            self._virtual_edges_df = pd.read_csv(edges_path)
            
            # Optimiser l'indexation pour les requêtes de coût
            price_cols = ['c1', 'c2', 'c3', 'c4', 'c5']
            self._virtual_edges_df = self._virtual_edges_df.set_index(["entree", "sortie"])[price_cols]
            
            self._initialized = True
            
            print("✅ Cache global initialisé avec succès!")
            print(f"   - barriers.csv: {len(self._barriers_df)} péages")
            print(f"   - virtual_edges.csv: {len(self._virtual_edges_df)} routes tarifaires")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du cache: {e}")
            raise
    
    @property
    def barriers_df(self):
        """Accès aux données de barriers.csv"""
        if not self._initialized:
            raise RuntimeError("Cache non initialisé ! Appelez initialize() d'abord.")
        return self._barriers_df
    
    @property
    def spatial_index(self):
        """Accès à l'index spatial des péages"""
        if not self._initialized:
            raise RuntimeError("Cache non initialisé ! Appelez initialize() d'abord.")
        return self._spatial_index
    
    @property
    def virtual_edges_df(self):
        """Accès aux données de virtual_edges.csv"""
        if not self._initialized:
            raise RuntimeError("Cache non initialisé ! Appelez initialize() d'abord.")
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


# Instance globale unique
toll_data_cache = GlobalTollDataCache()
