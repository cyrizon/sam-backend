"""
Toll Selector V2
===============

Orchestrateur principal pour la sélection des péages selon différents critères.
ÉTAPE 5 de l'algorithme d'optimisation avec remplacement intelligent des péages fermés.
Version refactorisée et compacte.
"""

from typing import List, Dict, Optional
from .selection_core import TollSelectionCore
from .replacement.toll_replacement_engine import TollReplacementEngine
from .budget.budget_selector import BudgetTollSelector
from ..utils.cache_accessor import CacheAccessor


class TollSelector:
    """
    Sélecteur de péages optimisé et modulaire.
    Responsabilité : ÉTAPE 5 de l'algorithme d'optimisation.
    """
    
    def __init__(self):
        """Initialise le sélecteur de péages."""
        self.selection_core = TollSelectionCore()
        self.replacement_engine = TollReplacementEngine()
        self.budget_selector = BudgetTollSelector()
        print("🎯 Toll Selector V2 initialisé")
    
    def select_tolls_by_count(
        self, 
        tolls_on_route: List, 
        target_count: int,
        identification_result: Dict
    ) -> Dict:
        """
        ÉTAPE 5a: Sélection par nombre maximum de péages.
        
        Args:
            tolls_on_route: Péages disponibles sur la route
            target_count: Nombre de péages souhaité
            identification_result: Résultat complet de l'identification
            
        Returns:
            Péages sélectionnés avec métadonnées
        """
        print(f"🎯 Étape 5a: Sélection par nombre ({target_count} péages)...")
        
        # Étape 1: Sélection de base avec règles
        selection_result = self.selection_core.select_by_count_with_rules(
            tolls_on_route, target_count
        )
        
        if not selection_result.get('selection_valid'):
            return selection_result
        
        # Étape 2: Analyse pour optimisation
        route_coords = identification_result.get('route_info', {}).get('start_point', [])
        enhanced_result = self.selection_core.analyze_selection_for_optimization(
            selection_result, route_coords
        )
        
        # Étape 3: Optimisation si nécessaire
        if enhanced_result.get('needs_optimization'):
            return self._optimize_selection_with_replacement(enhanced_result, identification_result)
        
        print(f"   ✅ Sélection terminée : {enhanced_result['selection_count']} péages")
        return enhanced_result
    
    def select_tolls_by_budget(
        self, 
        tolls_on_route: List, 
        target_budget: float,
        identification_result: Dict
    ) -> Dict:
        """
        ÉTAPE 5b: Sélection par budget maximum.
        
        Args:
            tolls_on_route: Péages disponibles sur la route
            target_budget: Budget maximum en euros
            identification_result: Résultat complet de l'identification
            
        Returns:
            Péages sélectionnés respectant le budget
        """
        print(f"🎯 Étape 5b: Sélection par budget ({target_budget}€)...")
        
        # Utiliser le nouveau BudgetSelector avec cache V2
        route_coords = identification_result.get('route_coordinates', [])
        
        return self.budget_selector.select_tolls_by_budget(
            tolls_on_route, target_budget, route_coords
        )
    
    def _optimize_selection_with_replacement(
        self, 
        selection_result: Dict, 
        identification_result: Dict
    ) -> Dict:
        """Optimise la sélection en remplaçant les péages fermés sur route."""
        print("   🔄 Optimisation avec remplacement des péages fermés...")
        
        try:
            tolls_to_optimize = selection_result.get('tolls_to_optimize', [])
            route_coords = self._extract_route_coordinates(identification_result)
            
            # Remplacer chaque péage fermé sur route
            optimized_tolls = selection_result['selected_tolls'].copy()
            
            for toll_to_replace in tolls_to_optimize:
                replacement = self.replacement_engine.find_replacement_entry(
                    toll_to_replace, route_coords
                )
                
                if replacement:
                    # Remplacer dans la liste
                    optimized_tolls = [
                        replacement if t == toll_to_replace else t 
                        for t in optimized_tolls
                    ]
                    print(f"   ✅ Péage {toll_to_replace.get('name', 'Inconnu')} remplacé")
            
            # Mettre à jour le résultat
            selection_result['selected_tolls'] = optimized_tolls
            selection_result['optimization_applied'] = True
            selection_result['needs_optimization'] = False
            
            return selection_result
            
        except Exception as e:
            print(f"   ❌ Erreur optimisation : {e}")
            selection_result['optimization_applied'] = False
            return selection_result
    
    def _calculate_toll_costs(self, tolls_on_route: List) -> List[Dict]:
        """Calcule le coût de chaque péage en utilisant le cache V2."""
        tolls_with_costs = []
        
        for toll in tolls_on_route:
            try:
                # Utiliser le CacheAccessor pour calculer le coût
                toll_cost = 0.0  # Valeur par défaut
                
                # TODO: Implémenter calcul de coût réel avec le cache V2
                # toll_cost = CacheAccessor.calculate_toll_cost(toll, vehicle_category="1")
                
                tolls_with_costs.append({
                    **toll,
                    'estimated_cost': toll_cost
                })
                
            except Exception as e:
                print(f"   ⚠️ Erreur calcul coût pour {toll.get('name')}: {e}")
                tolls_with_costs.append({
                    **toll,
                    'estimated_cost': 0.0
                })
        
        return tolls_with_costs
    
    def _select_by_budget_optimization(
        self, 
        tolls_with_costs: List[Dict], 
        target_budget: float,
        identification_result: Dict
    ) -> Dict:
        """Sélectionne les péages optimaux pour le budget donné."""
        # Trier par rapport coût/valeur (à implémenter selon les critères métier)
        sorted_tolls = sorted(tolls_with_costs, key=lambda x: x.get('estimated_cost', 0))
        
        selected_tolls = []
        current_cost = 0.0
        
        for toll in sorted_tolls:
            toll_cost = toll.get('estimated_cost', 0)
            if current_cost + toll_cost <= target_budget:
                selected_tolls.append(toll)
                current_cost += toll_cost
            else:
                break
        
        return {
            'selection_valid': True,
            'selected_tolls': selected_tolls,
            'selection_count': len(selected_tolls),
            'total_cost': current_cost,
            'budget_used': f"{current_cost:.2f}€ / {target_budget}€",
            'selection_reason': f"Sélection optimisée par budget ({len(selected_tolls)} péages)"
        }
    
    def _extract_route_coordinates(self, identification_result: Dict) -> List[List[float]]:
        """Extrait les coordonnées de route du résultat d'identification."""
        route_info = identification_result.get('route_info', {})
        
        # Construire une route approximative avec start/end
        start = route_info.get('start_point', [0, 0])
        end = route_info.get('end_point', [0, 0])
        
        return [start, end]  # Route simplifiée
    
    def get_selection_stats(self) -> Dict:
        """Retourne les statistiques du sélecteur."""
        return {
            'selector_ready': True,
            'modules_loaded': {
                'selection_core': self.selection_core is not None,
                'replacement_engine': self.replacement_engine is not None
            }
        }
