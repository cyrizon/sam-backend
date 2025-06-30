"""
Cache Serializer
------------------

Main serializer for OSM cache with multi-source support.
"""

import os
import time
import pickle
from typing import Dict, Optional, Tuple, TYPE_CHECKING
from datetime import datetime

from .cache_metadata import CacheMetadata
from .compression_utils import CompressionUtils, CompressionType

if TYPE_CHECKING:
    from ..managers.osm_data_manager import OSMData
    from ..parsers.multi_source_parser import ParsedOSMData
    from ..linking.link_builder import LinkingResult
    from ..linking.toll_detector import TollDetectionResult


class CacheSerializer:
    """
    Main serializer for OSM cache.
    
    Handles serialization/deserialization of multi-source OSM data with
    compression, metadata management, and integrity validation.
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
        
        print(f"🗂️ Cache Serializer initialisé: {cache_dir}")
    
    def ensure_cache_directory(self) -> None:
        """Create cache directory if it doesn't exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            print(f"📁 Dossier cache créé: {self.cache_dir}")
    
    def save_cache(
        self,
        osm_data,  # OSMData type annotation removed to avoid circular import
        source_files: Dict[str, str],
        processing_times: Dict[str, float],
        compression_type: Optional[CompressionType] = None
    ) -> bool:
        """
        Save OSM cache data to disk.
        
        Args:
            osm_data: Complete OSM data
            source_files: Source file paths
            processing_times: Processing time measurements
            compression_type: Compression type (auto-detect if None)
            
        Returns:
            bool: True if save successful
        """
        print(f"💾 Sauvegarde du cache OSM...")
        start_time = time.time()
        
        try:
            # Prepare complete data structure
            cache_data = {
                # Raw parsed data
                'parsed_data': {
                    'toll_booths': osm_data.parsed_data.toll_booths,
                    'entry_links': osm_data.parsed_data.entry_links,
                    'exit_links': osm_data.parsed_data.exit_links,
                    'indeterminate_links': osm_data.parsed_data.indeterminate_links
                },
                
                # Linking results
                'linking_result': {
                    'complete_entry_links': osm_data.linking_result.complete_entry_links,
                    'complete_exit_links': osm_data.linking_result.complete_exit_links,
                    'unlinked_indeterminate': osm_data.linking_result.unlinked_indeterminate
                },
                
                # Toll detection results
                'toll_detection_result': {
                    'associations': osm_data.toll_detection_result.associations,
                    'unassociated_tolls': osm_data.toll_detection_result.unassociated_tolls,
                    'links_with_tolls': osm_data.toll_detection_result.links_with_tolls,
                    'links_without_tolls': osm_data.toll_detection_result.links_without_tolls
                },
                
                # Processing metadata
                'processing_metadata': {
                    'processing_times': processing_times,
                    'save_timestamp': datetime.now().isoformat()
                }
            }
            
            # Auto-detect compression if not specified
            if compression_type is None:
                # Estimate size based on data counts
                total_objects = (
                    len(osm_data.parsed_data.toll_booths) +
                    len(osm_data.parsed_data.get_all_motorway_links()) +
                    len(osm_data.linking_result.get_all_complete_links())
                )
                estimated_size_mb = total_objects * 0.002  # ~2KB per object
                compression_type = CompressionUtils.get_optimal_compression_type(estimated_size_mb)
                print(f"🔍 Compression auto-détectée: {compression_type.value}")
            
            # Serialize and compress data
            serialized_data = pickle.dumps(cache_data)
            compressed_data = CompressionUtils.compress_data(serialized_data, compression_type)
            
            # Save compressed data
            with open(self.cache_data_file, 'wb') as f:
                f.write(compressed_data)
            
            cache_size = len(compressed_data)
            
            # Create and save metadata
            metadata = CacheMetadata.create_from_sources(
                source_files=source_files,
                parsing_stats=osm_data.parsed_data.get_stats(),
                linking_stats=osm_data.linking_result.get_stats(),
                detection_stats=osm_data.toll_detection_result.get_stats(),
                algorithm_params={
                    'linking_distance_m': 2.0,
                    'toll_detection_distance_m': 500.0
                },
                compression_type=compression_type.value
            )
            metadata.cache_size = cache_size
            metadata.save_to_file(self.metadata_file)
            
            save_time = time.time() - start_time
            print(f"✅ Cache sauvegardé avec succès en {save_time:.2f}s")
            print(f"   💾 Taille: {cache_size / 1024 / 1024:.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde cache: {e}")
            return False
    
    def load_cache(
        self,
        source_files: Dict[str, str],
        force_reload: bool = False
    ):
        """
        Load OSM cache data from disk.
        
        Args:
            source_files: Source file paths for validation
            force_reload: Force reload even if cache is valid
            
        Returns:
            OSMData or None: Loaded data or None if failed
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
            if not force_reload and not metadata.is_cache_valid(source_files):
                print("🔄 Cache invalide, rechargement nécessaire")
                return None
            
            # Load compressed data
            with open(self.cache_data_file, 'rb') as f:
                compressed_data = f.read()
            
            # Determine compression type
            compression_type = CompressionType.LZMA
            if hasattr(metadata, 'compression_type'):
                try:
                    compression_type = CompressionType(metadata.compression_type)
                except ValueError:
                    print(f"⚠️ Type de compression inconnu: {metadata.compression_type}")
            
            # Decompress and deserialize
            decompressed_data = CompressionUtils.decompress_data(compressed_data, compression_type)
            cache_data = pickle.loads(decompressed_data)
            
            # Reconstruct OSMData
            osm_data = self._reconstruct_osm_data(cache_data)
            
            load_time = time.time() - start_time
            print(f"✅ Cache chargé avec succès en {load_time:.2f}s")
            
            return osm_data
            
        except Exception as e:
            print(f"❌ Erreur chargement cache: {e}")
            return None
    
    def _reconstruct_osm_data(self, cache_data: Dict):
        """Reconstruct OSMData from cached data."""
        # Import here to avoid circular import
        from ..managers.osm_data_manager import OSMData
        from ..parsers.multi_source_parser import ParsedOSMData
        from ..linking.link_builder import LinkingResult
        from ..linking.toll_detector import TollDetectionResult
        
        # Reconstruct ParsedOSMData
        parsed_data = ParsedOSMData()
        parsed_data.toll_booths = cache_data['parsed_data']['toll_booths']
        parsed_data.entry_links = cache_data['parsed_data']['entry_links']
        parsed_data.exit_links = cache_data['parsed_data']['exit_links']
        parsed_data.indeterminate_links = cache_data['parsed_data']['indeterminate_links']
        
        # Reconstruct LinkingResult
        linking_result = LinkingResult(
            complete_entry_links=cache_data['linking_result']['complete_entry_links'],
            complete_exit_links=cache_data['linking_result']['complete_exit_links'],
            unlinked_indeterminate=cache_data['linking_result']['unlinked_indeterminate']
        )
        
        # Reconstruct TollDetectionResult
        toll_detection_result = TollDetectionResult(
            associations=cache_data['toll_detection_result']['associations'],
            unassociated_tolls=cache_data['toll_detection_result']['unassociated_tolls'],
            links_with_tolls=cache_data['toll_detection_result']['links_with_tolls'],
            links_without_tolls=cache_data['toll_detection_result']['links_without_tolls']
        )
        
        return OSMData(
            parsed_data=parsed_data,
            linking_result=linking_result,
            toll_detection_result=toll_detection_result
        )
    
    def is_cache_available(self, source_files: Dict[str, str]) -> bool:
        """
        Check if valid cache is available for the given source files.
        
        Args:
            source_files: Source file paths to check
            
        Returns:
            bool: True if valid cache is available
        """
        try:
            if not os.path.exists(self.metadata_file) or not os.path.exists(self.cache_data_file):
                return False
            
            metadata = CacheMetadata.load_from_file(self.metadata_file)
            if not metadata:
                return False
            
            return metadata.is_cache_valid(source_files)
            
        except Exception:
            return False
    
    def get_cache_info(self) -> Optional[CacheMetadata]:
        """Get information about the current cache."""
        return CacheMetadata.load_from_file(self.metadata_file)
    
    def clear_cache(self) -> bool:
        """Clear all cache files."""
        try:
            files_to_remove = [self.metadata_file, self.cache_data_file]
            
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Supprimé: {file_path}")
            
            print("✅ Cache vidé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression cache: {e}")
            return False
