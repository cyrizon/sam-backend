"""
Compression utilities for OSM cache serialization.

Provides efficient compression and decompression of cache data.
"""

import gzip
import lzma
import pickle
from typing import Any, Optional, Dict
from enum import Enum


class CompressionType(Enum):
    """Available compression types."""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"


class CompressionUtils:
    """
    Utilities for compressing and decompressing cache data.
    
    Supports multiple compression algorithms with automatic fallback.
    """
    
    @staticmethod
    def compress_data(
        data: Any, 
        compression_type: CompressionType = CompressionType.LZMA,
        compression_level: int = 6
    ) -> bytes:
        """
        Compress data using the specified compression algorithm.
        
        Args:
            data: Data to compress (will be pickled first)
            compression_type: Type of compression to use
            compression_level: Compression level (1-9, higher = better compression)
            
        Returns:
            bytes: Compressed data
        """
        # First, serialize the data with pickle
        try:
            serialized_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"📦 Données sérialisées: {len(serialized_data) / 1024 / 1024:.1f} MB")
        except Exception as e:
            raise Exception(f"Erreur sérialisation pickle: {e}")
        
        # Then compress based on the specified type
        if compression_type == CompressionType.NONE:
            print("📦 Aucune compression appliquée")
            return serialized_data
            
        elif compression_type == CompressionType.GZIP:
            try:
                compressed_data = gzip.compress(serialized_data, compresslevel=compression_level)
                compression_ratio = len(compressed_data) / len(serialized_data)
                print(f"🗜️ Compression GZIP: {len(compressed_data) / 1024 / 1024:.1f} MB "
                      f"(ratio: {compression_ratio:.2f})")
                return compressed_data
            except Exception as e:
                raise Exception(f"Erreur compression GZIP: {e}")
                
        elif compression_type == CompressionType.LZMA:
            try:
                compressed_data = lzma.compress(
                    serialized_data, 
                    format=lzma.FORMAT_XZ,
                    preset=compression_level
                )
                compression_ratio = len(compressed_data) / len(serialized_data)
                print(f"🗜️ Compression LZMA: {len(compressed_data) / 1024 / 1024:.1f} MB "
                      f"(ratio: {compression_ratio:.2f})")
                return compressed_data
            except Exception as e:
                raise Exception(f"Erreur compression LZMA: {e}")
        
        else:
            raise ValueError(f"Type de compression non supporté: {compression_type}")
    
    @staticmethod
    def decompress_data(
        compressed_data: bytes,
        compression_type: CompressionType = CompressionType.LZMA
    ) -> Any:
        """
        Decompress data using the specified compression algorithm.
        
        Args:
            compressed_data: Compressed data bytes
            compression_type: Type of compression used
            
        Returns:
            Any: Decompressed and deserialized data
        """
        if compression_type == CompressionType.NONE:
            serialized_data = compressed_data
            
        elif compression_type == CompressionType.GZIP:
            try:
                serialized_data = gzip.decompress(compressed_data)
                print(f"🗜️ Décompression GZIP: {len(serialized_data) / 1024 / 1024:.1f} MB")
            except Exception as e:
                raise Exception(f"Erreur décompression GZIP: {e}")
                
        elif compression_type == CompressionType.LZMA:
            try:
                serialized_data = lzma.decompress(compressed_data)
                print(f"🗜️ Décompression LZMA: {len(serialized_data) / 1024 / 1024:.1f} MB")
            except Exception as e:
                raise Exception(f"Erreur décompression LZMA: {e}")
        
        else:
            raise ValueError(f"Type de compression non supporté: {compression_type}")
        
        # Deserialize with pickle
        try:
            data = pickle.loads(serialized_data)
            print(f"📦 Données désérialisées avec succès")
            return data
        except Exception as e:
            raise Exception(f"Erreur désérialisation pickle: {e}")
    
    @staticmethod
    def get_optimal_compression_type(data_size_mb: float) -> CompressionType:
        """
        Get the optimal compression type based on data size.
        
        Args:
            data_size_mb: Size of data in megabytes
            
        Returns:
            CompressionType: Recommended compression type
        """
        if data_size_mb < 1.0:
            # Small data: no compression overhead
            return CompressionType.NONE
        elif data_size_mb < 10.0:
            # Medium data: fast compression
            return CompressionType.GZIP
        else:
            # Large data: best compression
            return CompressionType.LZMA
    
    @staticmethod
    def test_compression_methods(data: Any) -> Dict[str, Dict]:
        """
        Test different compression methods and return statistics.
        
        Args:
            data: Data to test compression on
            
        Returns:
            Dict: Statistics for each compression method
        """
        results = {}
        
        # Serialize once for fair comparison
        serialized_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        original_size = len(serialized_data)
        
        print(f"🧪 Test de compression sur {original_size / 1024 / 1024:.1f} MB de données...")
        
        # Test each compression method
        for comp_type in CompressionType:
            try:
                import time
                start_time = time.time()
                
                if comp_type == CompressionType.NONE:
                    compressed_data = serialized_data
                    compress_time = 0
                    decompress_time = 0
                    decompressed_data = serialized_data
                else:
                    # Compress
                    compressed_data = CompressionUtils.compress_data(data, comp_type)
                    compress_time = time.time() - start_time
                    
                    # Decompress
                    decompress_start = time.time()
                    decompressed_data = pickle.dumps(
                        CompressionUtils.decompress_data(compressed_data, comp_type),
                        protocol=pickle.HIGHEST_PROTOCOL
                    )
                    decompress_time = time.time() - decompress_start
                
                # Verify integrity
                integrity_ok = decompressed_data == serialized_data
                
                results[comp_type.value] = {
                    'original_size_mb': original_size / 1024 / 1024,
                    'compressed_size_mb': len(compressed_data) / 1024 / 1024,
                    'compression_ratio': len(compressed_data) / original_size,
                    'space_saved_percent': (1 - len(compressed_data) / original_size) * 100,
                    'compress_time_s': compress_time,
                    'decompress_time_s': decompress_time,
                    'integrity_ok': integrity_ok
                }
                
                print(f"   {comp_type.value.upper()}: "
                      f"{len(compressed_data) / 1024 / 1024:.1f} MB "
                      f"({results[comp_type.value]['compression_ratio']:.2f} ratio, "
                      f"{results[comp_type.value]['space_saved_percent']:.1f}% saved)")
            
            except Exception as e:
                print(f"   ❌ {comp_type.value.upper()}: Erreur - {e}")
                results[comp_type.value] = {'error': str(e)}
        
        return results
