"""
Toll Selector V2
===============

Orchestrateur principal pour la sélection des péages selon différents critères.
ÉTAPE 5 de l'algorithme d'optimisation avec remplacement intelligent des péages fermés.
Version refactorisée et compacte.
"""

from typing import List, Dict, Optional
from .selection_analyzer import SelectionAnalyzer
from .budget.budget_selector import BudgetTollSelector


class TollSelector:
    """
    Sélecteur de péages optimisé et modulaire.
    Responsabilité : ÉTAPE 5 de l'algorithme d'optimisation.
    """
    
    def __init__(self):
        """Initialise le sélecteur de péages."""
        self.selection_analyzer = SelectionAnalyzer()
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
        Process simplifié en 3 étapes:
        1. Suppression de péages pour respecter la demande (fermés d'abord)
        2. Optimisation avec entrées/sorties si nécessaire  
        3. Création structure segments
        
        Args:
            tolls_on_route: Péages disponibles sur la route
            target_count: Nombre de péages souhaité
            identification_result: Résultat complet de l'identification
            
        Returns:
            Structure avec segments [start->end, avec/sans péage]
        """
        print(f"🎯 Étape 5a: Sélection par nombre ({target_count} péages)...")
        
        # ÉTAPE 1: Suppression simple pour respecter la demande
        step1_result = self._remove_tolls_to_match_count(tolls_on_route, target_count)
        
        if not step1_result.get('selection_valid'):
            # Cas péage fermé isolé → route sans péage
            return self._create_no_toll_route_result(step1_result.get('reason', 'Sélection impossible'))
        
        # ÉTAPE 2: Optimisation avec entrées/sorties
        route_coords = self._extract_route_coordinates(identification_result)
        optimized_elements = self._optimize_with_motorway_links(
            step1_result['selected_tolls'], 
            step1_result['removed_tolls'],
            route_coords
        )
        
        # ÉTAPE 3: Création structure segments
        segments_structure = self._create_segments_structure(
            optimized_elements, 
            route_coords[0],  # départ
            route_coords[1]   # arrivée
        )
        
        result = {
            'selection_valid': True,
            'selected_tolls': optimized_elements,
            'selection_count': len([e for e in optimized_elements if hasattr(e, 'osm_id')]),
            'segments': segments_structure,
            'optimization_applied': True,
            'selection_reason': f"Sélection optimisée ({len(optimized_elements)} éléments)"
        }
        
        print(f"   ✅ Sélection terminée : {len(segments_structure)} segments créés")
        return result
    
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
    
    def _remove_tolls_to_match_count(self, tolls_on_route: List, target_count: int) -> Dict:
        """
        ÉTAPE 1: Supprime les péages pour respecter la demande.
        Enlève dans l'ordre de la route : fermés d'abord, puis ouverts.
        
        Args:
            tolls_on_route: Péages sur la route (dans l'ordre)
            target_count: Nombre de péages souhaité
            
        Returns:
            Résultat avec péages sélectionnés
        """
        print(f"   📊 Étape 1: Suppression pour respecter {target_count} péages")
        print(f"   📍 Péages disponibles: {len(tolls_on_route)}")
        
        # Cas spéciaux
        if target_count <= 0:
            return {
                'selection_valid': True,
                'selected_tolls': [],
                'removed_tolls': tolls_on_route.copy(),
                'reason': "0 péage demandé"
            }
        
        if target_count >= len(tolls_on_route):
            return {
                'selection_valid': True,
                'selected_tolls': tolls_on_route.copy(),
                'removed_tolls': [],
                'reason': "Tous les péages conservés"
            }
        
        # Calculer combien supprimer
        to_remove_count = len(tolls_on_route) - target_count
        print(f"   ➖ À supprimer: {to_remove_count} péages")
        
        # Créer des listes de travail
        remaining_tolls = tolls_on_route.copy()
        removed_tolls = []
        
        # Supprimer dans l'ordre : fermés d'abord, puis ouverts
        # Toujours prendre le PREMIER dans l'ordre de la route
        for _ in range(to_remove_count):
            if not remaining_tolls:
                break
                
            # Chercher le premier fermé
            toll_to_remove = None
            for toll in remaining_tolls:
                if toll.get('toll_type') == 'fermé':
                    toll_to_remove = toll
                    break
            
            # Si pas de fermé, prendre le premier ouvert
            if toll_to_remove is None:
                toll_to_remove = remaining_tolls[0]
            
            # Supprimer le péage
            remaining_tolls.remove(toll_to_remove)
            removed_tolls.append(toll_to_remove)
            print(f"   ❌ Supprimé: {toll_to_remove.get('name', 'Inconnu')} ({toll_to_remove.get('toll_type')})")
        
        # Vérifier la règle du péage fermé isolé
        closed_remaining = [t for t in remaining_tolls if t.get('toll_type') == 'fermé']
        if len(closed_remaining) == 1:
            print(f"   ⚠️ Péage fermé isolé détecté → route sans péage")
            return {
                'selection_valid': False,
                'selected_tolls': [],
                'removed_tolls': tolls_on_route.copy(),
                'reason': "Péage fermé isolé évité"
            }
        
        print(f"   ✅ Péages conservés: {len(remaining_tolls)}")
        return {
            'selection_valid': True,
            'selected_tolls': remaining_tolls,
            'removed_tolls': removed_tolls,
            'reason': f"Sélection de {len(remaining_tolls)} péages"
        }
    
    def _optimize_with_motorway_links(
        self, 
        selected_tolls: List, 
        removed_tolls: List,
        route_coords: List[List[float]]
    ) -> List:
        """
        ÉTAPE 2: Optimisation avec entrées/sorties d'autoroute.
        Optimise seulement le PREMIER péage fermé restant après suppression.
        
        Args:
            selected_tolls: Péages sélectionnés à l'étape 1
            removed_tolls: Péages supprimés à l'étape 1
            route_coords: Coordonnées de la route
            
        Returns:
            Liste d'éléments optimisés (TollBoothStation + CompleteMotorwayLink)
        """
        print(f"   🔄 Étape 2: Optimisation des éléments")
        optimized_elements = []
        
        # Convertir les péages sélectionnés en objets cache V2
        for toll in selected_tolls:
            cache_element = self.selection_analyzer._optimize_toll_element(toll, route_coords)
            if cache_element:
                optimized_elements.append(cache_element)
        
        # Optimiser le PREMIER péage fermé restant
        first_closed_toll = None
        for toll in selected_tolls:
            if toll.get('toll_type') == 'fermé':
                first_closed_toll = toll
                break
        
        if first_closed_toll:
            print(f"   🎯 Optimisation du premier fermé: {first_closed_toll.get('name', 'Inconnu')}")
            # Trouver une entrée proche pour remplacer ce péage fermé
            entry_link = self._find_optimization_entry(route_coords, first_closed_toll)
            if entry_link:
                # Remplacer le péage fermé par l'entrée optimisée
                optimized_elements = [e for e in optimized_elements 
                                    if not (hasattr(e, 'osm_id') and 
                                           e.osm_id == first_closed_toll.get('osm_id'))]
                optimized_elements.append(entry_link)
                print("   ✅ Péage fermé remplacé par entrée optimisée")
        
        print(f"   📝 Éléments optimisés: {len(optimized_elements)}")
        return optimized_elements
    
    def _check_if_optimization_needed(self, selected_tolls: List, removed_tolls: List) -> bool:
        """Vérifie si une optimisation avec entrée est nécessaire."""
        # Si on a supprimé un fermé et le suivant dans selected est aussi fermé
        for i, removed in enumerate(removed_tolls):
            if removed.get('toll_type') == 'fermé':
                # Chercher le péage suivant dans la sélection
                for selected in selected_tolls:
                    if selected.get('toll_type') == 'fermé':
                        return True
        return False
    
    def _find_optimization_entry(self, route_coords: List[List[float]], toll_to_optimize: Dict):
        """
        Trouve une entrée d'autoroute pour remplacer un péage fermé.
        
        Args:
            route_coords: Coordonnées de la route
            toll_to_optimize: Péage fermé à optimiser
            
        Returns:
            CompleteMotorwayLink d'entrée ou None
        """
        try:
            toll_coords = toll_to_optimize.get('coordinates', [])
            if not toll_coords:
                return None
            
            # Chercher des entrées proches du péage à optimiser
            for link in self.selection_analyzer.cache_manager.complete_motorway_links:
                if hasattr(link, 'link_type') and str(link.link_type) == 'LinkType.ENTRY':
                    distance = self.selection_analyzer._calculate_distance(
                        link.get_start_point(), toll_coords
                    )
                    if distance < 5.0:  # Dans un rayon de 5km
                        print(f"   🚪 Entrée trouvée: {link.link_id} à {distance:.1f}km")
                        return link
            
            print("   ⚠️ Aucune entrée proche trouvée")
            return None
            
        except Exception as e:
            print(f"   ❌ Erreur recherche entrée: {e}")
            return None
    
    def _create_no_toll_route_result(self, reason: str) -> Dict:
        """Crée un résultat pour une route sans péage."""
        return {
            'selection_valid': True,
            'selected_tolls': [],
            'selection_count': 0,
            'segments': [{
                'start_point': [0, 0],
                'end_point': [0, 0], 
                'has_toll': False,
                'toll_info': {},
                'segment_reason': 'Route sans péage'
            }],
            'optimization_applied': False,
            'selection_reason': f'Route sans péage : {reason}'
        }
    
    def _extract_route_coordinates(self, identification_result: Dict) -> List[List[float]]:
        """Extrait les coordonnées de route du résultat d'identification."""
        route_info = identification_result.get('route_info', {})
        
        # Construire une route approximative avec start/end
        start = route_info.get('start_point', [0, 0])
        end = route_info.get('end_point', [0, 0])
        
        return [start, end]  # Route simplifiée
    
    def _create_segments_structure(
        self, 
        selected_elements: List, 
        start_point: List[float], 
        end_point: List[float]
    ) -> List[Dict]:
        """
        Crée la structure simple de segments selon la logique :
        - EXIT → avec péage jusqu'à end_coordinates
        - Entre EXIT et ENTRY → sans péage
        - ENTRY → avec péage à partir de start_coordinates
        - TollBoothStation → toujours avec péage
        
        Args:
            selected_elements: Éléments optimisés (TollBoothStation, CompleteMotorwayLink)
            start_point: Point de départ [lon, lat]
            end_point: Point d'arrivée [lon, lat]
            
        Returns:
            Liste de segments [start->end, avec/sans péage]
        """
        print(f"   📋 Création structure : {len(selected_elements)} éléments optimisés")
        
        segments = []
        current_point = start_point
        
        for i, element in enumerate(selected_elements):
            element_type = self._get_element_type(element)
            element_coords = self._get_element_coordinates(element)
            
            print(f"     Element {i+1}: {element_type} à {element_coords}")
            
            if element_type == 'TollBoothStation':
                # Péage normal → trajet avec péage
                segments.append({
                    'start_point': current_point,
                    'end_point': element_coords,
                    'has_toll': True,
                    'toll_info': element,
                    'segment_reason': f'Vers péage {getattr(element, "name", "Inconnu")}'
                })
                current_point = element_coords
                
            elif element_type == 'CompleteMotorwayLink_EXIT':
                # Sortie → trajet avec péage jusqu'à la fin de la sortie
                exit_end = element.get_end_point()
                segments.append({
                    'start_point': current_point,
                    'end_point': exit_end,
                    'has_toll': True,
                    'toll_info': element,
                    'segment_reason': f'Sortie autoroute via {element.link_id}'
                })
                current_point = exit_end
                
            elif element_type == 'CompleteMotorwayLink_ENTRY':
                # Entrée → trajet sans péage jusqu'au début de l'entrée
                entry_start = element.get_start_point()
                segments.append({
                    'start_point': current_point,
                    'end_point': entry_start,
                    'has_toll': False,
                    'toll_info': {},
                    'segment_reason': f'Hors autoroute vers entrée {element.link_id}'
                })
                current_point = entry_start
        
        # Segment final vers l'arrivée
        if current_point != end_point:
            # Déterminer si le dernier segment a des péages
            last_element = selected_elements[-1] if selected_elements else None
            last_type = self._get_element_type(last_element) if last_element else None
            
            # Si le dernier élément est une entrée, on continue avec péage
            # Si c'est un péage normal, on continue avec péage aussi
            # Seule exception : si c'est une sortie, on évite les péages
            has_toll = last_type in ['CompleteMotorwayLink_ENTRY', 'TollBoothStation']
            
            segments.append({
                'start_point': current_point,
                'end_point': end_point,
                'has_toll': has_toll,
                'toll_info': last_element if has_toll else {},
                'segment_reason': 'Vers destination finale'
            })
        
        print(f"   ✅ {len(segments)} segments créés")
        for i, seg in enumerate(segments):
            toll_status = 'avec péage' if seg['has_toll'] else 'sans péage'
            print(f"     Segment {i+1}: {toll_status} - {seg['segment_reason']}")
        
        return segments
    
    def _get_element_type(self, element) -> str:
        """Détermine le type d'un élément sélectionné."""
        if element is None:
            return 'Unknown'
            
        # Vérifier si c'est un objet TollBoothStation
        if hasattr(element, 'osm_id') and hasattr(element, 'get_coordinates'):
            return 'TollBoothStation'
            
        # Vérifier si c'est un objet CompleteMotorwayLink
        if hasattr(element, 'link_type') and hasattr(element, 'get_start_point'):
            link_type = element.link_type
            if hasattr(link_type, 'name'):
                return f'CompleteMotorwayLink_{link_type.name}'
            else:
                return f'CompleteMotorwayLink_{str(link_type)}'
                
        # Dictionnaire legacy avec link_type
        if hasattr(element, 'link_type') and isinstance(element, dict):
            link_type = element.get('link_type', 'UNKNOWN')
            return f'CompleteMotorwayLink_{link_type}'
            
        # Dict legacy avec osm_id 
        if isinstance(element, dict) and 'osm_id' in element:
            return 'TollBoothStation'
            
        # Coordonnées simples ou autre
        return 'Coordinates'
    
    def _get_element_coordinates(self, element) -> List[float]:
        """Récupère les coordonnées d'un élément."""
        if element is None:
            return [0.0, 0.0]
            
        # Objet TollBoothStation
        if hasattr(element, 'get_coordinates'):
            return element.get_coordinates()
            
        # Objet CompleteMotorwayLink
        if hasattr(element, 'get_start_point'):
            return element.get_start_point()
            
        # Dict legacy avec coordinates
        if isinstance(element, dict) and 'coordinates' in element:
            return element['coordinates']
            
        # Liste de coordonnées directe
        if isinstance(element, list) and len(element) >= 2:
            return element[:2]  # Prendre les 2 premiers éléments
            
        # Fallback
        return [0.0, 0.0]
    
    def get_selection_stats(self) -> Dict:
        """Retourne les statistiques du sélecteur."""
        return {
            'selector_ready': True,
            'modules_loaded': {
                'selection_analyzer': self.selection_analyzer is not None,
                'budget_selector': self.budget_selector is not None
            }
        }
