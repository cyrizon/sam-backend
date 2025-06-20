"""
intelligent_segmentation_strategy_v2.py
--------------------------------------

Implémentation simplifiée de l'algorithme de segmentation intelligente.
Basé sur l'analyse de la route de base et la segmentation aux points de sortie.

Algorithme en 9 étapes :
1. Route de base
2. Identifier péages SUR la route
3. Sélectionner X péages (prioriser système ouvert)
4. Trouver dernière sortie avant péage suivant
5. Récupérer motorway_link associé
6. Segmenter en 2 trajets
7. Requête segment 1 (avec péages) + segment 2 (sans péages)
8. Assembler les trajets (enlever point dupliqué)
9. Retourner le résultat
"""

from typing import List, Dict, Optional
from .toll_segment_builder import TollSegmentBuilder
from .segment_route_calculator import SegmentRouteCalculator
from .osm_data_parser import OSMDataParser
from .toll_matcher import TollMatcher, MatchedToll, convert_osm_tolls_to_matched_format
from .toll_deduplicator import TollDeduplicator
from .intelligent_segmentation_helpers import SegmentationSpecialCases, RouteUtils
from .segmentation_point_finder import SegmentationPointFinder
from .segment_calculator import SegmentCalculator
from .route_assembler import RouteAssembler
from .polyline_intersection import filter_tolls_on_route_strict
from benchmark.performance_tracker import performance_tracker


