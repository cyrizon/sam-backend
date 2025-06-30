"""
Cache Accessor V2
=================

Accès unifié au système de cache V2 pour récupérer péages, links complets et données motorway.
Utilise le nouveau cache V2 avec liens motorway et association automatique des péages.
"""

from typing import List, Optional, Dict, Any
from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking
from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink
from src.cache.v2.models.toll_booth_station import TollBoothStation


class CacheAccessor:
    """Accesseur unifié au cache V2 avec liens motorway et péages associés."""
    
    _cache_manager: Optional[V2CacheManagerWithLinking] = None
    _initialized: bool = False
    
    @classmethod
    def _ensure_initialized(cls) -> bool:
        """Assure que le cache V2 est initialisé."""
        if cls._initialized and cls._cache_manager:
            return True
        
        try:
            print("🚀 Initialisation du cache V2 pour route optimization...")
            cls._cache_manager = V2CacheManagerWithLinking("data")
            success = cls._cache_manager.load_all_including_motorway_linking()
            
            if success:
                cls._initialized = True
                print("✅ Cache V2 initialisé avec succès")
                return True
            else:
                print("❌ Échec d'initialisation du cache V2")
                return False
                
        except Exception as e:
            print(f"❌ Erreur initialisation cache V2: {e}")
            return False
    
    @classmethod
    def get_toll_stations(cls) -> List[TollBoothStation]:
        """
        Récupère toutes les stations de péage du cache V2.
        
        Returns:
            Liste des stations de péage avec types (ouvert/fermé)
        """
        if not cls._ensure_initialized():
            return []
        
        return cls._cache_manager.toll_booths or []
    
    @classmethod
    def get_complete_motorway_links(cls) -> List[CompleteMotorwayLink]:
        """
        Récupère tous les liens complets d'autoroute du cache V2.
        
        Returns:
            Liste des liens complets avec segments chaînés
        """
        if not cls._ensure_initialized():
            return []
        
        return cls._cache_manager.get_complete_motorway_links()
    
    @classmethod
    def get_links_with_tolls(cls) -> List[CompleteMotorwayLink]:
        """
        Récupère uniquement les liens motorway avec péages associés.
        
        Returns:
            Liste des liens avec péages (distance < 2m)
        """
        if not cls._ensure_initialized():
            return []
        
        return cls._cache_manager.get_links_with_tolls()
    
    @classmethod
    def get_entry_links(cls) -> List[CompleteMotorwayLink]:
        """
        Récupère tous les liens d'entrée d'autoroute.
        
        Returns:
            Liste des liens d'entrée
        """
        if not cls._ensure_initialized():
            return []
        
        return cls._cache_manager.get_entry_links()
    
    @classmethod
    def get_exit_links(cls) -> List[CompleteMotorwayLink]:
        """
        Récupère tous les liens de sortie d'autoroute.
        
        Returns:
            Liste des liens de sortie
        """
        if not cls._ensure_initialized():
            return []
        
        return cls._cache_manager.get_exit_links()
    
    @classmethod
    def get_links_by_toll_type(cls, toll_type: str) -> List[CompleteMotorwayLink]:
        """
        Récupère les liens filtrés par type de péage.
        
        Args:
            toll_type: "O" pour ouvert, "F" pour fermé
            
        Returns:
            Liste des liens correspondants
        """
        if not cls._ensure_initialized():
            return []
        
        return cls._cache_manager.get_links_by_toll_type(toll_type)
    
    @classmethod
    def get_links_by_operator(cls, operator: str) -> List[CompleteMotorwayLink]:
        """
        Récupère les liens filtrés par opérateur de péage.
        
        Args:
            operator: Nom de l'opérateur (ex: "ASF", "APRR")
            
        Returns:
            Liste des liens correspondants
        """
        if not cls._ensure_initialized():
            return []
        
        return cls._cache_manager.get_links_by_operator(operator)
    
    @classmethod
    def calculate_toll_cost(
        cls, 
        toll_from: TollBoothStation, 
        toll_to: TollBoothStation, 
        vehicle_category: str = "1",
        distance_km: Optional[float] = None
    ) -> Optional[float]:
        """
        Calcule le coût entre deux péages en utilisant le cache V2.
        
        Args:
            toll_from: Station de péage de départ
            toll_to: Station de péage d'arrivée  
            vehicle_category: Catégorie du véhicule (1-5)
            distance_km: Distance en km (calculée automatiquement si non fournie)
            
        Returns:
            Coût en euros ou None si impossible
        """
        if not cls._ensure_initialized():
            return None
        
        try:
            # Utiliser la méthode calculate_toll_cost du cache manager
            result = cls._cache_manager.calculate_toll_cost(
                from_id=toll_from.osm_id,
                to_id=toll_to.osm_id,
                vehicle_class=vehicle_category,
                distance_km=distance_km
            )
            
            if result and 'cost' in result:
                return round(result['cost'], 2)
            else:
                print(f"⚠️ Calcul de coût impossible entre {toll_from.osm_id} et {toll_to.osm_id}")
                return None
            
        except Exception as e:
            print(f"❌ Erreur calcul coût péage: {e}")
            return None
    
    @classmethod
    def calculate_total_cost(
        cls, 
        toll_objects: List, 
        vehicle_category: str = "1"
    ) -> float:
        """
        Calcule le coût total d'une liste de péages par couples consécutifs.
        
        Args:
            toll_objects: Liste d'objets TollBoothStation ou CompleteMotorwayLink
            vehicle_category: Catégorie du véhicule (1-5)
            
        Returns:
            Coût total en euros
        """
        if not toll_objects or len(toll_objects) < 2:
            return 0.0
        
        # Filtrer pour ne garder que les TollBoothStation
        toll_stations = []
        for obj in toll_objects:
            if hasattr(obj, 'osm_id') and hasattr(obj, 'name'):
                # C'est un TollBoothStation
                toll_stations.append(obj)
            elif hasattr(obj, 'associated_toll'):
                # C'est un CompleteMotorwayLink avec péage associé
                toll_stations.append(obj.associated_toll)
        
        if len(toll_stations) < 2:
            return 0.0
        
        # Calcul par couples consécutifs
        total_cost = 0.0
        for i in range(len(toll_stations) - 1):
            toll_from = toll_stations[i]
            toll_to = toll_stations[i + 1]
            
            cost = cls.calculate_toll_cost(toll_from, toll_to, vehicle_category)
            if cost is not None:
                total_cost += cost
        
        return round(total_cost, 2)

    @classmethod
    def is_cache_available(cls) -> bool:
        """
        Vérifie si le cache V2 est disponible et chargé.
        
        Returns:
            True si le cache est disponible, False sinon
        """
        return cls._initialized and cls._cache_manager is not None
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Récupère les statistiques complètes du cache V2.
        
        Returns:
            Dictionnaire avec les statistiques détaillées
        """
        if not cls._ensure_initialized():
            return {
                'available': False,
                'toll_stations': 0,
                'complete_links': 0,
                'links_with_tolls': 0,
                'entry_links': 0,
                'exit_links': 0
            }
        
        links_with_tolls = cls.get_links_with_tolls()
        entry_links = cls.get_entry_links()
        exit_links = cls.get_exit_links()
        
        # Statistiques détaillées par opérateur
        operators_stats = {}
        for link in links_with_tolls:
            op = link.associated_toll.operator
            operators_stats[op] = operators_stats.get(op, 0) + 1
        
        # Statistiques par type de péage
        open_tolls = len(cls.get_links_by_toll_type("O"))
        closed_tolls = len(cls.get_links_by_toll_type("F"))
        
        return {
            'available': True,
            'toll_stations': len(cls.get_toll_stations()),
            'complete_links': len(cls.get_complete_motorway_links()),
            'links_with_tolls': len(links_with_tolls),
            'entry_links': len(entry_links),
            'exit_links': len(exit_links),
            'toll_types': {
                'open_tolls': open_tolls,
                'closed_tolls': closed_tolls
            },
            'operators': operators_stats,
            'cache_efficiency': cls._cache_manager.get_linking_statistics() if cls._cache_manager else None
        }
    
    @classmethod
    def force_rebuild_cache(cls) -> bool:
        """
        Force la reconstruction du cache (utile pour tests).
        
        Returns:
            True si la reconstruction a réussi
        """
        try:
            if cls._cache_manager:
                success = cls._cache_manager.force_rebuild_links()
                if success:
                    print("✅ Cache V2 reconstruit avec succès")
                return success
            return False
        except Exception as e:
            print(f"❌ Erreur reconstruction cache: {e}")
            return False
