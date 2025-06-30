"""
Main cache serializer for OSM data.

Handles the complete serialization and deserialization of OSM cache data
including toll stations, motorway junctions, motorway links, and matched tolls.
"""

import os
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .cache_metadata import CacheMetadata
from .compression_utils import CompressionUtils, CompressionType
from ..models.toll_station import TollStation
from ..models.motorway_junction import MotorwayJunction  
from ..models.motorway_link import MotorwayLink
from ..models.matched_toll import MatchedToll


class CacheSerializer:
    """
    Main serializer for OSM cache data.
    
    Handles complete serialization/deserialization workflow with compression,
    metadata management, and integrity validation.
    """
    
    def __init__(self, cache_dir: str = "osm_cache"):
        """
        Initialize the cache serializer.
        
        Args:
            cache_dir: Directory where cache files will be stored
        """
        self.cache_dir = cache_dir
        self.ensure_cache_directory()
        
        # File names
        self.metadata_file = os.path.join(cache_dir, "metadata.json")
        self.cache_data_file = os.path.join(cache_dir, "cache_data.bin")
        
        print(f"🗂️ Cache serializer initialisé: {cache_dir}")
    
    def ensure_cache_directory(self) -> None:
        """Create cache directory if it doesn't exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            print(f"📁 Dossier cache créé: {self.cache_dir}")
    
    def save_cache(
        self, 
        toll_stations: List[TollStation],
        motorway_junctions: List[MotorwayJunction],
        motorway_links: List[MotorwayLink],
        matched_tolls: List[MatchedToll],
        source_file: str,
        compression_type: Optional[CompressionType] = None
    ) -> bool:
        """
        Save OSM cache data to disk with compression and metadata.
        
        Args:
            toll_stations: List of toll stations
            motorway_junctions: List of motorway junctions
            motorway_links: List of motorway links
            matched_tolls: List of matched tolls
            source_file: Original OSM file path
            compression_type: Compression type to use (auto-detect if None)
            
        Returns:
            bool: True if save successful, False otherwise
        """
        print(f"💾 Sauvegarde du cache OSM...")
        start_time = time.time()
        
        try:
            # Prepare data structure
            cache_data = {
                'toll_stations': toll_stations,
                'motorway_junctions': motorway_junctions,
                'motorway_links': motorway_links,
                'matched_tolls': matched_tolls,
                'save_timestamp': datetime.now().isoformat()
            }
            
            # Auto-detect compression type if not specified
            if compression_type is None:
                # Estimate data size (rough approximation)
                estimated_size_mb = (
                    len(toll_stations) * 0.001 +  # ~1KB per toll station
                    len(motorway_junctions) * 0.002 +  # ~2KB per junction
                    len(motorway_links) * 0.001 +  # ~1KB per link
                    len(matched_tolls) * 0.001  # ~1KB per matched toll
                )
                compression_type = CompressionUtils.get_optimal_compression_type(estimated_size_mb)
                print(f"🔍 Compression auto-détectée: {compression_type.value}")
            
            # Compress and save data
            compressed_data = CompressionUtils.compress_data(cache_data, compression_type)
            
            with open(self.cache_data_file, 'wb') as f:
                f.write(compressed_data)
            
            cache_size = len(compressed_data)
            
            # Create and save metadata
            metadata = CacheMetadata.create_from_source(
                source_file=source_file,
                toll_stations_count=len(toll_stations),
                motorway_junctions_count=len(motorway_junctions),
                motorway_links_count=len(motorway_links),
                matched_tolls_count=len(matched_tolls),
                compression_enabled=(compression_type != CompressionType.NONE),
                compression_type=compression_type.value
            )
            metadata.cache_size = cache_size
            metadata.save_to_file(self.metadata_file)
            
            save_time = time.time() - start_time
            print(f"✅ Cache sauvegardé avec succès en {save_time:.2f}s")
            print(f"   📊 Données: {len(toll_stations)} péages, {len(motorway_junctions)} junctions, "
                  f"{len(motorway_links)} links, {len(matched_tolls)} matchés")
            print(f"   💾 Taille: {cache_size / 1024 / 1024:.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde cache: {e}")
            return False
    
    def load_cache(
        self, 
        source_file: str,
        force_reload: bool = False
    ) -> Optional[Tuple[List[TollStation], List[MotorwayJunction], List[MotorwayLink], List[MatchedToll]]]:
        """
        Load OSM cache data from disk.
        
        Args:
            source_file: Original OSM file path (for validation)
            force_reload: Force reload even if cache is valid
            
        Returns:
            Tuple of lists or None: (toll_stations, motorway_junctions, motorway_links, matched_tolls)
        """
        print(f"📂 Chargement du cache OSM...")
        start_time = time.time()
        
        try:
            # Check if cache files exist
            if not os.path.exists(self.metadata_file) or not os.path.exists(self.cache_data_file):
                print("⚠️ Fichiers de cache introuvables")
                return None
            
            # Load and validate metadata
            metadata = CacheMetadata.load_from_file(self.metadata_file)
            if not metadata:
                print("❌ Impossible de charger les métadonnées")
                return None
            
            # Check cache validity
            if not force_reload and not metadata.is_cache_valid(source_file):
                print("🔄 Cache invalide, rechargement nécessaire")
                return None
            
            # Load compressed data
            with open(self.cache_data_file, 'rb') as f:
                compressed_data = f.read()
            
            # Determine compression type from metadata
            compression_type = CompressionType.NONE
            if metadata.compression_enabled and hasattr(metadata, 'compression_type'):
                try:
                    compression_type = CompressionType(metadata.compression_type)
                except ValueError:
                    print(f"⚠️ Type de compression inconnu: {metadata.compression_type}, utilisation LZMA")
                    compression_type = CompressionType.LZMA
            elif metadata.compression_enabled:
                # Fallback pour anciens caches sans compression_type
                compression_type = CompressionType.LZMA
            
            # Decompress data
            cache_data = CompressionUtils.decompress_data(compressed_data, compression_type)
            
            # Extract data components
            toll_stations = cache_data.get('toll_stations', [])
            motorway_junctions = cache_data.get('motorway_junctions', [])
            motorway_links = cache_data.get('motorway_links', [])
            matched_tolls = cache_data.get('matched_tolls', [])
            
            load_time = time.time() - start_time
            print(f"✅ Cache chargé avec succès en {load_time:.2f}s")
            print(f"   📊 Données: {len(toll_stations)} péages, {len(motorway_junctions)} junctions, "
                  f"{len(motorway_links)} links, {len(matched_tolls)} matchés")
            
            return toll_stations, motorway_junctions, motorway_links, matched_tolls
            
        except Exception as e:
            print(f"❌ Erreur chargement cache: {e}")
            return None
    
    def is_cache_available(self, source_file: str) -> bool:
        """
        Check if valid cache is available for the given source file.
        
        Args:
            source_file: Original OSM file path
            
        Returns:
            bool: True if valid cache is available
        """
        try:
            if not os.path.exists(self.metadata_file) or not os.path.exists(self.cache_data_file):
                return False
            
            metadata = CacheMetadata.load_from_file(self.metadata_file)
            if not metadata:
                return False
            
            return metadata.is_cache_valid(source_file)
            
        except Exception:
            return False
    
    def get_cache_info(self) -> Optional[CacheMetadata]:
        """
        Get information about the current cache.
        
        Returns:
            CacheMetadata or None: Cache metadata if available
        """
        return CacheMetadata.load_from_file(self.metadata_file)
    
    def clear_cache(self) -> bool:
        """
        Clear all cache files.
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            files_to_remove = [self.metadata_file, self.cache_data_file]
            
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Supprimé: {file_path}")
            
            print("✅ Cache vidé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur vidage cache: {e}")
            return False
    
    def get_cache_size_mb(self) -> float:
        """
        Get the total size of cache files in MB.
        
        Returns:
            float: Total cache size in megabytes
        """
        total_size = 0
        
        try:
            for file_path in [self.metadata_file, self.cache_data_file]:
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            
            return total_size / 1024 / 1024
            
        except Exception:
            return 0.0
    
    def benchmark_cache_performance(
        self, 
        toll_stations: List[TollStation],
        motorway_junctions: List[MotorwayJunction],
        motorway_links: List[MotorwayLink],
        matched_tolls: List[MatchedToll],
        source_file: str
    ) -> Dict[str, Any]:
        """
        Benchmark cache performance with different compression methods.
        
        Args:
            toll_stations: List of toll stations
            motorway_junctions: List of motorway junctions  
            motorway_links: List of motorway links
            matched_tolls: List of matched tolls
            source_file: Original OSM file path
            
        Returns:
            Dict: Performance benchmark results
        """
        print("🏁 Benchmark de performance du cache...")
        
        cache_data = {
            'toll_stations': toll_stations,
            'motorway_junctions': motorway_junctions,
            'motorway_links': motorway_links,
            'matched_tolls': matched_tolls,
            'save_timestamp': datetime.now().isoformat()
        }
        
        # Test compression methods
        compression_results = CompressionUtils.test_compression_methods(cache_data)
        
        # Test save/load performance for each method
        performance_results = {}
        
        for comp_type in CompressionType:
            if comp_type.value in compression_results and 'error' not in compression_results[comp_type.value]:
                print(f"🧪 Test {comp_type.value.upper()}...")
                
                # Test save performance
                save_start = time.time()
                success = self.save_cache(
                    toll_stations, motorway_junctions, motorway_links, matched_tolls,
                    source_file, comp_type
                )
                save_time = time.time() - save_start
                
                if success:
                    # Test load performance
                    load_start = time.time()
                    result = self.load_cache(source_file, force_reload=True)
                    load_time = time.time() - load_start
                    
                    cache_size_mb = self.get_cache_size_mb()
                    
                    performance_results[comp_type.value] = {
                        'save_time_s': save_time,
                        'load_time_s': load_time,
                        'cache_size_mb': cache_size_mb,
                        'load_success': result is not None
                    }
                    
                    print(f"   ✅ Save: {save_time:.2f}s, Load: {load_time:.2f}s, "
                          f"Taille: {cache_size_mb:.1f} MB")
                else:
                    performance_results[comp_type.value] = {'error': 'Save failed'}
        
        return {
            'compression_results': compression_results,
            'performance_results': performance_results,
            'data_summary': {
                'toll_stations_count': len(toll_stations),
                'motorway_junctions_count': len(motorway_junctions),
                'motorway_links_count': len(motorway_links),
                'matched_tolls_count': len(matched_tolls)
            }
        }
