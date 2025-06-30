"""
Configuration des chemins SAM
=============================

Centralise la gestion des chemins de données et de cache via les variables d'environnement.
"""

import os
from pathlib import Path


class PathConfig:
    """Configuration centralisée des chemins du système SAM."""
    
    @staticmethod
    def get_data_dir() -> str:
        """
        Retourne le répertoire des données depuis DATA_DIR ou valeur par défaut.
        
        Returns:
            Chemin absolu vers le répertoire de données
        """
        data_dir = os.getenv("DATA_DIR", "./data")
        return os.path.abspath(data_dir)
    
    @staticmethod
    def get_cache_dir() -> str:
        """
        Retourne le répertoire du cache depuis CACHE_DIR ou valeur par défaut.
        
        Returns:
            Chemin absolu vers le répertoire de cache
        """
        cache_dir = os.getenv("CACHE_DIR", "./osm_cache_test")
        return os.path.abspath(cache_dir)
    
    @staticmethod
    def ensure_directories_exist():
        """
        Créé les répertoires de données et de cache s'ils n'existent pas.
        """
        data_dir = PathConfig.get_data_dir()
        cache_dir = PathConfig.get_cache_dir()
        
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Répertoires vérifiés:")
        print(f"   DATA_DIR: {data_dir}")
        print(f"   CACHE_DIR: {cache_dir}")
    
    @staticmethod
    def get_data_subdirs() -> dict:
        """
        Retourne les sous-répertoires de données standardisés.
        
        Returns:
            Dictionnaire des chemins vers les sous-répertoires
        """
        data_dir = PathConfig.get_data_dir()
        return {
            'osm': os.path.join(data_dir, 'osm'),
            'operators': os.path.join(data_dir, 'operators'),
            'custom': os.path.join(data_dir, 'custom')
        }
    
    @staticmethod
    def validate_data_structure() -> bool:
        """
        Valide que la structure de données requise existe.
        
        Returns:
            True si la structure est valide, False sinon
        """
        data_dir = PathConfig.get_data_dir()
        subdirs = PathConfig.get_data_subdirs()
        
        # Vérifier les répertoires critiques
        required_dirs = ['osm', 'operators']
        for dir_name in required_dirs:
            if not os.path.exists(subdirs[dir_name]):
                print(f"❌ Répertoire manquant: {subdirs[dir_name]}")
                return False
        
        # Vérifier les fichiers critiques
        required_files = [
            os.path.join(subdirs['osm'], 'toll_booths.geojson'),
            os.path.join(subdirs['osm'], 'motorway_entries.geojson'),
            os.path.join(subdirs['osm'], 'motorway_exits.geojson')
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"⚠️ Fichier manquant: {file_path}")
                # Ne pas retourner False car ces fichiers peuvent être optionnels
        
        print(f"✅ Structure de données validée: {data_dir}")
        return True


# Variables globales pratiques pour usage direct
DATA_DIR = PathConfig.get_data_dir()
CACHE_DIR = PathConfig.get_cache_dir()

# Ensure directories exist on import
PathConfig.ensure_directories_exist()
