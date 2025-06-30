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
        target_tolls: Optional[int] = None,
        target_budget: Optional[float] = None,
        optimization_mode: str = 'count',
        veh_class: str = "c1"
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
        print(f"🎯 Optimisation route: {target_tolls if optimization_mode == 'count' else target_budget} {'péages' if optimization_mode == 'count' else '€'}")
        
        target_value = int(target_tolls) if optimization_mode == 'count' else target_budget

        # Validation des entrées
        if not self._validate_inputs(coordinates, target_value, optimization_mode):
            return None
        
        try:
            print("Etape 1")
            # ÉTAPE 1: Route sans péage (cas spéciaux : 0 ou 1 péage)
            if (optimization_mode == 'count' and (target_tolls == 0 or target_tolls == 1)) or (optimization_mode == 'budget' and target_budget is not None and target_budget <= 0):
                return self._handle_zero_tolls(coordinates)
            
            # ÉTAPES 2-3: Route de base + identification péages
            route_data, identification_result = self._analyze_route_and_tolls(coordinates)
            if not route_data or not identification_result:
                return None
            
            print("Etape 4")
            # ÉTAPE 4: Validation quantité (cas suffisant)
            target_value = target_tolls if optimization_mode == 'count' else target_budget
            if self._is_base_route_sufficient(identification_result, target_value, optimization_mode):
                target_for_result = target_tolls if optimization_mode == 'count' else 0
                return self.route_assembler.format_base_route_as_result(
                    route_data['route'], target_for_result
                )
            
            # ÉTAPES 5-8: Optimisation complète
            return self._perform_full_optimization(
                coordinates, target_value, optimization_mode,
                route_data, identification_result
            )
            
        except Exception as e:
            print(f"❌ Erreur optimisation : {e}")
            return None
    
    def _validate_inputs(
        self, 
        coordinates: List[List[float]], 
        target_tolls: float, 
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
        """ÉTAPE 1: Gère le cas spécial 0 ou 1 péage (route sans péage)."""
        print("🚫 Cas spécial : route sans péage demandée")
        
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
        target_value: float,
        optimization_mode: str = 'count'
    ) -> bool:
        """ÉTAPE 4: Vérifie si la route de base suffit."""
        # Vérification centrale : aucun péage détecté sur la route de base
        if identification_result['total_tolls_on_route'] == 0:
            print("✅ Aucun péage détecté sur la route de base, optimisation inutile.")
            return True
        
        if optimization_mode == 'count':
            tolls_available = identification_result['total_tolls_on_route']
            target_tolls = int(target_value)
            
            # Logique principale : route de base suffisante SEULEMENT si :
            # 1. On demande plus qu'il n'y en a (maximum atteint)
            # 2. OU on demande exactement ce qu'il y a
            if target_tolls > tolls_available:
                print(f"✅ Route de base suffisante : {tolls_available} péages disponibles (maximum atteint pour {target_tolls} demandés)")
                return True
            elif target_tolls == tolls_available:
                print(f"✅ Route de base suffisante : {tolls_available} péages disponibles = {target_tolls} demandés")
                return True
            else:
                # target_tolls < tolls_available → on peut optimiser pour avoir moins de péages
                print(f"🔧 Optimisation nécessaire : {target_tolls} péages demandés < {tolls_available} disponibles")
                return False
        
        elif optimization_mode == 'budget':
            # Calculer le coût total de la route de base
            target_budget = target_value
            print(f"   💰 Calcul du coût total pour budget de {target_budget}€...")
            
            # Utiliser les péages identifiés sur la route de base
            tolls_on_route = identification_result.get('tolls_on_route', [])
            if not tolls_on_route:
                print("   ✅ Aucun péage → coût 0€, budget respecté")
                return True
            
            # Calculer le coût avec le cache V2
            total_cost = self._calculate_route_cost(tolls_on_route)
            print(f"   💰 Coût total calculé: {total_cost}€")
            
            if total_cost <= target_budget:
                print(f"   ✅ Route de base suffisante: {total_cost}€ <= {target_budget}€")
                return True
            else:
                print(f"   🔧 Optimisation nécessaire: {total_cost}€ > {target_budget}€")
                return False
        
        return False
    
    def _perform_full_optimization(
        self,
        coordinates: List[List[float]], 
        target_value: float,
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
            identification_result, target_value, optimization_mode
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
        target_tolls = int(target_value) if optimization_mode == 'count' else 0
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
        target_value: float,
        optimization_mode: str
    ) -> Optional[Dict]:
        """ÉTAPE 5: Sélection des péages selon le mode."""
        
        tolls_on_route = identification_result['tolls_on_route']
        
        if optimization_mode == 'count':
            target_tolls = int(target_value)
            return self.toll_selector.select_tolls_by_count(
                tolls_on_route, target_tolls, identification_result
            )
        elif optimization_mode == 'budget':
            return self.toll_selector.select_tolls_by_budget(
                tolls_on_route, target_value, identification_result
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
    
    def _calculate_route_cost(self, tolls_on_route: List) -> float:
        """
        Calcule le coût total d'une route en utilisant les péages identifiés.
        
        Args:
            tolls_on_route: Liste des péages sur la route
            
        Returns:
            Coût total en euros
        """
        try:
            from ..utils.cache_accessor import CacheAccessor
            
            if not tolls_on_route:
                return 0.0
            
            # Extraire les objets TollBoothStation
            toll_stations = []
            for toll_data in tolls_on_route:
                if isinstance(toll_data, dict) and 'toll' in toll_data:
                    toll_station = toll_data['toll']
                    if hasattr(toll_station, 'osm_id') and hasattr(toll_station, 'name'):
                        toll_stations.append(toll_station)
            
            if len(toll_stations) < 2:
                print(f"   ⚠️ Moins de 2 péages ({len(toll_stations)}) - pas de calcul possible")
                return 0.0
            
            # Calcul par binômes consécutifs
            total_cost = 0.0
            vehicle_category = "1"  # Catégorie standard
            
            for i in range(len(toll_stations) - 1):
                toll_from = toll_stations[i]
                toll_to = toll_stations[i + 1]
                
                cost = CacheAccessor.calculate_toll_cost(toll_from, toll_to, vehicle_category)
                if cost is not None:
                    total_cost += cost
                    print(f"   💳 {toll_from.name} → {toll_to.name}: {cost}€")
                else:
                    print(f"   ⚠️ Coût non trouvé: {toll_from.name} → {toll_to.name}")
            
            return round(total_cost, 2)
            
        except Exception as e:
            print(f"   ❌ Erreur calcul coût route: {e}")
            return 0.0
