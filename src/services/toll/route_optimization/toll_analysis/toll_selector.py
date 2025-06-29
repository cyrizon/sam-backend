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
            step1_result['selected_tolls'],  # Passer aussi les péages sélectionnés comme fallback
            route_coords[0],  # départ
            route_coords[1]   # arrivée
        )
        
        result = {
            'selection_valid': True,
            'selected_tolls': step1_result['selected_tolls'],  # Utiliser les péages sélectionnés, pas les optimisés
            'optimized_elements': optimized_elements,  # Garder les éléments optimisés séparément
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
        Règles de suppression :
        1. Toujours essayer de supprimer les péages fermés en premier
        2. Ne supprimer les péages ouverts que si pas assez de fermés disponibles
        3. Ne jamais laisser un seul péage fermé isolé (minimum 2 fermés ou 0)
        
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
        
        # Analyser la composition des péages
        closed_tolls = []
        open_tolls = []
        
        for i, toll in enumerate(tolls_on_route):
            toll_type = self._extract_toll_type(toll)
            if toll_type == 'fermé':
                closed_tolls.append((i, toll))
            else:
                open_tolls.append((i, toll))
        
        print(f"   🔒 Péages fermés: {len(closed_tolls)}")
        print(f"   🔓 Péages ouverts: {len(open_tolls)}")
        
        # Calculer combien supprimer
        to_remove_count = len(tolls_on_route) - target_count
        print(f"   ➖ À supprimer: {to_remove_count} péages")
        
        # Planifier la suppression selon les règles
        removal_plan = self._plan_toll_removal(closed_tolls, open_tolls, to_remove_count, target_count)
        
        if not removal_plan['valid']:
            print(f"   ⚠️ {removal_plan['reason']} → route sans péage")
            return {
                'selection_valid': False,
                'selected_tolls': [],
                'removed_tolls': tolls_on_route.copy(),
                'reason': removal_plan['reason']
            }
        
        # Exécuter le plan de suppression
        remaining_tolls = tolls_on_route.copy()
        removed_tolls = []
        
        # Supprimer dans l'ordre du plan
        for toll_to_remove in removal_plan['tolls_to_remove']:
            remaining_tolls.remove(toll_to_remove)
            removed_tolls.append(toll_to_remove)
            
            toll_name = self._extract_toll_name(toll_to_remove)
            toll_type = self._extract_toll_type(toll_to_remove)
            print(f"   ❌ Supprimé: {toll_name} ({toll_type})")
        
        print(f"   ✅ Péages conservés: {len(remaining_tolls)}")
        return {
            'selection_valid': True,
            'selected_tolls': remaining_tolls,
            'removed_tolls': removed_tolls,
            'reason': f"Sélection de {len(remaining_tolls)} péages"
        }
    
    def _plan_toll_removal(self, closed_tolls: List, open_tolls: List, to_remove_count: int, target_count: int) -> Dict:
        """
        Planifie la suppression des péages selon les règles strictes :
        1. Priorité aux péages fermés
        2. Jamais un seul péage fermé isolé
        3. Se rabattre sur les ouverts si nécessaire
        
        Args:
            closed_tolls: Liste des péages fermés [(index, toll), ...]
            open_tolls: Liste des péages ouverts [(index, toll), ...]
            to_remove_count: Nombre de péages à supprimer
            target_count: Nombre final de péages souhaité
            
        Returns:
            Plan de suppression avec validation
        """
        print(f"   🎯 Planification suppression: {to_remove_count} péages à retirer")
        
        tolls_to_remove = []
        closed_count = len(closed_tolls)
        open_count = len(open_tolls)
        
        # Cas 1: Si on a que des fermés ou que des ouverts
        if closed_count == 0:
            # Que des ouverts, suppression simple
            print("   📋 Que des péages ouverts → suppression directe")
            tolls_to_remove = [toll for _, toll in open_tolls[:to_remove_count]]
            
        elif open_count == 0:
            # Que des fermés, vérifier la règle d'isolement
            remaining_closed = closed_count - to_remove_count
            if remaining_closed == 1:
                print("   ⚠️ Suppression laisserait 1 seul fermé → invalide")
                return {
                    'valid': False,
                    'reason': "Suppression laisserait un péage fermé isolé",
                    'tolls_to_remove': []
                }
            else:
                print(f"   📋 Que des fermés, {remaining_closed} resteront → valide")
                tolls_to_remove = [toll for _, toll in closed_tolls[:to_remove_count]]
        
        else:
            # Cas mixte : fermés + ouverts
            print("   📋 Péages mixtes → stratégie avancée")
            
            # Stratégie : supprimer d'abord les fermés, mais vérifier la règle d'isolement
            max_closed_removable = closed_count
            
            # Si on enlève tous les fermés sauf 1, c'est interdit
            if closed_count > 1 and (closed_count - to_remove_count) == 1:
                # Il faut soit enlever tous les fermés, soit en laisser au moins 2
                if to_remove_count >= closed_count:
                    # On peut enlever tous les fermés + des ouverts
                    closed_to_remove = closed_count
                    open_to_remove = to_remove_count - closed_count
                    print(f"   🔄 Enlever tous les fermés ({closed_to_remove}) + {open_to_remove} ouverts")
                else:
                    # On ne peut pas enlever que des fermés, il faut adapter
                    # Option 1: enlever tous les fermés si possible
                    if closed_count <= to_remove_count:
                        closed_to_remove = closed_count
                        open_to_remove = to_remove_count - closed_count
                        print(f"   🔄 Solution: tous fermés ({closed_to_remove}) + {open_to_remove} ouverts")
                    else:
                        # Option 2: enlever des fermés mais en laisser au moins 2
                        closed_to_remove = max(0, closed_count - 2)
                        open_to_remove = to_remove_count - closed_to_remove
                        if open_to_remove < 0:
                            print("   ⚠️ Impossible de respecter les contraintes")
                            return {
                                'valid': False,
                                'reason': "Impossible de respecter la règle du péage fermé isolé",
                                'tolls_to_remove': []
                            }
                        print(f"   🔄 Solution: {closed_to_remove} fermés + {open_to_remove} ouverts (garde 2+ fermés)")
                
                tolls_to_remove.extend([toll for _, toll in closed_tolls[:closed_to_remove]])
                tolls_to_remove.extend([toll for _, toll in open_tolls[:open_to_remove]])
            
            else:
                # Cas normal : on peut enlever des fermés sans problème d'isolement
                closed_to_remove = min(to_remove_count, closed_count)
                open_to_remove = to_remove_count - closed_to_remove
                
                print(f"   ✅ Suppression normale: {closed_to_remove} fermés + {open_to_remove} ouverts")
                
                tolls_to_remove.extend([toll for _, toll in closed_tolls[:closed_to_remove]])
                if open_to_remove > 0:
                    tolls_to_remove.extend([toll for _, toll in open_tolls[:open_to_remove]])
        
        print(f"   📋 Plan validé: {len(tolls_to_remove)} péages à supprimer")
        return {
            'valid': True,
            'tolls_to_remove': tolls_to_remove,
            'reason': "Plan de suppression validé"
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
            print(toll)
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
        selected_tolls: List,  # Nouveau paramètre
        start_point: List[float], 
        end_point: List[float]
    ) -> List[Dict]:
        """
        Crée la structure simple de segments selon la logique :
        - Si des éléments optimisés existent, les utiliser
        - Sinon, utiliser les péages sélectionnés comme fallback
        
        Args:
            selected_elements: Éléments optimisés (TollBoothStation, CompleteMotorwayLink)
            selected_tolls: Péages sélectionnés (fallback si selected_elements est vide)
            start_point: Point de départ [lon, lat]
            end_point: Point d'arrivée [lon, lat]
            
        Returns:
            Liste de segments [start->end, avec/sans péage]
        """
        print(f"   📋 Création structure : {len(selected_elements)} éléments optimisés")
        print(f"   📋 Debug: {len(selected_tolls)} péages sélectionnés en fallback")
        
        # Si pas d'éléments optimisés mais des péages sélectionnés, créer un segment simple avec péages
        if not selected_elements and selected_tolls:
            print(f"   🔄 Fallback: utiliser {len(selected_tolls)} péages sélectionnés")
            return self._create_simple_segment_with_selected_tolls(selected_tolls, start_point, end_point)
        elif not selected_elements and not selected_tolls:
            print(f"   ⚠️ Aucun élément optimisé ET aucun péage sélectionné - segment sans péage")
        
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
                # Sortie → trajet AVEC péage jusqu'à la fin de la sortie (on roule sur autoroute puis on sort)
                exit_end = element.get_end_point()
                segments.append({
                    'start_point': current_point,
                    'end_point': exit_end,
                    'has_toll': True,
                    'toll_info': element,
                    'segment_reason': f'Sur autoroute vers sortie {element.link_id}'
                })
                current_point = exit_end
                
            elif element_type == 'CompleteMotorwayLink_ENTRY':
                # Entrée → trajet SANS péage jusqu'au début de l'entrée (hors autoroute)
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
            
            # Logique corrigée :
            # - Si le dernier élément est une ENTRÉE, on continue AVEC péages (on a rejoint l'autoroute)
            # - Si c'est un péage normal, on continue AVEC péages aussi  
            # - Si c'est une SORTIE, on continue SANS péages (on a quitté l'autoroute)
            has_toll = last_type in ['CompleteMotorwayLink_ENTRY', 'TollBoothStation']
            
            # Spécial : si c'est une sortie, le segment final est SANS péages
            if last_type == 'CompleteMotorwayLink_EXIT':
                has_toll = False
            
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
    
    def _extract_toll_name(self, toll_data) -> str:
        """Extrait le nom d'un péage depuis sa structure (Shapely ou dict)."""
        if isinstance(toll_data, dict):
            # Format Shapely: {'toll': TollBoothStation, ...}
            if 'toll' in toll_data:
                toll_station = toll_data['toll']
                return getattr(toll_station, 'display_name', getattr(toll_station, 'nom', 'Inconnu'))
            # Format dict direct
            return toll_data.get('name', toll_data.get('nom', 'Inconnu'))
        else:
            # Objet TollBoothStation direct
            return getattr(toll_data, 'display_name', getattr(toll_data, 'nom', 'Inconnu'))
    
    def _extract_toll_type(self, toll_data) -> str:
        """Extrait le type d'un péage depuis sa structure (Shapely ou dict)."""
        if isinstance(toll_data, dict):
            # Format Shapely: {'toll': TollBoothStation, ...}
            if 'toll' in toll_data:
                toll_station = toll_data['toll']
                return 'ouvert' if getattr(toll_station, 'is_open_toll', False) else 'fermé'
            # Format dict direct
            return toll_data.get('toll_type', 'fermé')
        else:
            # Objet TollBoothStation direct
            return 'ouvert' if getattr(toll_data, 'is_open_toll', False) else 'fermé'
    
    def _extract_toll_station(self, toll_data):
        """Extrait l'objet TollBoothStation depuis sa structure."""
        if isinstance(toll_data, dict):
            # Format Shapely: {'toll': TollBoothStation, ...}
            if 'toll' in toll_data:
                return toll_data['toll']
            # Format dict direct - ne devrait pas arriver
            return toll_data
        else:
            # Objet TollBoothStation direct
            return toll_data
    
    def _create_simple_segment_with_selected_tolls(
        self, 
        selected_tolls: List, 
        start_point: List[float], 
        end_point: List[float]
    ) -> List[Dict]:
        """
        Crée un segment simple qui passe par les péages sélectionnés.
        
        Args:
            selected_tolls: Liste des péages sélectionnés
            start_point: Point de départ
            end_point: Point d'arrivée
            
        Returns:
            Segment unique avec waypoints des péages
        """
        # Extraire les coordonnées des péages sélectionnés
        toll_waypoints = []
        for i, toll in enumerate(selected_tolls):
            print(f"     🔍 Debug toll {i}: keys = {list(toll.keys())}")
            
            coords = None
            
            # Cas 1: Objet TollBoothStation dans toll['toll']
            if 'toll' in toll and hasattr(toll['toll'], 'get_coordinates'):
                coords = toll['toll'].get_coordinates()
                print(f"     📍 Coordonnées via get_coordinates(): {coords}")
            elif 'toll' in toll and hasattr(toll['toll'], 'coordinates'):
                coords = toll['toll'].coordinates
                print(f"     📍 Coordonnées via .coordinates: {coords}")
            # Cas 2: Coordonnées directes
            elif 'coordinates' in toll:
                coords = toll['coordinates']
                print(f"     📍 Coordonnées directes: {coords}")
            # Cas 3: Latitude/longitude séparés
            else:
                lat = toll.get('latitude') or toll.get('lat')
                lon = toll.get('longitude') or toll.get('lon') or toll.get('lng')
                if lat is not None and lon is not None:
                    coords = [float(lon), float(lat)]
                    print(f"     🔄 Coordonnées reconstruites: {coords}")
            
            if coords and len(coords) == 2:
                toll_waypoints.append(coords)
                print(f"     ✅ Waypoint ajouté: {coords}")
            else:
                print(f"     ❌ Pas de coordonnées trouvées pour toll {i}")
                # Debug supplémentaire
                if 'toll' in toll:
                    print(f"     🔍 Type toll['toll']: {type(toll['toll'])}")
                    if hasattr(toll['toll'], '__dict__'):
                        print(f"     🔍 Attributs toll['toll']: {vars(toll['toll'])}")
        
        # Créer le chemin : start -> péages -> end
        waypoints = [start_point] + toll_waypoints + [end_point]
        
        # Créer un segment unique qui passe par tous les péages
        segment = {
            'start_point': start_point,
            'end_point': end_point,
            'has_toll': True,
            'toll_info': {'selected_tolls': selected_tolls},
            'segment_reason': f'Segment avec {len(selected_tolls)} péages sélectionnés',
            'waypoints': waypoints,  # Points de passage obligatoires
            'force_tolls': toll_waypoints  # Forcer le passage par ces péages
        }
        
        print(f"     ✅ Segment créé avec {len(toll_waypoints)} waypoints de péages")
        return [segment]