class IntelligentSegmentationStrategyV2:
    """
    Stratégie de segmentation intelligente simplifiée.
    Basée sur la route de base et la segmentation aux points de sortie.
    """
    
    def __init__(self, ors_service, osm_data_file: str):
        """
        Initialise la stratégie avec un service ORS et des données OSM.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
            osm_data_file: Chemin vers le fichier GeoJSON OSM
        """
        self.ors = ors_service
        self.osm_parser = OSMDataParser(osm_data_file)
        self.toll_matcher = TollMatcher()
        self.osm_loaded = False
        self.special_cases = SegmentationSpecialCases(ors_service)
        self.point_finder = SegmentationPointFinder(self.osm_parser)
        self.segment_calculator = SegmentCalculator(ors_service)
        self.route_assembler = RouteAssembler()
        
        # Nouveaux modules pour la segmentation intelligente
        self.segment_builder = TollSegmentBuilder(ors_service)
        self.route_calculator = SegmentRouteCalculator(ors_service)
    
    def find_route_with_exact_tolls(
        self, 
        coordinates: List[List[float]], 
        target_tolls: int
    ) -> Optional[Dict]:
        """
        Trouve une route avec exactement le nombre de péages demandé.
        Algorithme simplifié en 9 étapes basé sur la route de base.
        
        Args:
            coordinates: [départ, arrivée]
            target_tolls: Nombre exact de péages voulu
            
        Returns:
            dict: Route segmentée ou None si échec
        """
        with performance_tracker.measure_operation("intelligent_segmentation_v2"):
            print(f"🧠 Segmentation Intelligente V2 : {target_tolls} péage(s) exact(s)")
            
            # CAS SPÉCIAL 1 : 0 péage demandé → route sans péages directement
            if target_tolls == 0:
                print("🚫 Cas spécial : 0 péage demandé")
                return self.special_cases.get_toll_free_route(coordinates)
            
            # Étape 0 : Charger les données OSM si nécessaire
            if not self._ensure_osm_data_loaded():
                return None
            
            # Étape 1 : Récupérer la route de base
            base_route = self._get_base_route(coordinates)
            if not base_route:
                return None
            # Étape 2 : Identifier les péages SUR la route de base
            route_coords = RouteUtils.extract_route_coordinates(base_route)
            tolls_on_route = self._identify_tolls_on_base_route(route_coords)
              # CAS SPÉCIAL 2 : Plus de péages demandés que disponibles → retourner route de base
            if len(tolls_on_route) < target_tolls:
                print(f"⚠️ Pas assez de péages sur la route ({len(tolls_on_route)} < {target_tolls})")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # OPTIMISATION : Si le trajet de base a exactement le bon nombre de péages, on le retourne directement
            if len(tolls_on_route) == target_tolls:
                print(f"✅ Optimisation : trajet de base avec exactement {len(tolls_on_route)} péage(s) = {target_tolls} demandé(s)")
                return self.special_cases.format_base_route_as_result(base_route)            # Étape 3 : Sélectionner les péages à utiliser (prioriser système ouvert)
            selected_tolls = self._select_target_tolls(tolls_on_route, target_tolls)
            if not selected_tolls:
                return None            # Étape 4 : Construction des segments intelligents (nouvelle approche)
            print("🏗️ Étape 4 : Construction des segments intelligents...")
            segments = self.segment_builder.build_intelligent_segments(
                coordinates[0], coordinates[1], tolls_on_route, selected_tolls,
                osm_parser=self.osm_parser, route_coords=route_coords
            )
            if not segments:
                print("❌ Impossible de construire les segments intelligents")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 5 : Calcul des routes pour chaque segment
            print("📍 Étape 5 : Calcul des routes pour chaque segment...")
            segment_routes = self.route_calculator.calculate_all_segments(segments)
            if not segment_routes:
                print("❌ Échec du calcul des segments, fallback vers route de base")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 6 : Assembler et retourner le résultat final
            print("🔧 Étape 6 : Assemblage du résultat final...")
            return self.route_assembler.assemble_final_route_multi(
                segment_routes, target_tolls, selected_tolls
            )
    
    def _ensure_osm_data_loaded(self) -> bool:
        """Assure que les données OSM sont chargées."""
        if not self.osm_loaded:
            print("📁 Chargement des données OSM...")
            self.osm_loaded = self.osm_parser.load_and_parse()
        return self.osm_loaded
    
    def _get_base_route(self, coordinates: List[List[float]]) -> Optional[Dict]:
        """Étape 1 : Récupérer la route de base."""
        try:
            print(f"🛣️ Étape 1 : Route de base {coordinates[0]} → {coordinates[1]}")
            return self.ors.get_base_route(coordinates, include_tollways=True)
        except Exception as e:
            print(f"❌ Erreur route de base : {e}")
            return None

    def _identify_tolls_on_base_route(self, route_coords: List[List[float]]) -> List[MatchedToll]:
        """Étape 2 : Identifier les péages SUR la route de base avec détection stricte."""
        print("🔍 Étape 2 : Identification des péages sur la route...")        # Recherche large des péages proches SANS déduplication (pour avoir tous les candidats)
        osm_tolls_large = self.osm_parser.find_tolls_near_route(route_coords, max_distance_km=0.5)
        print(f"   📍 Détection large brute : {len(osm_tolls_large)} péages dans 500m")
        # Recherche stricte des péages vraiment SUR la route (intersection géométrique)
        tolls_on_route_strict = filter_tolls_on_route_strict(
            osm_tolls_large, 
            route_coords, 
            max_distance_m=1,  # 1m max de la polyline (ultra-strict pour éviter les péages côté opposé)
            coordinate_attr='coordinates'
        )
          # Extraire les péages de la détection stricte
        osm_tolls_strict = [toll_data[0] for toll_data in tolls_on_route_strict]
        print(f"   🎯 Détection stricte : {len(osm_tolls_strict)} péages vraiment sur la route (dans 1m)")
        
        # Convertir et matcher avec les données CSV (utiliser la détection stricte)
        osm_tolls_formatted = convert_osm_tolls_to_matched_format(osm_tolls_strict)
        matched_tolls = self.toll_matcher.match_osm_tolls_with_csv(
            osm_tolls_formatted, 
            max_distance_km=2.0
        )
        
        # Déduplication par proximité à la route (éliminer les doublons des portes de péage)
        deduplicated_tolls = TollDeduplicator.deduplicate_tolls_by_proximity(matched_tolls, route_coords)
        
        # Ordonner les péages selon leur position sur la route
        ordered_tolls = TollDeduplicator.sort_tolls_by_route_position(deduplicated_tolls, route_coords)
        
        # Afficher les péages finaux ordonnés
        print(f"   📋 Péages finaux détectés sur la route :")
        for i, toll in enumerate(ordered_tolls, 1):
            system_type = "ouvert" if toll.is_open_system else "fermé"
            print(f"      {i}. {toll.effective_name} (système {system_type})")
        
        return ordered_tolls
    
    def _select_target_tolls(self, available_tolls: List[MatchedToll], target_count: int) -> List[MatchedToll]:
        """
        Étape 3 : Sélectionner les péages à utiliser en respectant les contraintes des systèmes.
        
        Règles :
        - 1 péage : Seulement système ouvert
        - 2 péages : Soit 2 ouverts, soit 2 fermés (pas de mixte)
        - 3+ péages : Combinaisons possibles, mais chaque fermé accompagné d'au moins un autre fermé
        """
        print(f"🎯 Étape 3 : Sélection de {target_count} péage(s) avec contraintes systèmes...")
        
        if target_count > len(available_tolls):
            print(f"❌ Pas assez de péages disponibles ({len(available_tolls)} < {target_count})")
            return []
        
        # Séparer les péages par système
        open_tolls = [t for t in available_tolls if t.is_open_system]
        closed_tolls = [t for t in available_tolls if not t.is_open_system]
        
        print(f"   📊 Disponibles : {len(open_tolls)} ouverts, {len(closed_tolls)} fermés")
        
        # Appliquer les règles selon le nombre demandé
        if target_count == 1:
            return self._select_one_toll(open_tolls, closed_tolls)
        elif target_count == 2:
            return self._select_two_tolls(open_tolls, closed_tolls)
        else:
            return self._select_multiple_tolls(open_tolls, closed_tolls, target_count)
    
    def _select_one_toll(self, open_tolls: List[MatchedToll], closed_tolls: List[MatchedToll]) -> List[MatchedToll]:
        """Règle : 1 péage = seulement système ouvert."""
        if open_tolls:
            selected = [open_tolls[0]]
            print(f"   ✅ 1 péage ouvert : {selected[0].effective_name}")
            return selected
        else:
            print(f"   ❌ Aucun péage ouvert disponible pour 1 péage")
            return []
    
    def _select_two_tolls(self, open_tolls: List[MatchedToll], closed_tolls: List[MatchedToll]) -> List[MatchedToll]:
        """Règle : 2 péages = soit 2 ouverts, soit 2 fermés (pas de mixte)."""
        # Priorité : 2 ouverts
        if len(open_tolls) >= 2:
            selected = open_tolls[:2]
            print(f"   ✅ 2 péages ouverts : {[t.effective_name for t in selected]}")
            return selected
        
        # Sinon : 2 fermés
        if len(closed_tolls) >= 2:
            selected = closed_tolls[:2]
            print(f"   ✅ 2 péages fermés : {[t.effective_name for t in selected]}")
            return selected
        
        print(f"   ❌ Impossible de faire 2 péages (besoin de 2 ouverts ou 2 fermés)")
        return []
    
    def _select_multiple_tolls(self, open_tolls: List[MatchedToll], closed_tolls: List[MatchedToll], target_count: int) -> List[MatchedToll]:
        """Règle : 3+ péages = combinaisons possibles, mais chaque fermé accompagné d'au moins un autre fermé."""
        selected_tolls = []
        
        # Stratégie : Prendre d'abord les ouverts, puis des paires de fermés
        # Ajouter tous les ouverts disponibles
        selected_tolls.extend(open_tolls)
        remaining = target_count - len(selected_tolls)
        
        if remaining <= 0:
            # Assez d'ouverts, prendre seulement ce qu'il faut
            selected_tolls = open_tolls[:target_count]
            print(f"   ✅ {target_count} péages ouverts : {[t.effective_name for t in selected_tolls]}")
            return selected_tolls
        
        # Il faut ajouter des fermés - s'assurer qu'on en prend au moins 2
        if remaining == 1 and len(closed_tolls) >= 2:
            # Prendre 2 fermés au lieu d'1 pour respecter la contrainte
            if len(selected_tolls) > 0:
                # Enlever 1 ouvert et ajouter 2 fermés
                selected_tolls = selected_tolls[:-1]
                selected_tolls.extend(closed_tolls[:2])
            else:
                selected_tolls.extend(closed_tolls[:2])
        else:
            # Ajouter les fermés nécessaires (par paires si possible)
            selected_tolls.extend(closed_tolls[:remaining])
        
        # Vérifier qu'on respecte la contrainte des fermés
        final_selected = selected_tolls[:target_count]
        closed_count = sum(1 for t in final_selected if not t.is_open_system)
        
        if closed_count == 1:
            print(f"   ⚠️ Contrainte violée : 1 seul fermé détecté, ajustement nécessaire")
            # Réessayer avec une stratégie différente
            if len(closed_tolls) >= 2:
                # Remplacer par 2 fermés
                open_in_selection = [t for t in final_selected if t.is_open_system]
                if len(open_in_selection) > 0:
                    final_selected = open_in_selection[:-1] + closed_tolls[:2]
                else:
                    final_selected = closed_tolls[:target_count]
        
        print(f"   ✅ {len(final_selected)} péages sélectionnés : {[t.effective_name for t in final_selected]}")
        return final_selected[:target_count]
