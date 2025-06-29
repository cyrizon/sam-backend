"""
Budget Toll Selector
===================

Sélecteur de péages optimisé par budget.
Orchestrateur principal utilisant les modules spécialisés.
"""

from typing import List, Dict, Optional
from .budget_optimizer import BudgetOptimizer
from ...utils.cache_accessor import CacheAccessor
from .budget_optimizer import BudgetOptimizer


class BudgetTollSelector:
    """
    Sélecteur de péages par budget.
    Responsabilité : Orchestration de la sélection par budget.
    """
    
    def __init__(self):
        """Initialise le sélecteur par budget."""
        self.optimizer = BudgetOptimizer()
        print("💰 Budget Toll Selector initialisé")
    
    def select_tolls_by_budget(
        self, 
        tolls_on_route: List[Dict], 
        budget_limit: float,
        route_coordinates: List[List[float]]
    ) -> Optional[Dict]:
        """
        Sélectionne les péages pour respecter un budget donné.
        
        Args:
            tolls_on_route: Liste des péages sur la route
            budget_limit: Budget maximum en euros
            route_coordinates: Coordonnées de la route de base
            
        Returns:
            Résultat de sélection ou None si impossible
        """
        print(f"💰 Sélection par budget : {budget_limit}€")
        
        if not tolls_on_route:
            return self._create_result([], 0.0, "Aucun péage sur route")
        
        # Calculer le coût initial avec le cache
        initial_cost = self._calculate_total_cost(tolls_on_route)
        print(f"   Coût initial : {initial_cost:.2f}€")
        
        if initial_cost <= budget_limit:
            return self._create_result(
                tolls_on_route, initial_cost, 
                f"Budget respecté ({initial_cost:.2f}€ <= {budget_limit}€)"
            )
        
        # Optimisation nécessaire
        return self._optimize_for_budget(
            tolls_on_route, budget_limit, route_coordinates
        )
    
    def _optimize_for_budget(
        self, 
        tolls_on_route: List[Dict], 
        budget_limit: float,
        route_coordinates: List[List[float]]
    ) -> Optional[Dict]:
        """
        Optimise la liste de péages pour respecter le budget.
        
        Args:
            tolls_on_route: Péages de base
            budget_limit: Budget limite
            route_coordinates: Coordonnées de route
            
        Returns:
            Résultat optimisé
        """
        print("   🔄 Optimisation par budget...")
        
        # Séparer ouverts et fermés
        open_tolls = [t for t in tolls_on_route if t.get('toll_type') == 'ouvert']
        closed_tolls = [t for t in tolls_on_route if t.get('toll_type') == 'fermé']
        
        if not closed_tolls:
            # Que des ouverts, teste le coût
            cost = self._calculate_total_cost(open_tolls)
            if cost <= budget_limit:
                return self._create_result(open_tolls, cost, "Ouverts seulement")
            else:
                return self._create_no_toll_result("Budget dépassé même avec ouverts")
        
        # Cas spécial : 1 seul fermé → route sans péage
        if len(closed_tolls) == 1:
            return self._handle_single_closed_toll(open_tolls, budget_limit)
        
        # Optimisation des fermés avec l'optimiseur
        return self.optimizer.optimize_for_budget(
            open_tolls, closed_tolls, budget_limit, 
            route_coordinates
        )
    
    def _handle_single_closed_toll(
        self, 
        open_tolls: List[Dict], 
        budget_limit: float
    ) -> Dict:
        """
        Gère le cas d'un seul péage fermé (règle des systèmes fermés).
        
        Args:
            open_tolls: Péages ouverts
            budget_limit: Budget limite
            
        Returns:
            Résultat approprié
        """
        if open_tolls:
            # Tester si les ouverts respectent le budget
            cost = self._calculate_total_cost(open_tolls)
            if cost <= budget_limit:
                return self._create_result(
                    open_tolls, cost, 
                    "Ouverts seulement (fermé isolé évité)"
                )
        
        # Sinon route sans péage
        return self._create_no_toll_result("Fermé isolé → route sans péage")
    
    def _create_result(
        self, 
        selected_tolls: List[Dict], 
        total_cost: float, 
        reason: str
    ) -> Dict:
        """
        Crée un résultat de sélection.
        
        Args:
            selected_tolls: Péages sélectionnés
            total_cost: Coût total
            reason: Raison de la sélection
            
        Returns:
            Dictionnaire de résultat
        """
        return {
            'selection_valid': True,
            'selected_tolls': selected_tolls,
            'total_cost': total_cost,
            'selection_reason': reason,
            'optimization_applied': len(selected_tolls) > 0
        }
    
    def _create_no_toll_result(self, reason: str) -> Dict:
        """
        Crée un résultat "route sans péage".
        
        Args:
            reason: Raison du choix
            
        Returns:
            Résultat sans péage
        """
        return {
            'selection_valid': True,
            'selected_tolls': [],
            'total_cost': 0.0,
            'selection_reason': f"Route sans péage : {reason}",
            'optimization_applied': True
        }

    def _calculate_total_cost(self, tolls: List[Dict]) -> float:
        """
        Calcule le coût total d'une liste de péages.
        
        Args:
            tolls: Liste des péages
            
        Returns:
            Coût total en euros
        """
        total_cost = 0.0
        
        for toll in tolls:
            try:
                # Utiliser le coût estimé s'il existe
                if 'estimated_cost' in toll:
                    total_cost += toll['estimated_cost']
                else:
                    # Utiliser le CacheAccessor pour calculer le coût
                    toll_cost = CacheAccessor.calculate_toll_cost(
                        toll, vehicle_category="1"
                    )
                    total_cost += toll_cost
                    
            except Exception as e:
                print(f"   ⚠️ Erreur calcul coût péage {toll.get('name', 'Inconnu')}: {e}")
                # Coût par défaut si erreur
                total_cost += 3.0
        
        return total_cost
