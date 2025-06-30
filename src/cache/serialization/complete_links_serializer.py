"""
Complete Motorway Links Serializer
----------------------------------

Sérialisation et désérialisation des liens motorway complets.
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.complete_motorway_link import CompleteMotorwayLink
from ..models.motorway_link import MotorwayLink
from ..models.link_types import LinkType


class CompleteMotorwayLinksSerializer:
    """Sérialiseur pour les liens motorway complets."""
    
    def __init__(self, cache_dir: str = None):
        """
        Initialise le sérialiseur.
        
        Args:
            cache_dir: Répertoire du cache. Si None, utilise CACHE_DIR depuis l'environnement
        """
        # Utiliser la variable d'environnement si cache_dir n'est pas fourni
        if cache_dir is None:
            cache_dir = os.getenv("CACHE_DIR", "./osm_cache_test")
            
        self.cache_dir = cache_dir
        self.links_file = os.path.join(cache_dir, "complete_motorway_links.bin")
        self.stats_file = os.path.join(cache_dir, "linking_stats.json")
        self.metadata_file = os.path.join(cache_dir, "links_metadata.json")
    
    def save_complete_links(
        self, 
        links: List[CompleteMotorwayLink], 
        stats: Dict[str, Any],
        source_files_info: Dict[str, Any]
    ) -> bool:
        """
        Sauvegarde les liens complets et leurs statistiques.
        
        Args:
            links: Liste des liens complets
            stats: Statistiques de liaison
            source_files_info: Informations sur les fichiers sources
            
        Returns:
            bool: True si la sauvegarde a réussi
        """
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Sauvegarder les liens en binaire (pickle)
            with open(self.links_file, 'wb') as f:
                pickle.dump(links, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Sauvegarder les statistiques en JSON
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            # Sauvegarder les métadonnées
            metadata = {
                "created_at": datetime.now().isoformat(),
                "links_count": len(links),
                "source_files": source_files_info,
                "version": "2.0"
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Liens complets sauvegardés:")
            print(f"   • {len(links)} liens -> {self.links_file}")
            print(f"   • Statistiques -> {self.stats_file}")
            print(f"   • Métadonnées -> {self.metadata_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des liens: {e}")
            return False
    
    def load_complete_links(self) -> Optional[tuple[List[CompleteMotorwayLink], Dict[str, Any], Dict[str, Any]]]:
        """
        Charge les liens complets depuis le cache.
        
        Returns:
            Optional[Tuple[liens, stats, metadata]]: Données chargées ou None si échec
        """
        try:
            # Vérifier que tous les fichiers existent
            if not all(os.path.exists(f) for f in [self.links_file, self.stats_file, self.metadata_file]):
                print("🔍 Cache des liens complets non trouvé")
                return None
            
            # Charger les liens
            with open(self.links_file, 'rb') as f:
                links = pickle.load(f)
            
            # Charger les statistiques
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            # Charger les métadonnées
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print(f"📂 Liens complets chargés depuis le cache:")
            print(f"   • {len(links)} liens chargés")
            print(f"   • Créé le: {metadata.get('created_at', 'N/A')}")
            print(f"   • Version: {metadata.get('version', 'N/A')}")
            
            return links, stats, metadata
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des liens: {e}")
            return None
    
    def is_cache_valid(self, source_files_paths: List[str]) -> bool:
        """
        Vérifie si le cache est encore valide en comparant les dates de modification.
        
        Args:
            source_files_paths: Chemins des fichiers sources
            
        Returns:
            bool: True si le cache est valide
        """
        try:
            if not os.path.exists(self.metadata_file):
                return False
            
            # Charger les métadonnées
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            cache_time = datetime.fromisoformat(metadata['created_at'])
            
            # Vérifier si les fichiers sources ont été modifiés après la création du cache
            for file_path in source_files_paths:
                if os.path.exists(file_path):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime > cache_time:
                        print(f"⚠️  Fichier source modifié: {file_path}")
                        return False
                else:
                    print(f"⚠️  Fichier source manquant: {file_path}")
                    return False
            
            print("✅ Cache des liens complets valide")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification du cache: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Supprime le cache des liens complets.
        
        Returns:
            bool: True si la suppression a réussi
        """
        try:
            files_to_remove = [self.links_file, self.stats_file, self.metadata_file]
            removed_count = 0
            
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    removed_count += 1
            
            if removed_count > 0:
                print(f"🗑️  Cache des liens supprimé ({removed_count} fichiers)")
            else:
                print("ℹ️  Aucun cache à supprimer")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression du cache: {e}")
            return False
    
    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """
        Retourne les informations sur le cache.
        
        Returns:
            Dict avec les infos du cache ou None si pas de cache
        """
        try:
            if not os.path.exists(self.metadata_file):
                return None
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Ajouter les tailles des fichiers
            cache_info = metadata.copy()
            cache_info["files_info"] = {}
            
            for name, path in [
                ("links", self.links_file),
                ("stats", self.stats_file),
                ("metadata", self.metadata_file)
            ]:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    cache_info["files_info"][name] = {
                        "path": path,
                        "size_bytes": size,
                        "size_mb": round(size / (1024 * 1024), 2)
                    }
            
            return cache_info
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des infos du cache: {e}")
            return None
