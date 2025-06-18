"""
advanced_toll_optimizer.py
-------------------------

Optimiseur avancé combinant l'analyse tollways et la segmentation intelligente.

Responsabilité : Choisir la meilleure stratégie selon le contexte et les données disponibles.
"""

import os
from typing import List, Dict, Optional
from .tollway_segmentation_strategy import TollwaySegmentationStrategy
from .intelligent_segmentation_strategy_v2 import IntelligentSegmentationStrategyV2
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.error_handler import TollErrorHandler
from benchmark.performance_tracker import performance_tracker


class AdvancedTollOptimizer:
    """
    Optimiseur avancé utilisant plusieurs stratégies :
    1. Analyse tollways (visualisation des segments)
    2. Segmentation intelligente (algorithme 9 étapes avec OSM)
    
    Choisit automatiquement la meilleure approche selon les données disponibles.
    """
    
    def __init__(self, ors_service, osm_data_file: str = None):
        """
        Initialise l'optimiseur avancé.
        
        Args:
            ors_service: Service ORS
            osm_data_file: Chemin vers les données OSM (optionnel)
        """
        self.ors = ors_service
        
        # Stratégie d'analyse (toujours disponible)
        self.tollway_strategy = TollwaySegmentationStrategy(ors_service)
        
        # Stratégie intelligente (si données OSM disponibles)
        self.intelligent_strategy = None
        if osm_data_file and os.path.exists(osm_data_file):
            self.intelligent_strategy = IntelligentSegmentationStrategyV2(ors_service, osm_data_file)
            print(f"🧠 Stratégie intelligente activée avec {osm_data_file}")
        else:
            print("⚠️ Stratégie intelligente non disponible (données OSM manquantes)")
    
    def optimize_route_with_exact_tolls(
        self,
        coordinates: List[List[float]],
        target_tolls: int,
        veh_class: str = Config.DEFAULT_VEH_CLASS,
        use_intelligent_strategy: bool = True
    ) -> Dict:
        """
        Optimise une route pour avoir exactement le nombre de péages demandé.
        
        Args:
            coordinates: [départ, arrivée]
            target_tolls: Nombre exact de péages voulu
            veh_class: Classe de véhicule
            use_intelligent_strategy: Si True, essaie la stratégie intelligente en premier
            
        Returns:
            dict: Résultat optimisé
        """
        TollErrorHandler.log_operation_start(
            "advanced_toll_optimizer",
            target_tolls=target_tolls,
            veh_class=veh_class
        )
        
        with performance_tracker.measure_operation("advanced_toll_optimizer", {
            "target_tolls": target_tolls,
            "veh_class": veh_class,
            "has_intelligent": self.intelligent_strategy is not None
        }):
            print(f"🚀 Optimiseur Avancé : {target_tolls} péage(s) exact(s)")
            
            # CAS SPÉCIAL 1 : 0 péage demandé → route sans péages directement 
            # (avant toute autre logique, comme dans la stratégie simple)
            if target_tolls == 0:
                print("🚫 Cas spécial : 0 péage demandé, route sans péages directe")
                try:
                    # Utiliser ORS avec la méthode spécifique pour éviter les péages
                    toll_free_route = self.ors.get_route_avoid_tollways(coordinates)
                    
                    if toll_free_route:
                        return self._format_toll_free_result(toll_free_route)
                    else:
                        return self._format_error_result("Impossible de trouver une route sans péages")
                        
                except Exception as e:
                    return self._format_error_result(f"Erreur route sans péages : {e}")
            
            # Stratégie 1 : Segmentation intelligente (si disponible et demandée)
            if use_intelligent_strategy and self.intelligent_strategy and target_tolls > 0:
                print("🧠 Tentative avec stratégie intelligente...")
                try:
                    intelligent_result = self.intelligent_strategy.find_route_with_exact_tolls(
                        coordinates, target_tolls
                    )
                    
                    if intelligent_result:
                        print("✅ Stratégie intelligente réussie !")
                        return self._format_intelligent_result(intelligent_result, target_tolls)
                    else:
                        print("⚠️ Stratégie intelligente échouée, fallback vers analyse...")
                        
                except Exception as e:
                    print(f"❌ Erreur stratégie intelligente : {e}")
                    print("🔄 Fallback vers analyse tollways...")
            
            # Stratégie 2 : Analyse tollways (fallback ou choix par défaut)
            print("🧩 Utilisation de l'analyse tollways...")
            try:
                analysis_result = self.tollway_strategy.analyze_route_tollways(coordinates)
                
                if analysis_result:
                    return self._format_analysis_result(analysis_result, target_tolls)
                else:
                    return self._format_error_result("Aucune stratégie n'a fonctionné")
                    
            except Exception as e:
                return self._format_error_result(f"Erreur analyse tollways : {e}")
    
    def analyze_route_only(self, coordinates: List[List[float]]) -> Dict:
        """
        Effectue uniquement une analyse des péages sans optimisation.
        
        Args:
            coordinates: [départ, arrivée]
            
        Returns:
            dict: Résultat d'analyse
        """
        print("🔍 Analyse simple des péages...")
        
        try:
            result = self.tollway_strategy.analyze_route_tollways(coordinates)
            if result:
                return self._format_analysis_result(result, None)
            else:
                return self._format_error_result("Échec de l'analyse")
                
        except Exception as e:
            return self._format_error_result(f"Erreur analyse : {e}")
    
    def _format_intelligent_result(self, result: Dict, target_tolls: int) -> Dict:
        """Formate le résultat de la stratégie intelligente."""
        return {
            "found_solution": "intelligent_success",
            "strategy_used": "intelligent_segmentation",
            "route": result['route'],
            "target_tolls": target_tolls,
            "segments": result.get('segments', {}),
            "distance": result.get('distance', 0),
            "duration": result.get('duration', 0),
            "respects_constraint": True
        }
    
    def _format_analysis_result(self, result: Dict, target_tolls: Optional[int]) -> Dict:
        """Formate le résultat de l'analyse tollways."""
        toll_count = result.get('toll_count', 0)
        
        if target_tolls is not None:
            status = "analysis_within_limit" if toll_count <= target_tolls else "analysis_exceeds_limit"
            respects_constraint = toll_count <= target_tolls
        else:
            status = "analysis_complete"
            respects_constraint = True
        
        return {
            "found_solution": status,
            "strategy_used": "tollway_analysis",
            "route": result['route'],
            "toll_count": toll_count,
            "toll_segments": result.get('toll_segments', []),
            "cost_summary": result.get('cost_summary', {}),            
            "target_tolls": target_tolls,
            "respects_constraint": respects_constraint,
            "distance": result.get('distance', 0),
            "toll_free_alternatives": result.get('toll_free_alternatives', [])
        }
    
    def _format_error_result(self, error_message: str) -> Dict:
        """Formate un résultat d'erreur."""
        return {
            "found_solution": "error",
            "strategy_used": "advanced_optimizer",
            "error": error_message
        }
    
    def _format_toll_free_result(self, route: Dict) -> Dict:
        """Formate le résultat d'une route sans péages."""
        return {
            "found_solution": "no_toll_success",
            "strategy_used": "toll_free_direct",
            "route": route,
            "toll_count": 0,
            "target_tolls": 0,
            "respects_constraint": True,
            "distance": self._extract_distance(route),            
            "duration": self._extract_duration(route)
        }
    
    def _extract_distance(self, route: Dict) -> float:
        """Extrait la distance d'une route."""
        try:
            return route['features'][0]['properties']['summary']['distance']
        except (KeyError, IndexError, TypeError):
            return 0.0
    
    def _extract_duration(self, route: Dict) -> float:
        """Extrait la durée d'une route."""
        try:
            return route['features'][0]['properties']['summary']['duration']
        except (KeyError, IndexError, TypeError):
            return 0.0


class TollOptimizerFactory:
    """
    Factory pour créer le bon optimiseur selon la configuration.
    """
    
    @staticmethod
    def create_optimizer(ors_service, config: Dict = None):
        """
        Crée l'optimiseur approprié selon la configuration.
        
        Args:
            ors_service: Service ORS
            config: Configuration optionnelle
            
        Returns:
            AdvancedTollOptimizer: Optimiseur configuré
        """
        config = config or {}
        
        # Chercher les données OSM
        osm_file_paths = [
            config.get('osm_data_file'),
            'data/osm_export.geojson',
            'data/export.geojson',
            os.path.join(os.path.dirname(__file__), '../../../data/osm_export.geojson')
        ]
        
        osm_file = None
        for path in osm_file_paths:
            if path and os.path.exists(path):
                osm_file = path
                break
        
        if osm_file:
            print(f"🗺️ Données OSM trouvées : {osm_file}")
        else:
            print("⚠️ Aucune donnée OSM trouvée, mode analyse uniquement")
        
        return AdvancedTollOptimizer(ors_service, osm_file)
