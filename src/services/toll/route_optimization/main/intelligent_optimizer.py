"""
Intelligent Optimizer
=====================

Orchestrateur principal de l'optimisation d'itinéraires avec péages.
Architecture simplifiée et modulaire en 8 étapes.
"""

from typing import List, Dict, Optional
from ..route_handling.base_route_provider import BaseRouteProvider
from ..toll_analysis.toll_identifier import TollIdentifier
from ..toll_analysis.toll_selector import TollSelector
from ..segmentation.segment_creator import SegmentCreator
from ..segmentation.segment_calculator import SegmentCalculator
from ..assembly.route_assembler import RouteAssembler


class IntelligentOptimizer:
    """
    Optimiseur intelligent d'itinéraires avec péages.
    Orchestrateur des 8 étapes de l'algorithme simplifié.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """
        self.ors = ors_service
        
        # Initialisation des modules par étape
        self.route_provider = BaseRouteProvider(ors_service)         # Étapes 1-2
        self.toll_identifier = TollIdentifier()                      # Étape 3  
        self.toll_selector = TollSelector()                          # Étape 5
        self.segment_creator = SegmentCreator()                      # Étape 6
        self.segment_calculator = SegmentCalculator(ors_service)     # Étape 7
        self.route_assembler = RouteAssembler()                      # Étape 8
        
        print("🚀 Optimiseur intelligent initialisé")
    
    def find_optimized_route(
        self, 
        coordinates: List[List[float]], 
        target_tolls: int,
        optimization_mode: str = 'count'
    ) -> Optional[Dict]:
        """
        Trouve une route optimisée selon les critères demandés.
        
        Args:
            coordinates: [départ, arrivée]
            target_tolls: Nombre de péages souhaité (mode count) ou budget (mode budget)
            optimization_mode: 'count' ou 'budget'
            
        Returns:
            Route optimisée ou None si échec
        """
        print(f"🎯 Optimisation route: {target_tolls} {'péages' if optimization_mode == 'count' else '€'}")
        
        # Validation des entrées
        if not self._validate_inputs(coordinates, target_tolls, optimization_mode):
            return None
        
        try:
            print("Etape 1")
            # ÉTAPE 1: Route sans péage (cas spécial)
            if optimization_mode == 'count' and target_tolls == 0:
                return self._handle_zero_tolls(coordinates)
            
            # ÉTAPES 2-3: Route de base + identification péages
            route_data, identification_result = self._analyze_route_and_tolls(coordinates)
            if not route_data or not identification_result:
                return None
            
            print("Etape 4")
            # ÉTAPE 4: Validation quantité (cas suffisant)
            if self._is_base_route_sufficient(identification_result, target_tolls, optimization_mode):
                return self.route_assembler.format_base_route_as_result(
                    route_data['route'], target_tolls
                )
            
            # ÉTAPES 5-8: Optimisation complète
            return self._perform_full_optimization(
                coordinates, target_tolls, optimization_mode,
                route_data, identification_result
            )
            
        except Exception as e:
            print(f"❌ Erreur optimisation : {e}")
            return None
    
    def _validate_inputs(
        self, 
        coordinates: List[List[float]], 
        target_tolls: int, 
        optimization_mode: str
    ) -> bool:
        """Valide les paramètres d'entrée."""
        if not self.route_provider.validate_coordinates(coordinates):
            return False
        
        if optimization_mode not in ['count', 'budget']:
            print(f"❌ Mode d'optimisation invalide : {optimization_mode}")
            return False
        
        if target_tolls < 0:
            print(f"❌ Cible invalide : {target_tolls}")
            return False
        
        return True
    
    def _handle_zero_tolls(self, coordinates: List[List[float]]) -> Optional[Dict]:
        """ÉTAPE 1: Gère le cas spécial 0 péage."""
        print("🚫 Cas spécial : 0 péage demandé")
        
        result = self.route_provider.get_toll_free_route(coordinates)
        if not result:
            print("❌ Impossible d'obtenir une route sans péages")
            return None
        
        print("✅ Route sans péages trouvée")
        return result
    
    def _analyze_route_and_tolls(
        self, 
        coordinates: List[List[float]]
    ) -> tuple:
        """ÉTAPES 2-3: Analyse route de base + identification péages."""
        
        print("Etape 2")
        # ÉTAPE 2: Route de base avec tollways
        route_data, tollways_data = self.route_provider.get_base_route_with_tollways(coordinates)
        if not route_data or not tollways_data:
            print("❌ Échec analyse route de base")
            return None, None
        
        print("Etape 3")
        # ÉTAPE 3: Identification péages sur route/autour
        identification_result = self.toll_identifier.identify_tolls_on_route(
            route_data['route_coords'], tollways_data['segments']
        )
        
        if not identification_result:
            print("❌ Échec identification péages")
            return route_data, None
        
        return route_data, identification_result
    
    def _is_base_route_sufficient(
        self, 
        identification_result: Dict, 
        target_tolls: int,
        optimization_mode: str
    ) -> bool:
        """ÉTAPE 4: Vérifie si la route de base suffit."""
        # Vérification centrale : aucun péage détecté sur la route de base
        if identification_result['total_tolls_on_route'] == 0:
            print("✅ Aucun péage détecté sur la route de base, optimisation inutile.")
            return True
        
        if optimization_mode == 'count':
            tolls_available = identification_result['total_tolls_on_route']
            
            # Cas spécial : si on ne demande qu'1 péage et qu'on n'a que des fermés
            # → impossible de respecter la règle (fermé doit être accompagné)
            # → renvoyer route sans péage
            if target_tolls == 1:
                open_tolls = sum(1 for toll in identification_result['tolls_on_route'] 
                               if toll.get('toll_type') == 'ouvert')
                if open_tolls == 0:
                    print("⚠️ 1 péage demandé mais que des fermés → route sans péage")
                    return True
            
            # Logique principale : route de base suffisante si on a assez de péages
            # OU si on a atteint le maximum possible (on demande plus qu'il n'y en a)
            if target_tolls <= tolls_available:
                print(f"✅ Route de base suffisante : {tolls_available} péages disponibles >= {target_tolls} demandés")
                return True
            else:
                print(f"✅ Route de base suffisante : {tolls_available} péages disponibles (maximum atteint pour {target_tolls} demandés)")
                return True
        
        elif optimization_mode == 'budget':
            # TODO: Implémenter validation budget
            print("⚠️ Validation budget : À IMPLÉMENTER")
        
        return False
    
    def _perform_full_optimization(
        self,
        coordinates: List[List[float]], 
        target_tolls: int,
        optimization_mode: str,
        route_data: Dict,
        identification_result: Dict
    ) -> Optional[Dict]:
        """ÉTAPES 5-8: Optimisation complète avec segmentation."""
        
        print("Etape 5")
        # ÉTAPE 5: Sélection péages avec remplacement intelligent
        # Exemple: [Ouvert,Fermé1,Fermé2,Fermé3,Fermé4] → objectif 2
        # Enlève: Ouvert,Fermé1,Fermé2 → reste: Fermé3,Fermé4
        # Optimise: Fermé3 → EntréeX (pour éviter de passer par Fermé3 sur route)
        selection_result = self._select_tolls(
            identification_result, target_tolls, optimization_mode
        )
        if not selection_result or not selection_result.get('selection_valid'):
            print("❌ Échec sélection péages")
            return None
        
        print("Etape 6")
        # ÉTAPE 6: Création segments optimisés
        # Segment 1: [Départ → Début EntréeX] (SANS péage)
        # Segment 2: [Début EntréeX → Arrivée] (AVEC péages: EntréeX + Fermé4)
        segments_config = self.segment_creator.create_optimized_segments(
            coordinates, selection_result['selected_tolls'],
            identification_result, selection_result
        )
        if not segments_config:
            print("❌ Échec création segments")
            return None
        
        print("Etape 7")
        # ÉTAPE 7: Calcul segments avec ORS
        # Appel 1: Route sans péage pour segment 1
        # Appel 2: Route avec péages pour segment 2
        calculated_segments = self.segment_calculator.calculate_segments_routes(
            segments_config, {'segments_config': segments_config}
        )
        if not calculated_segments:
            print("❌ Échec calcul segments")
            return None
        
        print("Etape 8")
        # ÉTAPE 8: Assemblage final des segments
        # Combine: segment1 + segment2 → route finale optimisée
        final_route = self.route_assembler.assemble_final_route(
            calculated_segments, target_tolls, selection_result['selected_tolls']
        )
        
        if not final_route:
            print("❌ Échec assemblage final")
            return None
        
        print("✅ Optimisation complète réussie")
        return final_route
    
    def _select_tolls(
        self, 
        identification_result: Dict, 
        target_tolls: int,
        optimization_mode: str
    ) -> Optional[Dict]:
        """ÉTAPE 5: Sélection des péages selon le mode."""
        
        tolls_on_route = identification_result['tolls_on_route']
        
        if optimization_mode == 'count':
            return self.toll_selector.select_tolls_by_count(
                tolls_on_route, target_tolls, identification_result
            )
        elif optimization_mode == 'budget':
            return self.toll_selector.select_tolls_by_budget(
                tolls_on_route, target_tolls, identification_result
            )
        
        return None
    
    def get_optimizer_stats(self) -> Dict:
        """Retourne les statistiques de l'optimiseur."""
        spatial_stats = self.toll_identifier.get_spatial_index_stats()
        
        return {
            'optimizer_ready': True,
            'spatial_index': spatial_stats,
            'modules_loaded': {
                'route_provider': self.route_provider is not None,
                'toll_identifier': self.toll_identifier is not None,
                'toll_selector': self.toll_selector is not None,
                'segment_creator': self.segment_creator is not None,
                'segment_calculator': self.segment_calculator is not None,
                'route_assembler': self.route_assembler is not None
            }
        }
