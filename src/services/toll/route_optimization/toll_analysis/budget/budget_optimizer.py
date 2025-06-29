"""
Budget Optimizer
===============

Optimiseur de péages pour respecter un budget donné.
Responsabilité : logique d'optimisation et de remplacement.
"""

from typing import List, Dict, Optional, Any
from ..spatial.unified_spatial_manager import UnifiedSpatialIndexManager
from ...utils.cache_accessor import CacheAccessor


class BudgetOptimizer:
    """
    Optimiseur de péages par budget.
    Logique simple : remplace séquentiellement les péages fermés
    par les prochaines entrées disponibles sur la route.
    """
    
    def __init__(self):
        """Initialise l'optimiseur."""
        self.spatial_manager = UnifiedSpatialIndexManager()
    
    def optimize_for_budget(
        self, 
        open_tolls: List[Dict], 
        closed_tolls: List[Dict],
        budget_limit: float,
        route_coordinates: List[List[float]]
    ) -> Optional[Dict]:
        """
        Optimise les péages fermés pour respecter le budget.
        Stratégie simple : remplace séquentiellement les péages fermés
        par les prochaines entrées disponibles.
        
        Args:
            open_tolls: Péages ouverts
            closed_tolls: Péages fermés
            budget_limit: Budget limite
            route_coordinates: Coordonnées route
            
        Returns:
            Résultat optimisé
        """
        if not closed_tolls:
            # Pas de péages fermés à optimiser
            total_cost = CacheAccessor.calculate_total_cost(open_tolls)
            if total_cost <= budget_limit:
                return self._create_result(
                    open_tolls, total_cost, "Ouverts seulement"
                )
            else:
                return self._create_no_toll_result("Budget dépassé")
        
        print(f"   🎯 Optimisation budget : {len(closed_tolls)} péages fermés")
        
        # Récupérer les entrées de remplacement
        replacement_entries = self._get_replacement_entries(route_coordinates)
        
        if not replacement_entries:
            print("   ⚠️ Aucune entrée de remplacement trouvée")
            return self._test_open_only_fallback(
                open_tolls, budget_limit
            )
        
        # Stratégie progressive simple : essayer chaque entrée séquentiellement
        current_tolls = open_tolls + closed_tolls
        
        for i, replacement_entry in enumerate(replacement_entries):
            print(f"   🔄 Test entrée {i + 1}/{len(replacement_entries)}")
            
            # Remplacer le premier péage fermé par cette entrée
            new_tolls = self._replace_first_closed_toll(
                current_tolls, closed_tolls[0], replacement_entry
            )
            
            # Tester le coût
            new_cost = CacheAccessor.calculate_total_cost(new_tolls)
            print(f"     Coût avec entrée {i + 1} : {new_cost:.2f}€")
            
            if new_cost <= budget_limit:
                return self._create_result(
                    new_tolls, new_cost, 
                    f"Optimisé avec entrée séquentielle {i + 1}"
                )
            
            # Continuer avec cette liste pour la prochaine tentative
            current_tolls = new_tolls
        
        # Si toutes les optimisations échouent
        print("   ❌ Toutes les optimisations ont échoué")
        return self._test_open_only_fallback(open_tolls, budget_limit)
    
    def _get_replacement_entries(
        self, 
        route_coordinates: List[List[float]]
    ) -> List:
        """
        Récupère les entrées candidates pour remplacement.
        
        Args:
            route_coordinates: Coordonnées de la route
            
        Returns:
            Liste des entrées avec péages
        """
        # Récupérer les entrées le long de la route
        entries_along_route = self.spatial_manager.get_entries_along_route(
            route_coordinates, buffer_km=0.2
        )
        
        # Filtrer seulement celles avec péages
        entries_with_tolls = [
            entry for entry in entries_along_route 
            if entry.has_toll()
        ]
        
        print(f"   📍 Entrées de remplacement : {len(entries_with_tolls)} trouvées")
        return entries_with_tolls
    
    def _replace_first_closed_toll(
        self, 
        current_tolls: List[Dict], 
        closed_toll: Dict, 
        replacement_entry
    ) -> List[Dict]:
        """
        Remplace le premier péage fermé par une entrée de remplacement.
        Logique simple : remplacement direct 1:1.
        
        Args:
            current_tolls: Liste actuelle des péages
            closed_toll: Péage fermé à remplacer
            replacement_entry: Entrée de remplacement
            
        Returns:
            Nouvelle liste avec remplacement
        """
        new_tolls = []
        
        for toll in current_tolls:
            if toll == closed_toll:
                # Remplacer par l'entrée de remplacement
                new_tolls.append({
                    'toll_type': 'fermé',
                    'name': f"Entrée {replacement_entry.link_id}",
                    'coordinates': replacement_entry.get_start_point(),
                    'associated_toll': replacement_entry.associated_toll
                })
                print(f"     ✅ Remplacé par entrée {replacement_entry.link_id}")
            else:
                new_tolls.append(toll)
        
        return new_tolls
    
    def _test_open_only_fallback(
        self, 
        open_tolls: List[Dict], 
        budget_limit: float
    ) -> Optional[Dict]:
        """
        Test de fallback : garder seulement les ouverts.
        
        Args:
            open_tolls: Péages ouverts
            budget_limit: Budget limite
            
        Returns:
            Résultat ou route sans péage
        """
        if not open_tolls:
            return self._create_no_toll_result("Aucun péage ouvert disponible")
        
        cost = CacheAccessor.calculate_total_cost(open_tolls)
        
        if cost <= budget_limit:
            return self._create_result(
                open_tolls, cost, 
                "Fallback : ouverts seulement"
            )
        else:
            return self._create_no_toll_result("Budget dépassé même avec ouverts")
    
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
