"""
exit_optimization_manager.py
----------------------------

Module orchestrateur pour l'optimisation des sorties d'autoroute.

Responsabilité unique :
- Coordonner la recherche de sorties d'autoroute optimales
- Gérer le processus de remplacement péage → sortie → nouveau péage
- Orchestrer les différents composants (finder, detector, etc.)
- Fournir une interface simple pour l'intégration

Architecture :
1. Détecter le besoin d'optimisation (système fermé + péages restants)
2. Trouver les sorties d'autoroute proches
3. Calculer une route test via la sortie
4. Détecter les nouveaux péages sur cette route
5. Valider et retourner le péage optimisé
"""

from typing import List, Optional
from .motorway_exit_finder import MotorwayExitFinder
from .exit_toll_detector import ExitTollDetector
from ..toll_matcher import MatchedToll
from ..osm_data_parser import OSMDataParser, MotorwayJunction
from ..toll_matcher import TollMatcher


class ExitOptimizationManager:
    """
    Gestionnaire principal pour l'optimisation des sorties d'autoroute.
    """
    
    def __init__(self, osm_data_parser: OSMDataParser, toll_matcher: TollMatcher, ors_service):
        """
        Initialise le gestionnaire avec les services nécessaires.
        
        Args:
            osm_data_parser: Parser pour accéder aux données OSM
            toll_matcher: Matcher pour identifier les péages
            ors_service: Service ORS pour calculer les routes
        """
        self.exit_finder = MotorwayExitFinder(osm_data_parser)
        self.toll_detector = ExitTollDetector(osm_data_parser, toll_matcher)
        self.ors = ors_service
    
    def optimize_toll_exit(
        self, 
        target_toll: MatchedToll, 
        remaining_tolls: List[MatchedToll],
        route_destination: List[float]
    ) -> Optional[MatchedToll]:
        """
        Optimise un péage en trouvant une sortie d'autoroute alternative.
        
        Args:
            target_toll: Le péage qu'on voudrait optimiser
            remaining_tolls: Les péages restants sur la route
            route_destination: Destination finale de la route
            
        Returns:
            Optional[MatchedToll]: Le péage optimisé, ou None si pas d'optimisation possible
        """
        print(f"   🎯 Optimisation de sortie pour : {target_toll.effective_name}")
        
        # 1. Vérifier si l'optimisation est nécessaire
        if not self._should_optimize(target_toll, remaining_tolls):
            return None
        
        # 2. Trouver les sorties d'autoroute proches
        target_coords = self._get_toll_coordinates(target_toll)
        if not target_coords:
            print(f"   ❌ Impossible de récupérer les coordonnées de {target_toll.effective_name}")
            return None
        
        exits = self.exit_finder.find_exits_near_point(target_coords, search_radius_km=1.0)
        if not exits:
            print(f"   ⚠️ Aucune sortie d'autoroute trouvée près de {target_toll.effective_name}")
            return None
        
        # 3. Tester la sortie la plus proche
        closest_exit = self.exit_finder.get_closest_exit(exits)
        if not closest_exit:
            return None
        
        # 4. Calculer une route via cette sortie
        exit_toll = self._test_exit_route(closest_exit, route_destination)
        if not exit_toll:
            print(f"   ❌ Aucun péage détecté sur la route via {closest_exit.properties.get('name', 'sortie inconnue')}")
            return None
        
        print(f"   🔍 Péage candidat trouvé : {exit_toll.effective_name}")
        # 5. Valider le remplacement
        if exit_toll and self.toll_detector.validate_exit_toll_replacement(target_toll, exit_toll):
            print(f"   ✅ Optimisation réussie : {target_toll.effective_name} → {exit_toll.effective_name}")
            # Marquer ce péage comme étant une sortie d'autoroute
            exit_toll.is_exit = True
            return exit_toll
        else:
            print(f"   ❌ Validation du remplacement échouée")
        
        return None
    
    def _should_optimize(self, target_toll: MatchedToll, remaining_tolls: List[MatchedToll]) -> bool:
        """
        Détermine si une optimisation est nécessaire.
        
        Args:
            target_toll: Le péage cible
            remaining_tolls: Les péages restants
            
        Returns:
            bool: True si l'optimisation est recommandée
        """
        # Vérifier que le péage cible est un système fermé
        if target_toll.is_open_system:
            return False
        
        # Vérifier qu'il y a des péages restants
        if not remaining_tolls:
            return False
        
        # Vérifier qu'il y a au moins un péage fermé dans les restants
        has_closed_remaining = any(not toll.is_open_system for toll in remaining_tolls)
        
        return has_closed_remaining
    
    def _get_toll_coordinates(self, toll: MatchedToll) -> Optional[List[float]]:
        """
        Récupère les coordonnées d'un péage (priorité OSM puis CSV).
        
        Args:
            toll: Le péage dont récupérer les coordonnées
            
        Returns:
            Optional[List[float]]: [longitude, latitude] ou None
        """
        if toll.osm_coordinates and len(toll.osm_coordinates) == 2:
            return toll.osm_coordinates
        elif toll.csv_coordinates and len(toll.csv_coordinates) == 2:
            return toll.csv_coordinates
        else:            return None

    def _test_exit_route(
        self, 
        exit_data: MotorwayJunction, 
        destination: List[float]
    ) -> Optional[MatchedToll]:
        """
        Teste une route via une sortie et détecte les péages.
        
        Args:
            exit_data: Données de la sortie d'autoroute
            destination: Destination finale
            
        Returns:
            Optional[MatchedToll]: Péage détecté sur la route de sortie
        """
        exit_coords = exit_data.coordinates
        if not exit_coords:
            return None
        
        try:
            # Calculer une route courte depuis la sortie vers la destination
            junction_name = exit_data.properties.get('name', 'inconnue')
            print(f"   🧪 Test route via sortie {junction_name}")
            print(f"       📍 Coordonnées sortie : {exit_coords}")
            print(f"       📍 Destination : {destination}")
              # Route de test courte (premier segment seulement)
            test_route = self.ors.get_base_route([exit_coords, destination], include_tollways=True)
            
            if not test_route:
                print(f"       ❌ Impossible de calculer la route via {junction_name}")
                return None
            
            # Extraire les coordonnées de la réponse GeoJSON
            route_coords = None
            if 'features' in test_route and len(test_route['features']) > 0:
                geometry = test_route['features'][0].get('geometry', {})
                route_coords = geometry.get('coordinates', [])
            elif 'coordinates' in test_route:
                # Fallback pour format simple
                route_coords = test_route['coordinates']
            
            if not route_coords:
                print(f"       ❌ Impossible d'extraire les coordonnées de la route via {junction_name}")
                return None
                
            print(f"       ✅ Route calculée : {len(route_coords)} points")
            print(f"       🔍 Recherche de péages sur cette route...")
            
            exit_toll = self.toll_detector.detect_tolls_on_exit_route(route_coords, exit_coords)
            
            if exit_toll:
                print(f"       ✅ Péage trouvé : {exit_toll.effective_name}")
            else:
                print(f"       ❌ Aucun péage détecté sur cette route")
            
            return exit_toll
            
        except Exception as e:
            print(f"   ⚠️ Erreur lors du test de route via sortie : {e}")
            return None
    
    def optimize_multiple_tolls(
        self, 
        selected_tolls: List[MatchedToll], 
        all_tolls: List[MatchedToll],
        route_destination: List[float]
    ) -> List[MatchedToll]:        
        """
        Optimise plusieurs péages en une seule opération.
        
        Args:
            selected_tolls: Les péages sélectionnés initialement
            all_tolls: Tous les péages disponibles sur la route
            route_destination: Destination finale
            
        Returns:
            List[MatchedToll]: Les péages optimisés
        """
        if len(selected_tolls) <= 1:
            return selected_tolls
        
        print(f"🔍 Optimisation des sorties pour {len(selected_tolls)} péages...")
        optimized_tolls = []
        
        for i, toll in enumerate(selected_tolls):
            print(f"   📍 Optimisation du péage {i+1}/{len(selected_tolls)} : {toll.effective_name}")
            
            # Calculer les péages restants après ce péage
            remaining_tolls = self._get_remaining_tolls(toll, all_tolls)
            print(f"      → {len(remaining_tolls)} péages restants après celui-ci")
            
            # Tenter l'optimisation
            optimized_toll = self.optimize_toll_exit(toll, remaining_tolls, route_destination)
            
            if optimized_toll:
                print(f"   🔄 Remplacement : {toll.effective_name} → {optimized_toll.effective_name}")
                optimized_tolls.append(optimized_toll)
            else:
                print(f"   ➡️ Péage conservé : {toll.effective_name}")
                optimized_tolls.append(toll)
        
        return optimized_tolls
    
    def _get_remaining_tolls(self, current_toll: MatchedToll, all_tolls: List[MatchedToll]) -> List[MatchedToll]:
        """
        Récupère les péages qui viennent après le péage courant sur la route.
        
        Args:
            current_toll: Le péage de référence
            all_tolls: Tous les péages ordonnés sur la route
            
        Returns:
            List[MatchedToll]: Les péages restants après le péage courant
        """
        try:
            current_index = all_tolls.index(current_toll)
            return all_tolls[current_index + 1:]
        except ValueError:
            # Si le péage n'est pas trouvé, retourner une liste vide
            return []
