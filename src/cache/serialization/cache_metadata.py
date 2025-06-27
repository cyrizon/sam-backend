"""
Cache metadata management for OSM cache serialization.

Handles version control, integrity checks, and cache freshness validation.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class CacheMetadata:
    """
    Metadata for cached OSM data.
    
    Attributes:
        version: Cache format version
        creation_time: When the cache was created
        source_file: Original OSM file path
        source_hash: Hash of the original OSM file
        source_size: Size of the original OSM file in bytes
        source_modified: Last modification time of the original OSM file
        toll_stations_count: Number of toll stations cached
        motorway_junctions_count: Number of motorway junctions cached
        motorway_links_count: Number of motorway links cached
        matched_tolls_count: Number of OSM/CSV matched tolls
        compression_enabled: Whether the cache data is compressed
        cache_size: Total size of cached data in bytes
    """
    version: str = "1.0"
    creation_time: str = ""
    source_file: str = ""
    source_hash: str = ""
    source_size: int = 0
    source_modified: str = ""
    toll_stations_count: int = 0
    motorway_junctions_count: int = 0
    motorway_links_count: int = 0
    matched_tolls_count: int = 0
    compression_enabled: bool = True
    compression_type: str = "lzma"  # Type de compression utilisé
    cache_size: int = 0
    
    @classmethod
    def create_from_source(
        cls, 
        source_file: str,
        toll_stations_count: int = 0,
        motorway_junctions_count: int = 0,
        motorway_links_count: int = 0,
        matched_tolls_count: int = 0,
        compression_enabled: bool = True,
        compression_type: str = "lzma"
    ) -> 'CacheMetadata':
        """
        Create metadata from source OSM file.
        
        Args:
            source_file: Path to the source OSM file
            toll_stations_count: Number of toll stations
            motorway_junctions_count: Number of motorway junctions
            motorway_links_count: Number of motorway links
            matched_tolls_count: Number of matched tolls
            compression_type: str = "lzma"
            
        Returns:
            CacheMetadata: Created metadata instance
        """
        source_hash = ""
        source_size = 0
        source_modified = ""
        
        if os.path.exists(source_file):
            # Calculate file hash
            source_hash = cls._calculate_file_hash(source_file)
            
            # Get file stats
            stat = os.stat(source_file)
            source_size = stat.st_size
            source_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        return cls(
            creation_time=datetime.now().isoformat(),
            source_file=source_file,
            source_hash=source_hash,
            source_size=source_size,
            source_modified=source_modified,
            toll_stations_count=toll_stations_count,
            motorway_junctions_count=motorway_junctions_count,
            motorway_links_count=motorway_links_count,
            matched_tolls_count=matched_tolls_count,
            compression_enabled=compression_enabled,
            compression_type=compression_type
        )
    
    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Hexadecimal hash string
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"⚠️ Erreur calcul hash {file_path}: {e}")
            return ""
    
    def is_cache_valid(self, source_file: str) -> bool:
        """
        Check if cached data is still valid compared to source file.
        
        Args:
            source_file: Path to the source OSM file
            
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if not os.path.exists(source_file):
            print(f"⚠️ Fichier source introuvable: {source_file}")
            return False
        
        # Check if source file has been modified
        stat = os.stat(source_file)
        current_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        if current_modified != self.source_modified:
            print(f"🔄 Fichier source modifié: {current_modified} vs {self.source_modified}")
            return False
        
        # Check file hash for integrity
        current_hash = self._calculate_file_hash(source_file)
        if current_hash != self.source_hash:
            print(f"🔄 Hash du fichier source changé")
            return False
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert metadata to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheMetadata':
        """Create metadata from dictionary."""
        return cls(**data)
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save metadata to JSON file.
        
        Args:
            file_path: Path where to save the metadata
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Métadonnées sauvegardées: {file_path}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde métadonnées {file_path}: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['CacheMetadata']:
        """
        Load metadata from JSON file.
        
        Args:
            file_path: Path to the metadata file
            
        Returns:
            CacheMetadata or None: Loaded metadata or None if failed
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls.from_dict(data)
        except Exception as e:
            print(f"❌ Erreur chargement métadonnées {file_path}: {e}")
            return None
    
    def print_summary(self) -> None:
        """Print a summary of the cache metadata."""
        print(f"""
📋 Résumé du cache OSM:
   📁 Fichier source: {os.path.basename(self.source_file)}
   🕒 Créé le: {self.creation_time}
   📏 Taille source: {self.source_size / 1024 / 1024:.1f} MB
   📊 Données:
      - Péages: {self.toll_stations_count}
      - Junctions: {self.motorway_junctions_count}
      - Links: {self.motorway_links_count}
      - Matchés: {self.matched_tolls_count}
   🗜️ Compression: {'Activée' if self.compression_enabled else 'Désactivée'}
   💾 Taille cache: {self.cache_size / 1024 / 1024:.1f} MB
""")
