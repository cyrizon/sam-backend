"""
OSM Data Manager V2
------------------

High-level manager for the new multi-source OSM cache system.
"""

import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..parsers.multi_source_parser import MultiSourceParser, ParsedOSMData
from ..linking.link_builder import LinkBuilder, LinkingResult
from ..linking.toll_detector import TollDetector, TollDetectionResult
from ..models.complete_motorway_link import CompleteMotorwayLink
from ..models.toll_booth_station import TollBoothStation
from ..serialization.cache_serializer import CacheSerializer
from ..serialization.cache_metadata import CacheMetadata


@dataclass
class OSMData:
    """Container pour toutes les données OSM V2."""
    parsed_data: ParsedOSMData
    linking_result: LinkingResult
    toll_detection_result: TollDetectionResult
    
    def get_complete_stats(self) -> Dict[str, int]:
        """Retourne les statistiques complètes."""
        stats = {}
        stats.update(self.parsed_data.get_stats())
        stats.update(self.linking_result.get_stats())
        stats.update(self.toll_detection_result.get_stats())
        return stats


class OSMDataManager:
    """
    Gestionnaire principal pour le système de cache OSM V2.
    
    Coordonne le parsing, la liaison et la détection de péages.
    """
    
    def __init__(self, cache_dir: str = "osm_cache_v2"):
        """Initialise le gestionnaire OSM V2."""
        self._data: Optional[OSMData] = None
        self._initialized = False
        
        # Composants
        self.cache_serializer = CacheSerializer(cache_dir)
        self.multi_parser = None
        self.link_builder = LinkBuilder(max_distance_m=2.0)
        self.toll_detector = TollDetector(max_distance_meters=500.0)
    
    def initialize(self, data_sources: Dict[str, str], force_rebuild: bool = False) -> bool:
        """
        Initialise le gestionnaire avec les sources de données.
        
        Args:
            data_sources: Chemins vers les fichiers GeoJSON
                {
                    'toll_booths': 'path/to/toll_booths.geojson',
                    'entries': 'path/to/motorway_entries.geojson',
                    'exits': 'path/to/motorway_exits.geojson',
                    'indeterminate': 'path/to/motorway_indeterminate.geojson'
                }
            force_rebuild: Force la reconstruction même si déjà initialisé
            
        Returns:
            bool: True si l'initialisation a réussi
        """
        if self._initialized and not force_rebuild:
            print("⚠️ OSM Data Manager V2 déjà initialisé")
            return True
        
        try:
            print("🚀 Initialisation OSM Data Manager V2...")
            
            # 1. Vérifier que tous les fichiers existent
            if not self._validate_data_sources(data_sources):
                return False
            
            # 2. Tenter de charger depuis le cache
            if not force_rebuild:
                cached_data = self.cache_serializer.load_cache(data_sources)
                if cached_data:
                    self._data = cached_data
                    self._initialized = True
                    print("✅ Données chargées depuis le cache V2!")
                    self._print_initialization_summary()
                    return True
            
            # 3. Construire depuis les sources (cache manquant ou force_rebuild)
            print("🔄 Construction depuis les sources...")
            start_time = time.time()
            
            # Parser toutes les sources
            parsing_start = time.time()
            self.multi_parser = MultiSourceParser(data_sources)
            parsed_data = self.multi_parser.parse_all_sources(use_parallel=True)
            parsing_time = time.time() - parsing_start
            
            # Construire les liens complets
            linking_start = time.time()
            linking_result = self.link_builder.build_complete_links(
                parsed_data.entry_links,
                parsed_data.exit_links,
                parsed_data.indeterminate_links
            )
            linking_time = time.time() - linking_start
            
            # Détecter les péages
            detection_start = time.time()
            all_complete_links = linking_result.get_all_complete_links()
            toll_detection_result = self.toll_detector.detect_tolls_on_links(
                all_complete_links,
                parsed_data.toll_booths
            )
            detection_time = time.time() - detection_start
            
            # Stocker les données
            self._data = OSMData(
                parsed_data=parsed_data,
                linking_result=linking_result,
                toll_detection_result=toll_detection_result
            )
            
            # Sauvegarder le cache
            processing_times = {
                'parsing_time': parsing_time,
                'linking_time': linking_time,
                'detection_time': detection_time,
                'total_time': time.time() - start_time
            }
            
            cache_saved = self.cache_serializer.save_cache(
                self._data,
                data_sources,
                processing_times
            )
            
            if cache_saved:
                print("💾 Cache V2 sauvegardé pour les prochains démarrages")
            
            self._initialized = True
            self._print_initialization_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation OSM V2: {e}")
            return False
    
    def _validate_data_sources(self, data_sources: Dict[str, str]) -> bool:
        """Valide que tous les fichiers de données existent."""
        required_sources = ['toll_booths', 'entries', 'exits', 'indeterminate']
        
        for source_name in required_sources:
            if source_name not in data_sources:
                print(f"❌ Source manquante: {source_name}")
                return False
            
            file_path = data_sources[source_name]
            if not os.path.exists(file_path):
                print(f"❌ Fichier introuvable: {file_path}")
                return False
        
        print("✅ Toutes les sources de données sont disponibles")
        return True
    
    def _print_initialization_summary(self):
        """Affiche un résumé de l'initialisation."""
        if not self._data:
            return
        
        stats = self._data.get_complete_stats()
        print(f"\n🎉 OSM Data Manager V2 initialisé avec succès!")
        print(f"📊 Statistiques finales:")
        print(f"   • Toll booths: {stats['toll_booths']}")
        print(f"   • Entry links: {stats['entry_links']} → Complets: {stats['complete_entry_links']}")
        print(f"   • Exit links: {stats['exit_links']} → Complets: {stats['complete_exit_links']}")
        print(f"   • Indeterminate links: {stats['indeterminate_links']} → Non liés: {stats['unlinked_indeterminate']}")
        print(f"   • Associations péage-lien: {stats['total_associations']}")
        print(f"   • Liens avec péages: {stats['links_with_tolls']}")
        print()
    
    # API d'accès aux données
    def get_toll_booths(self) -> List[TollBoothStation]:
        """Retourne toutes les stations de péage."""
        self._ensure_initialized()
        return self._data.parsed_data.toll_booths
    
    def get_complete_entry_links(self) -> List[CompleteMotorwayLink]:
        """Retourne tous les liens d'entrée complets."""
        self._ensure_initialized()
        return self._data.linking_result.complete_entry_links
    
    def get_complete_exit_links(self) -> List[CompleteMotorwayLink]:
        """Retourne tous les liens de sortie complets."""
        self._ensure_initialized()
        return self._data.linking_result.complete_exit_links
    
    def get_all_complete_links(self) -> List[CompleteMotorwayLink]:
        """Retourne tous les liens complets (entrées + sorties)."""
        self._ensure_initialized()
        return self._data.linking_result.get_all_complete_links()
    
    def get_links_with_tolls(self) -> List[CompleteMotorwayLink]:
        """Retourne les liens avec péages associés."""
        self._ensure_initialized()
        return self._data.toll_detection_result.links_with_tolls
    
    def get_data_stats(self) -> Dict[str, int]:
        """Retourne les statistiques complètes des données."""
        self._ensure_initialized()
        return self._data.get_complete_stats()
    
    def is_initialized(self) -> bool:
        """Retourne True si le gestionnaire est initialisé."""
        return self._initialized
    
    def _ensure_initialized(self):
        """Vérifie que le gestionnaire est initialisé."""
        if not self._initialized:
            raise RuntimeError("OSM Data Manager V2 non initialisé! Appelez initialize() d'abord.")
    
    @staticmethod
    def get_default_data_sources(project_root: str) -> Dict[str, str]:
        """
        Retourne les chemins par défaut des sources de données.
        
        Args:
            project_root: Chemin racine du projet
            
        Returns:
            Dict avec les chemins des fichiers par défaut
        """
        data_dir = os.path.join(project_root, 'data', 'osm')
        
        return {
            'toll_booths': os.path.join(data_dir, 'toll_booths.geojson'),
            'entries': os.path.join(data_dir, 'motorway_entries.geojson'),
            'exits': os.path.join(data_dir, 'motorway_exits.geojson'),
            'indeterminate': os.path.join(data_dir, 'motorway_indeterminate.geojson')
        }
    
    # Méthodes de gestion du cache
    def clear_cache(self) -> bool:
        """Vide le cache V2."""
        return self.cache_serializer.clear_cache()
    
    def get_cache_info(self) -> Optional[CacheMetadata]:
        """Retourne les informations du cache V2."""
        return self.cache_serializer.get_cache_info()
    
    def is_cache_available(self, data_sources: Dict[str, str]) -> bool:
        """Vérifie si un cache valide est disponible."""
        return self.cache_serializer.is_cache_available(data_sources)
