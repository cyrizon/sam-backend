"""
Cache Manager with Motorway Linking
--------------------------------------

Extended Cache Manager that includes motorway segment linking capabilities.
"""

import os
from typing import List, Optional, Dict, Any, Tuple

from .cache_manager_with_pricing import CacheManagerWithPricing
from ..models.motorway_link import MotorwayLink
from ..models.complete_motorway_link import CompleteMotorwayLink
from ..models.link_types import LinkType
from ..parsers.motorway_segments_parser import MotorwaySegmentsParser
from ..linking.motorway_link_orchestrator import MotorwayLinkOrchestrator
from ..serialization.complete_links_serializer import CompleteMotorwayLinksSerializer
from ..services.toll_association_service import TollAssociationService


class CacheManagerWithLinking(CacheManagerWithPricing):
    """Gestionnaire étendu avec capacités de liaison de segments motorway."""
    
    def __init__(self, data_dir: str, cache_dir: str = "osm_cache_test"):
        """
        Initialise le gestionnaire étendu.
        
        Args:
            data_dir: Répertoire racine des données
            cache_dir: Répertoire du cache (pour les orphelins)
        """
        super().__init__(data_dir)
        self.cache_dir = cache_dir
        
        # Composants de liaison
        self.motorway_entries: List[MotorwayLink] = []
        self.motorway_exits: List[MotorwayLink] = []
        self.motorway_indeterminates: List[MotorwayLink] = []
        self.complete_motorway_links: List[CompleteMotorwayLink] = []
        self.linking_orchestrator = MotorwayLinkOrchestrator(
            max_distance_m=2.0, 
            output_dir=cache_dir
        )
        self.links_serializer = CompleteMotorwayLinksSerializer(cache_dir)
        self.toll_association_service = TollAssociationService(max_distance_m=2.0)
        
        # État de liaison
        self.links_built = False
        self.linking_stats: Optional[Dict[str, Any]] = None
        self.toll_association_stats: Optional[Dict[str, Any]] = None
    
    def load_all_including_motorway_linking(self) -> bool:
        """
        Charge toutes les données et effectue la liaison des segments motorway.
        Utilise le cache si disponible et valide.
        
        Returns:
            bool: True si tout a été chargé et lié avec succès
        """
        try:
            # 1. Charger les données de base (toll booths, pricing, etc.)
            if not super().load_all():
                return False
            
            # 2. Charger les segments motorway
            if not self._load_motorway_segments():
                return False
            
            # 3. Vérifier si on peut utiliser le cache
            source_files = self._get_source_files_paths()
            
            if self.links_serializer.is_cache_valid(source_files):
                # Charger depuis le cache
                cached_data = self.links_serializer.load_complete_links()
                if cached_data:
                    self.complete_motorway_links, self.linking_stats, _ = cached_data
                    self.links_built = True
                    print("🚀 Liens motorway chargés depuis le cache!")
                    
                    # Les péages sont déjà associés dans le cache, pas besoin de refaire l'association
                    print("✅ Péages déjà associés depuis le cache")
                    return True
            
            # 4. Construire les liens complets (si pas de cache valide)
            if not self._build_complete_motorway_links():
                return False
            
            # 5. Associer les péages aux liens
            if not self._associate_tolls_to_links():
                return False
            
            # 6. Sauvegarder dans le cache
            self._save_links_to_cache(source_files)
            
            print("✅ Cache complet avec liaison motorway chargé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement complet du cache: {e}")
            return False
    
    def _load_motorway_segments(self) -> bool:
        """
        Charge les segments motorway depuis les fichiers GeoJSON.
        
        Returns:
            bool: True si le chargement a réussi
        """
        try:
            print("\n🛣️  Chargement des segments motorway...")
            
            # Chemins des fichiers
            entries_path = os.path.join(self.osm_dir, "motorway_entries.geojson")
            exits_path = os.path.join(self.osm_dir, "motorway_exits.geojson")
            indeterminates_path = os.path.join(self.osm_dir, "motorway_indeterminate.geojson")
            
            # Parser pour les segments
            parser = MotorwaySegmentsParser()
            
            # Charger les entrées
            if os.path.exists(entries_path):
                self.motorway_entries = parser.parse_segments(entries_path, LinkType.ENTRY)
                print(f"   📥 Entrées chargées: {len(self.motorway_entries)}")
            else:
                print(f"   ⚠️  Fichier entrées non trouvé: {entries_path}")
            
            # Charger les sorties
            if os.path.exists(exits_path):
                self.motorway_exits = parser.parse_segments(exits_path, LinkType.EXIT)
                print(f"   📤 Sorties chargées: {len(self.motorway_exits)}")
            else:
                print(f"   ⚠️  Fichier sorties non trouvé: {exits_path}")
            
            # Charger les indéterminés
            if os.path.exists(indeterminates_path):
                self.motorway_indeterminates = parser.parse_segments(indeterminates_path, LinkType.INDETERMINATE)
                print(f"   🔀 Indéterminés chargés: {len(self.motorway_indeterminates)}")
            else:
                print(f"   ⚠️  Fichier indéterminés non trouvé: {indeterminates_path}")
            
            total_segments = len(self.motorway_entries) + len(self.motorway_exits) + len(self.motorway_indeterminates)
            print(f"   📊 Total segments chargés: {total_segments}")
            
            return total_segments > 0
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des segments motorway: {e}")
            return False
    
    def _build_complete_motorway_links(self) -> bool:
        """
        Construit les liens complets en utilisant l'orchestrateur.
        
        Returns:
            bool: True si la construction a réussi
        """
        try:
            print("\n🏗️  Construction des liens complets...")
            
            # Utiliser l'orchestrateur pour construire les liens
            self.complete_motorway_links, self.linking_stats = self.linking_orchestrator.build_complete_links(
                self.motorway_entries,
                self.motorway_exits,
                self.motorway_indeterminates
            )
            
            self.links_built = True
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la construction des liens: {e}")
            return False
    
    def _associate_tolls_to_links(self) -> bool:
        """
        Associe les péages aux liens complets construits.
        
        Returns:
            bool: True si l'association a réussi
        """
        try:
            print("\n🏪 Association des péages aux liens...")
            
            if not self.complete_motorway_links:
                print("   ⚠️  Aucun lien complet à traiter pour l'association")
                return True
            
            if not self.toll_booths:
                print("   ⚠️  Aucun péage chargé pour l'association")
                return True
            
            # Utiliser le service d'association
            self.toll_association_stats = self.toll_association_service.associate_tolls_to_links(
                self.complete_motorway_links,
                self.toll_booths
            )
            
            # Afficher un rapport détaillé
            self.toll_association_service.print_toll_association_report(self.complete_motorway_links)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'association des péages: {e}")
            return False

    def get_toll_association_statistics(self) -> Optional[Dict[str, Any]]:
        """Retourne les statistiques d'association des péages."""
        return self.toll_association_stats

    def get_links_with_tolls(self) -> List[CompleteMotorwayLink]:
        """Retourne uniquement les liens qui ont des péages associés."""
        return self.toll_association_service.get_links_with_tolls(self.complete_motorway_links)

    def get_links_by_toll_type(self, toll_type: str) -> List[CompleteMotorwayLink]:
        """
        Retourne les liens filtrés par type de péage.
        
        Args:
            toll_type: "O" pour ouvert, "F" pour fermé
            
        Returns:
            Liste des liens correspondants
        """
        return self.toll_association_service.get_links_by_toll_type(self.complete_motorway_links, toll_type)

    def get_links_by_operator(self, operator: str) -> List[CompleteMotorwayLink]:
        """
        Retourne les liens filtrés par opérateur de péage.
        
        Args:
            operator: Nom de l'opérateur (ex: "ASF", "APRR")
            
        Returns:
            Liste des liens correspondants
        """
        return self.toll_association_service.get_links_by_operator(self.complete_motorway_links, operator)

    def get_complete_motorway_links(self) -> List[CompleteMotorwayLink]:
        """Retourne tous les liens complets construits."""
        return self.complete_motorway_links
    
    def get_entry_links(self) -> List[CompleteMotorwayLink]:
        """Retourne uniquement les liens d'entrée."""
        return [link for link in self.complete_motorway_links if link.link_type == LinkType.ENTRY]
    
    def get_exit_links(self) -> List[CompleteMotorwayLink]:
        """Retourne uniquement les liens de sortie."""
        return [link for link in self.complete_motorway_links if link.link_type == LinkType.EXIT]
    
    def get_link_by_id(self, link_id: str) -> Optional[CompleteMotorwayLink]:
        """Récupère un lien par son ID."""
        for link in self.complete_motorway_links:
            if link.link_id == link_id:
                return link
        return None
    
    def get_links_containing_way_id(self, way_id: str) -> List[CompleteMotorwayLink]:
        """Récupère tous les liens contenant un way_id spécifique."""
        result = []
        for link in self.complete_motorway_links:
            for segment in link.segments:
                if segment.way_id == way_id:
                    result.append(link)
                    break
        return result
    
    def get_linking_statistics(self) -> Optional[Dict[str, Any]]:
        """Retourne les statistiques de liaison."""
        return self.linking_stats
    
    def get_extended_summary(self) -> Dict[str, Any]:
        """Retourne un résumé étendu incluant les informations de liaison."""
        base_summary = super().get_summary()
        
        if self.links_built:
            base_summary.update({
                "motorway_linking": {
                    "segments_loaded": {
                        "entries": len(self.motorway_entries),
                        "exits": len(self.motorway_exits),
                        "indeterminates": len(self.motorway_indeterminates),
                        "total": len(self.motorway_entries) + len(self.motorway_exits) + len(self.motorway_indeterminates)
                    },
                    "links_built": {
                        "total_links": len(self.complete_motorway_links),
                        "entry_links": len(self.get_entry_links()),
                        "exit_links": len(self.get_exit_links())
                    },
                    "linking_stats": self.linking_stats
                }
            })
        else:
            base_summary.update({
                "motorway_linking": {
                    "status": "not_built",
                    "segments_loaded": {
                        "entries": len(self.motorway_entries),
                        "exits": len(self.motorway_exits),
                        "indeterminates": len(self.motorway_indeterminates)
                    }
                }
            })
        
        return base_summary
    
    def rebuild_links(self, max_distance_m: float = 2.0) -> bool:
        """
        Reconstruit les liens avec une nouvelle distance maximale.
        
        Args:
            max_distance_m: Nouvelle distance maximale pour lier les segments
            
        Returns:
            bool: True si la reconstruction a réussi
        """
        try:
            print(f"🔄 Reconstruction des liens avec distance max: {max_distance_m}m")
            
            # Créer un nouvel orchestrateur avec la nouvelle distance
            self.linking_orchestrator = MotorwayLinkOrchestrator(
                max_distance_m=max_distance_m,
                output_dir=self.cache_dir
            )
            
            # Reconstruire les liens
            return self._build_complete_motorway_links()
            
        except Exception as e:
            print(f"❌ Erreur lors de la reconstruction: {e}")
            return False
    
    def export_links_to_geojson(self, output_path: str) -> bool:
        """
        Exporte les liens complets vers un fichier GeoJSON.
        
        Args:
            output_path: Chemin du fichier de sortie
            
        Returns:
            bool: True si l'export a réussi
        """
        try:
            import json
            
            features = []
            for link in self.complete_motorway_links:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "link_id": link.link_id,
                        "link_type": link.link_type.value,
                        "segment_count": link.get_segment_count(),
                        "destination": link.destination,
                        "has_toll": link.has_toll()
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": link.get_all_coordinates()
                    }
                }
                features.append(feature)
            
            geojson_data = {
                "type": "FeatureCollection",
                "features": features
            }
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Liens exportés vers: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export: {e}")
            return False
    
    def _get_source_files_paths(self) -> List[str]:
        """Retourne les chemins des fichiers sources pour vérifier la validité du cache."""
        return [
            os.path.join(self.osm_dir, "motorway_entries.geojson"),
            os.path.join(self.osm_dir, "motorway_exits.geojson"),
            os.path.join(self.osm_dir, "motorway_indeterminate.geojson")
        ]
    
    def _save_links_to_cache(self, source_files: List[str]):
        """Sauvegarde les liens dans le cache."""
        try:
            source_files_info = {}
            for file_path in source_files:
                if os.path.exists(file_path):
                    source_files_info[os.path.basename(file_path)] = {
                        "path": file_path,
                        "mtime": os.path.getmtime(file_path),
                        "size": os.path.getsize(file_path)
                    }
            
            success = self.links_serializer.save_complete_links(
                self.complete_motorway_links,
                self.linking_stats,
                source_files_info
            )
            
            if success:
                print("💾 Liens sauvegardés dans le cache pour les prochains démarrages")
            
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde du cache: {e}")
    
    def clear_links_cache(self) -> bool:
        """Supprime le cache des liens et force la reconstruction."""
        return self.links_serializer.clear_cache()
    
    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """Retourne les informations sur le cache des liens."""
        return self.links_serializer.get_cache_info()
    
    def force_rebuild_links(self, max_distance_m: float = 2.0) -> bool:
        """Force la reconstruction des liens en ignorant le cache."""
        try:
            print("🔄 Reconstruction forcée des liens (cache ignoré)...")
            
            # Supprimer le cache existant
            self.clear_links_cache()
            
            # Reconstruire
            self.linking_orchestrator = MotorwayLinkOrchestrator(
                max_distance_m=max_distance_m,
                output_dir=self.cache_dir
            )
            
            success = self._build_complete_motorway_links()
            
            if success:
                # Sauvegarder le nouveau cache
                source_files = self._get_source_files_paths()
                self._save_links_to_cache(source_files)
            
            return success
            
        except Exception as e:
            print(f"❌ Erreur lors de la reconstruction forcée: {e}")
            return False
