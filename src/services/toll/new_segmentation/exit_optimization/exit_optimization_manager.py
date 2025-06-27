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
from src.services.toll.new_segmentation.exit_optimization.motorway_exit_finder import MotorwayExitFinder
from src.services.toll.new_segmentation.exit_optimization.exit_toll_detector import ExitTollDetector
from src.cache.models.matched_toll import MatchedToll
from src.cache.parsers.osm_parser import OSMParser, MotorwayJunction
from src.cache.parsers.toll_matcher import TollMatcher


class ExitOptimizationManager:
    """
    Gestionnaire principal pour l'optimisation des sorties d'autoroute.
    """
    
    def __init__(self, osm_data_parser: OSMParser, toll_matcher: TollMatcher, ors_service):
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
        route_destination: List[float],
        previous_toll: Optional[MatchedToll] = None,
        route_coords: Optional[List[List[float]]] = None
    ) -> Optional[MatchedToll]:
        """
        Optimise un péage en trouvant une sortie d'autoroute alternative.
        
        Args:
            target_toll: Le péage qu'on voudrait optimiser
            remaining_tolls: Les péages restants sur la route
            route_destination: Destination finale de la route
            previous_toll: Le péage précédent (pour délimiter le segment de recherche)
            route_coords: Coordonnées de la route complète
            
        Returns:
            Optional[MatchedToll]: Le péage optimisé, ou None si pas d'optimisation possible
        """
        print(f"   🎯 Optimisation de sortie pour : {target_toll.effective_name}")
        
        # 1. Vérifier si l'optimisation est nécessaire
        if not self._should_optimize(target_toll, remaining_tolls):
            return None
        
        # 2. Récupérer les coordonnées du péage cible et du péage précédent
        target_coords = self._get_toll_coordinates(target_toll)
        if not target_coords:
            print(f"   ❌ Impossible de récupérer les coordonnées de {target_toll.effective_name}")
            return None
          # 3. Utiliser les coordonnées pour créer un segment de recherche
        if previous_toll:
            prev_coords = self._get_toll_coordinates(previous_toll)
            if prev_coords and route_coords:
                print(f"   🎯 Recherche sur segment de route entre {previous_toll.effective_name} et {target_toll.effective_name}")
                # Chercher la dernière sortie AVANT le péage cible sur le segment
                exits = self._find_exits_on_route_segment(prev_coords, target_coords, route_coords)
            else:
                print(f"   ⚠️ Fallback: recherche autour du péage (prev_coords: {bool(prev_coords)}, route_coords: {bool(route_coords)})")
                # Fallback: chercher autour du péage cible
                exits = self.exit_finder.find_exits_near_point(target_coords, search_radius_km=1.0)
        else:
            print(f"   ⚠️ Pas de péage précédent, recherche autour du péage cible")
            # Pas de péage précédent, chercher autour du péage cible
            exits = self.exit_finder.find_exits_near_point(target_coords, search_radius_km=1.0)
        
        if not exits:
            print(f"   ⚠️ Aucune sortie d'autoroute trouvée sur le segment avant {target_toll.effective_name}")
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
            # IMPORTANT: Utiliser les coordonnées de la sortie réelle, pas du péage
            exit_coords = self.exit_finder.get_exit_link_last_point({'coordinates': closest_exit.coordinates})
            exit_toll.osm_coordinates = exit_coords
            print(f"   🎯 Coordonnées de sortie assignées au péage : {exit_coords}")
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
        # Utiliser le dernier point de la way motorway_link au lieu des coordonnées de la junction
        exit_coords = self.exit_finder.get_exit_link_last_point({'coordinates': exit_data.coordinates})
        print(f"   🎯 Point de sortie final utilisé : {exit_coords}")
        
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
        route_destination: List[float],
        route_coords: Optional[List[List[float]]] = None
    ) -> List[MatchedToll]:
        """
        Optimise uniquement le dernier péage sélectionné si nécessaire.
        
        Logic: L'optimisation n'est nécessaire que pour le dernier péage sélectionné,
        et seulement s'il y a des péages restants après lui sur la route.
        
        Args:
            selected_tolls: Les péages sélectionnés initialement
            all_tolls: Tous les péages disponibles sur la route
            route_destination: Destination finale
            
        Returns:
            List[MatchedToll]: Les péages optimisés
        """
        if len(selected_tolls) == 0:
            return selected_tolls
        
        print(f"🔍 Optimisation des sorties pour {len(selected_tolls)} péages...")
        
        # Ne considérer que le dernier péage sélectionné
        last_toll = selected_tolls[-1]
        remaining_tolls = self._get_remaining_tolls(last_toll, all_tolls)
        
        print(f"   📍 Dernier péage sélectionné : {last_toll.effective_name}")
        print(f"   📍 Péages restants après le dernier : {len(remaining_tolls)}")
        
        if len(remaining_tolls) == 0:
            print(f"   ✅ Aucun péage restant après le dernier - pas d'optimisation nécessaire")
            return selected_tolls
          # Vérifier si le dernier péage a déjà été optimisé
        if hasattr(last_toll, 'is_exit') and last_toll.is_exit:
            print(f"   ✅ Dernier péage déjà optimisé comme sortie - pas de re-optimisation")
            return selected_tolls
          # Vérifier si le dernier péage est un système fermé (condition pour optimisation)
        if last_toll.is_open_system:
            print(f"   ✅ Dernier péage est un système ouvert - pas d'optimisation nécessaire")
            return selected_tolls
        
        print(f"   🎯 Optimisation nécessaire pour le dernier péage (système fermé avec péages restants)")
        
        # Optimiser uniquement le dernier péage avec le péage précédent si disponible
        previous_toll = selected_tolls[-2] if len(selected_tolls) > 1 else None
        optimized_last_toll = self.optimize_toll_exit(
            last_toll, 
            remaining_tolls, 
            route_destination, 
            previous_toll, 
            route_coords
        )
        
        # Construire la liste finale
        optimized_tolls = selected_tolls[:-1]  # Tous sauf le dernier
        
        if optimized_last_toll:
            print(f"   🔄 Remplacement du dernier péage : {last_toll.effective_name} → {optimized_last_toll.effective_name}")
            optimized_tolls.append(optimized_last_toll)
        else:
            print(f"   ➡️ Dernier péage conservé : {last_toll.effective_name}")
            optimized_tolls.append(last_toll)
        
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
    
    def _find_exits_on_route_segment(
        self, 
        prev_coords: List[float], 
        target_coords: List[float], 
        route_coords: List[List[float]]
    ) -> List[MotorwayJunction]:
        """
        Trouve la dernière sortie avant le péage cible (pas sur tout le segment entre les péages).
        
        Args:
            prev_coords: Coordonnées du péage précédent (non utilisé maintenant)
            target_coords: Coordonnées du péage cible
            route_coords: Coordonnées complètes de la route
            
        Returns:
            List[MotorwayJunction]: Sorties trouvées avant le péage cible, ordonnées par position
        """
        print(f"   🔍 Recherche de sorties autour du péage cible {target_coords}")
        
        # Chercher les sorties autour du péage cible uniquement (dans 10km)
        exits_near_target = self.exit_finder.find_exits_near_point(target_coords, search_radius_km=10.0)
        
        if not exits_near_target:
            print(f"   ❌ Aucune sortie trouvée autour du péage cible")
            return []
        
        # Position du péage cible sur la route
        target_position = self._calculate_position_on_route(target_coords, route_coords)
        if target_position is None:
            print(f"   ❌ Impossible de déterminer la position du péage cible sur la route")
            return []
        
        # Analyser chaque sortie et garder seulement celles AVANT le péage cible
        exits_before_target = []
        for junction in exits_near_target:
            exit_position = self._calculate_position_on_route(junction.coordinates, route_coords)
            if exit_position is None:
                continue
            
            # Garder seulement les sorties AVANT le péage cible sur la route
            if exit_position < target_position:
                exits_before_target.append(junction)
                junction_name = junction.properties.get('name', 'sans nom')
                print(f"   ✅ Sortie avant péage : {junction_name} (pos: {exit_position:.1f} < {target_position:.1f})")
            else:
                junction_name = junction.properties.get('name', 'sans nom')
                print(f"   ❌ Sortie après péage : {junction_name} (pos: {exit_position:.1f} >= {target_position:.1f})")
        
        if not exits_before_target:
            print(f"   ❌ Aucune sortie trouvée AVANT le péage cible")
            return []
        
        # Trier par position décroissante pour avoir la dernière sortie avant le péage en premier
        exits_before_target.sort(key=lambda x: self._calculate_position_on_route(x.coordinates, route_coords), reverse=True)
        
        print(f"   📍 {len(exits_before_target)} sorties trouvées avant le péage cible")
        return exits_before_target
    
    def _calculate_position_on_route(self, point: List[float], route_coords: List[List[float]]) -> Optional[float]:
        """
        Calcule la position d'un point sur la route (distance cumulée depuis le début).
        
        Args:
            point: Coordonnées du point [lon, lat]
            route_coords: Coordonnées de la route complète
            
        Returns:
            Optional[float]: Position en km depuis le début de la route, ou None si échec
        """
        if not route_coords or len(route_coords) < 2:
            return None
            
        min_distance = float('inf')
        best_position = None
        
        cumulative_distance = 0.0
        
        for i in range(len(route_coords) - 1):
            # Distance du point à ce segment de route
            segment_start = route_coords[i]
            segment_end = route_coords[i + 1]
            
            # Distance du point au segment
            dist_to_segment = self._distance_point_to_segment(point, segment_start, segment_end)
            
            if dist_to_segment < min_distance:
                min_distance = dist_to_segment
                # Position approximative sur ce segment
                segment_length = self._calculate_distance(segment_start, segment_end)
                best_position = cumulative_distance + segment_length * 0.5  # Milieu du segment
            
            # Ajouter la distance de ce segment
            cumulative_distance += self._calculate_distance(segment_start, segment_end)
        
        return best_position if min_distance < 1.0 else None  # Seulement si à moins de 1km
    
    def _distance_point_to_segment(self, point: List[float], seg_start: List[float], seg_end: List[float]) -> float:
        """
        Calcule la distance d'un point à un segment de ligne.
        
        Args:
            point: Point [lon, lat]
            seg_start: Début du segment [lon, lat]
            seg_end: Fin du segment [lon, lat]
            
        Returns:
            float: Distance en km
        """
        # Simplification : distance au point le plus proche du segment
        dist_to_start = self._calculate_distance(point, seg_start)
        dist_to_end = self._calculate_distance(point, seg_end)
        return min(dist_to_start, dist_to_end)

    def _calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """Calcule la distance entre deux points en km."""
        from src.cache.utils.geographic_utils import calculate_distance
        return calculate_distance(point1, point2)
