"""
Cache Metadata V2
----------------

Metadata management for OSM cache V2 with multi-source support.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class CacheMetadata:
    """
    Metadata for cached OSM data V2 (multi-source).
    
    Attributes:
        version: Cache format version (2.0)
        creation_time: When the cache was created
        source_files: Dict mapping source type to file path
        source_hashes: Dict mapping source type to file hash
        source_sizes: Dict mapping source type to file size
        source_modified: Dict mapping source type to modification time
        
        # Parsing statistics
        toll_booths_count: Number of toll booths parsed
        entry_links_count: Number of entry links parsed
        exit_links_count: Number of exit links parsed
        indeterminate_links_count: Number of indeterminate links parsed
        
        # Linking statistics  
        complete_entry_links_count: Number of complete entry links built
        complete_exit_links_count: Number of complete exit links built
        unlinked_indeterminate_count: Number of unlinked indeterminate segments
        
        # Detection statistics
        toll_associations_count: Number of toll-link associations
        links_with_tolls_count: Number of complete links with tolls
        
        # Algorithm parameters
        linking_distance_threshold_m: Distance threshold for linking (meters)
        toll_detection_distance_threshold_m: Distance threshold for toll detection (meters)
        
        # Cache properties
        compression_enabled: Whether cache data is compressed
        compression_type: Type of compression used
        cache_size: Total cache size in bytes
    """
    version: str = "2.0"
    creation_time: str = ""
    
    # Multi-source files
    source_files: Dict[str, str] = field(default_factory=dict)
    source_hashes: Dict[str, str] = field(default_factory=dict)
    source_sizes: Dict[str, int] = field(default_factory=dict)
    source_modified: Dict[str, str] = field(default_factory=dict)
    
    # Parsing counts
    toll_booths_count: int = 0
    entry_links_count: int = 0
    exit_links_count: int = 0
    indeterminate_links_count: int = 0
    
    # Linking results
    complete_entry_links_count: int = 0
    complete_exit_links_count: int = 0
    unlinked_indeterminate_count: int = 0
    
    # Detection results
    toll_associations_count: int = 0
    links_with_tolls_count: int = 0
    
    # Algorithm parameters
    linking_distance_threshold_m: float = 2.0
    toll_detection_distance_threshold_m: float = 500.0
    
    # Cache metadata
    compression_enabled: bool = True
    compression_type: str = "lzma"
    cache_size: int = 0
    
    @classmethod
    def create_from_sources(
        cls,
        source_files: Dict[str, str],
        parsing_stats: Dict[str, int],
        linking_stats: Dict[str, int],
        detection_stats: Dict[str, int],
        algorithm_params: Dict[str, float],
        compression_type: str = "lzma"
    ) -> 'CacheMetadata':
        """
        Create metadata from multiple source files and statistics.
        
        Args:
            source_files: Dict mapping source type to file path
            parsing_stats: Parsing statistics
            linking_stats: Linking statistics
            detection_stats: Detection statistics
            algorithm_params: Algorithm parameters used
            compression_type: Compression type to use
            
        Returns:
            CacheMetadata: Created metadata instance
        """
        source_hashes = {}
        source_sizes = {}
        source_modified = {}
        
        # Process each source file
        for source_type, file_path in source_files.items():
            if os.path.exists(file_path):
                # Calculate file hash
                source_hashes[source_type] = cls._calculate_file_hash(file_path)
                
                # Get file stats
                stat = os.stat(file_path)
                source_sizes[source_type] = stat.st_size
                source_modified[source_type] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            else:
                source_hashes[source_type] = ""
                source_sizes[source_type] = 0
                source_modified[source_type] = ""
        
        return cls(
            creation_time=datetime.now().isoformat(),
            source_files=source_files,
            source_hashes=source_hashes,
            source_sizes=source_sizes,
            source_modified=source_modified,
            
            # Parsing stats
            toll_booths_count=parsing_stats.get('toll_booths', 0),
            entry_links_count=parsing_stats.get('entry_links', 0),
            exit_links_count=parsing_stats.get('exit_links', 0),
            indeterminate_links_count=parsing_stats.get('indeterminate_links', 0),
            
            # Linking stats
            complete_entry_links_count=linking_stats.get('complete_entry_links', 0),
            complete_exit_links_count=linking_stats.get('complete_exit_links', 0),
            unlinked_indeterminate_count=linking_stats.get('unlinked_indeterminate', 0),
            
            # Detection stats
            toll_associations_count=detection_stats.get('total_associations', 0),
            links_with_tolls_count=detection_stats.get('links_with_tolls', 0),
            
            # Algorithm params
            linking_distance_threshold_m=algorithm_params.get('linking_distance_m', 2.0),
            toll_detection_distance_threshold_m=algorithm_params.get('toll_detection_distance_m', 500.0),
            
            compression_enabled=True,
            compression_type=compression_type
        )
    
    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def is_cache_valid(self, current_source_files: Dict[str, str]) -> bool:
        """
        Check if cache is valid for current source files.
        
        Args:
            current_source_files: Current source files to validate against
            
        Returns:
            bool: True if cache is still valid
        """
        # Check if all source files still exist and match
        for source_type, file_path in current_source_files.items():
            if source_type not in self.source_files:
                return False
            
            if self.source_files[source_type] != file_path:
                return False
            
            if not os.path.exists(file_path):
                return False
            
            # Check if file has been modified
            current_hash = self._calculate_file_hash(file_path)
            if current_hash != self.source_hashes.get(source_type, ""):
                return False
        
        return True
    
    def save_to_file(self, file_path: str) -> bool:
        """Save metadata to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde métadonnées V2: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['CacheMetadata']:
        """Load metadata from JSON file."""
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls(**data)
        except Exception as e:
            print(f"❌ Erreur chargement métadonnées V2: {e}")
            return None
    
    def print_summary(self):
        """Print a summary of cache metadata."""
        print(f"📊 Cache OSM V2 - Résumé:")
        print(f"   Version: {self.version}")
        print(f"   Créé le: {self.creation_time}")
        print(f"   Sources:")
        for source_type, file_path in self.source_files.items():
            size_mb = self.source_sizes.get(source_type, 0) / 1024 / 1024
            print(f"     • {source_type}: {size_mb:.1f}MB")
        
        print(f"   Parsing:")
        print(f"     • Toll booths: {self.toll_booths_count}")
        print(f"     • Entry links: {self.entry_links_count}")
        print(f"     • Exit links: {self.exit_links_count}")
        print(f"     • Indeterminate links: {self.indeterminate_links_count}")
        
        print(f"   Linking:")
        print(f"     • Complete entry links: {self.complete_entry_links_count}")
        print(f"     • Complete exit links: {self.complete_exit_links_count}")
        print(f"     • Unlinked indeterminate: {self.unlinked_indeterminate_count}")
        
        print(f"   Detection:")
        print(f"     • Toll associations: {self.toll_associations_count}")
        print(f"     • Links with tolls: {self.links_with_tolls_count}")
        
        print(f"   Cache: {self.cache_size / 1024 / 1024:.1f}MB ({self.compression_type})")
