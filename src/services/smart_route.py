"""
smart_route.py
--------------

Module principal de routage intelligent avec gestion des contraintes de péages et de budget.
Sert de point d'entrée et d'orchestration pour les différentes stratégies de routage.

Pipeline complet :
    1.  Appel ORS « rapid »  (tollways extra_info)
    2.  Locate → cost → sélection des péages à éviter
    3.  Construction MultiPolygon
    4.  2ᵉ appel ORS avec `options.avoid_polygons`
    5.  Retourne les meilleures solutions :
        • la moins chère
        • la plus rapide
        • la meilleure selon la contrainte
"""
from __future__ import annotations
from src.services.ors_service import ORSService
from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
from src.services.budget_strategies import BudgetRouteOptimizer

class SmartRouteService:
    """
    Service principal de routage intelligent.
    Ce service orchestre les différentes stratégies de routage pour fournir des itinéraires optimisés.
    """
    
    def __init__(self):
        """
        Initialise le service de routage intelligent avec les services nécessaires.
        """
        self.ors_service = ORSService()
        # Utiliser la stratégie intelligente V2 simplifiée
        self.intelligent_optimizer = IntelligentOptimizer(self.ors_service)
        self.budget_optimizer = BudgetRouteOptimizer(self.ors_service)
    
    def compute_route_with_toll_limit(
        self,
        coordinates: list,
        max_tolls: int,
        veh_class: str = "c1",
        max_comb_size: int = 2
    ):
        """
        Calcule un itinéraire avec une limite sur le nombre de péages.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        # DÉMARRER LA SESSION
        from benchmark.performance_tracker import performance_tracker
        session_id = performance_tracker.start_optimization_session(
            origin=f"{coordinates[0][1]:.3f},{coordinates[0][0]:.3f}",
            destination=f"{coordinates[1][1]:.3f},{coordinates[1][0]:.3f}",
            route_distance_km=0
        )
        
        try:
            result = self.intelligent_optimizer.find_optimized_route(
                coordinates = coordinates,
                target_tolls = max_tolls,
                optimization_mode = 'count',
                veh_class = veh_class
            )
            return result
        finally:
            # TERMINER LA SESSION - Le résumé sera automatiquement loggé
            performance_tracker.end_optimization_session(result if 'result' in locals() else {})
    
    def compute_route_with_budget_limit(
        self,
        coordinates: list,
        max_price: float = None,
        max_price_percent: float = None,
        veh_class: str = "c1",
        max_comb_size: int = 2
    ):
        """
        Calcule un itinéraire avec une contrainte de budget maximum.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_price: Prix maximum en euros (absolu)
            max_price_percent: Pourcentage du coût de base (0.8 = 80%)
            veh_class: Classe de véhicule
            max_comb_size: Taille maximale des combinaisons de péages à tester
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, status)
        """
        from benchmark.performance_tracker import performance_tracker
        session_id = performance_tracker.start_optimization_session(
            origin=f"{coordinates[0][1]:.3f},{coordinates[0][0]:.3f}",
            destination=f"{coordinates[1][1]:.3f},{coordinates[1][0]:.3f}",
            route_distance_km=0
        )
        
        try:
            result = self.intelligent_optimizer.find_optimized_route(
                coordinates = coordinates,
                target_budget = max_price,
                optimization_mode = 'budget',
                veh_class = veh_class
            )
            return result
        finally:
            # TERMINER LA SESSION - Le résumé sera automatiquement loggé
            performance_tracker.end_optimization_session(result if 'result' in locals() else {})

# Les fonctions wrapper ont été supprimées car elles ne sont plus nécessaires
# Le code utilisateur importe maintenant directement la classe SmartRouteService
