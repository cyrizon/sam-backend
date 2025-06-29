"""
Toll Selection Core Logic
========================

Logique principale de sélection des péages avec règles des systèmes fermés.
Module dédié aux algorithmes de sélection.
"""

from typing import List, Dict, Optional


class TollSelectionCore:
    """Logique centrale de sélection des péages."""
    
    def __init__(self):
        """Initialise le module de sélection."""
        pass
    
    def select_by_count_with_rules(
        self, 
        tolls_on_route: List[Dict], 
        target_count: int
    ) -> Dict:
        """
        Sélectionne les péages par nombre en respectant les règles.
        
        Args:
            tolls_on_route: Liste des péages sur la route
            target_count: Nombre de péages souhaité
            
        Returns:
            Résultat de sélection avec métadonnées
        """
        if not self._validate_selection_input(tolls_on_route, target_count):
            return self._create_failed_result("Données d'entrée invalides")
        
        # Cas spéciaux
        if target_count == 0:
            return self._create_success_result([], "Aucun péage sélectionné")
        
        if target_count >= len(tolls_on_route):
            return self._create_success_result(tolls_on_route, "Tous les péages sélectionnés")
        
        # Sélection avec règles des systèmes fermés
        return self._select_with_closed_system_rules(tolls_on_route, target_count)
    
    def _validate_selection_input(self, tolls_on_route: List[Dict], target_count: int) -> bool:
        """Valide les données d'entrée pour la sélection."""
        if not tolls_on_route:
            return target_count == 0
        
        if target_count < 0:
            return False
        
        return True
    
    def _select_with_closed_system_rules(self, tolls_on_route: List[Dict], target_count: int) -> Dict:
        """Sélectionne en respectant les règles des systèmes fermés."""
        
        # Analyser les types de péages
        open_tolls = [t for t in tolls_on_route if t.get('toll_type') == 'ouvert']
        closed_tolls = [t for t in tolls_on_route if t.get('toll_type') == 'fermé']
        
        print(f"   📊 Analyse : {len(open_tolls)} ouverts, {len(closed_tolls)} fermés")
        
        # Cas spécial : 1 péage demandé avec que des fermés
        if target_count == 1 and len(open_tolls) == 0:
            print("   ⚠️ 1 péage demandé mais que des fermés → sélection impossible")
            return self._create_failed_result("1 péage fermé isolé interdit")
        
        # Stratégies de sélection
        if len(open_tolls) >= target_count:
            # Cas idéal : que des ouverts
            selected = open_tolls[:target_count]
            return self._create_success_result(selected, "Sélection que d'ouverts")
        
        # Sélection mixte nécessaire
        return self._select_mixed_tolls(open_tolls, closed_tolls, target_count)
    
    def _select_mixed_tolls(self, open_tolls: List[Dict], closed_tolls: List[Dict], target_count: int) -> Dict:
        """Sélectionne un mélange d'ouverts et fermés en respectant les règles."""
        
        # Prendre tous les ouverts disponibles
        selected = open_tolls.copy()
        remaining_slots = target_count - len(open_tolls)
        
        # Ajouter des fermés en respectant la règle (minimum 2 fermés)
        if remaining_slots == 1:
            # Ne peut pas ajouter qu'1 fermé → ajouter 2 ou aucun
            if len(closed_tolls) >= 2 and target_count < len(open_tolls) + len(closed_tolls):
                # Ajouter 2 fermés (dépasse target mais respecte règle)
                selected.extend(closed_tolls[:2])
                return self._create_success_result(
                    selected, 
                    f"Ajout de 2 fermés pour respecter la règle (target dépassé: {len(selected)})"
                )
            else:
                # Garder que les ouverts
                return self._create_success_result(selected, "Que des ouverts pour éviter fermé isolé")
        
        else:
            # Ajouter le nombre exact de fermés demandés
            available_closed = min(remaining_slots, len(closed_tolls))
            selected.extend(closed_tolls[:available_closed])
            
            return self._create_success_result(
                selected, 
                f"Sélection mixte : {len(open_tolls)} ouverts + {available_closed} fermés"
            )
    
    def _create_success_result(self, selected_tolls: List[Dict], reason: str) -> Dict:
        """Crée un résultat de sélection réussie."""
        
        # Statistiques
        open_count = sum(1 for t in selected_tolls if t.get('toll_type') == 'ouvert')
        closed_count = len(selected_tolls) - open_count
        
        return {
            'selection_valid': True,
            'selected_tolls': selected_tolls,
            'selection_count': len(selected_tolls),
            'selection_reason': reason,
            'statistics': {
                'open_tolls': open_count,
                'closed_tolls': closed_count,
                'total_selected': len(selected_tolls)
            },
            'needs_optimization': False  # Pas d'optimisation par défaut
        }
    
    def _create_failed_result(self, reason: str) -> Dict:
        """Crée un résultat de sélection échouée."""
        return {
            'selection_valid': False,
            'selected_tolls': [],
            'selection_count': 0,
            'selection_reason': reason,
            'statistics': {
                'open_tolls': 0,
                'closed_tolls': 0,
                'total_selected': 0
            }
        }
