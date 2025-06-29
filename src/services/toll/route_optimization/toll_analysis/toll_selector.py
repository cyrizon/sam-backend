"""
Toll Selector
=============

Orchestrateur principal pour la sélection des péages selon différents critères.
ÉTAPE 5 de l'algorithme d'optimisation.
"""

from typing import List, Dict
from .removal import TollRemovalManager
from .optimization import TollOptimizer
from .utils import SingleTollSelector, SelectionResultBuilder


class TollSelector:
    """
    Sélecteur de péages optimisé et modulaire.
    Responsabilité : ÉTAPE 5 de l'algorithme d'optimisation.
    """
    
    def __init__(self):
        """Initialise le sélecteur de péages."""
        pass
    
    def select_tolls_by_count(
        self, 
        tolls_on_route: List, 
        target_count: int,
        identification_result: Dict
    ) -> Dict:
        """
        ÉTAPE 5a: Sélection par nombre maximum de péages.
        
        Nouvelle logique correcte :
        1. Phase suppression : supprimer tous les péages nécessaires
        2. Phase analyse : vérifier si des péages fermés ont été supprimés 
        3. Phase optimisation : si oui, optimiser le prochain péage fermé restant
        
        Args:
            tolls_on_route: Péages disponibles sur la route
            target_count: Nombre de péages souhaité
            identification_result: Résultat complet de l'identification
            
        Returns:
            Péages sélectionnés avec métadonnées
        """
        print(f"🎯 Étape 5a: Sélection par nombre ({target_count} péages)...")
        
        # Cas spécial : 1 péage uniquement
        if target_count == 1:
            return SingleTollSelector.select_single_open_toll(tolls_on_route)
        
        # Cas spécial : garder tous les péages
        if target_count >= len(tolls_on_route):
            return SelectionResultBuilder.create_selection_result(
                tolls_on_route, target_count, 'keep_all'
            )
        
        # Phase 1 : Suppression des péages depuis la fin
        remaining_tolls, removed_open, removed_closed = TollRemovalManager.remove_tolls_from_end(
            tolls_on_route, target_count
        )
        
        # Phase 2 : Analyse des suppressions
        if not removed_closed:
            # Aucun péage fermé supprimé → Pas d'optimisation nécessaire
            print("   ℹ️ Aucun péage fermé supprimé, pas d'optimisation nécessaire")
            final_tolls = remaining_tolls
        else:
            # Phase 3 : Optimisation des péages fermés supprimés
            print(f"   🔧 {len(removed_closed)} péage(s) fermé(s) supprimé(s) → Optimisation nécessaire")
            final_tolls = TollOptimizer.optimize_after_removal(
                remaining_tolls, removed_closed, identification_result
            )
        
        # Résultat final
        if final_tolls:
            print(f"✅ Sélection finale : {len(final_tolls)} péages")
            return SelectionResultBuilder.create_selection_result(
                final_tolls, target_count, 'removal_with_optimization'
            )
        else:
            print("⚠️ Aucun péage restant après suppression")
            return SelectionResultBuilder.create_empty_selection(target_count)
    
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
            Péages sélectionnés avec métadonnées
        """
        print(f"💰 Étape 5b: Sélection par budget ({target_budget}€)...")
        
        # TODO: Implémenter la logique de sélection par budget
        print("⚠️ Sélection par budget: À IMPLÉMENTER")
        
        return {
            'selected_tolls': [],
            'selection_method': 'budget_based',
            'selection_strategy': 'not_implemented',
            'target_budget': target_budget,
            'achieved_budget': 0.0,
            'selection_valid': False,
            'failure_reason': 'budget_selection_not_implemented',
            'updated_segments_mapping': {}
        }