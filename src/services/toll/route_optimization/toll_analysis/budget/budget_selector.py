"""
Budget Toll Selector
===================

Sélecteur de péages optimisé par budget.
Orchestrateur principal utilisant les modules spécialisés.
"""

from typing import List, Dict, Optional
from .budget_optimizer import BudgetOptimizer
from ...utils.cache_accessor import CacheAccessor
from .budget_optimizer import BudgetOptimizer


class BudgetTollSelector:
    """
    Sélecteur de péages par budget.
    Responsabilité : Orchestration de la sélection par budget.
    """
    
    def __init__(self):
        """Initialise le sélecteur par budget."""
        self.optimizer = BudgetOptimizer()
        print("💰 Budget Toll Selector initialisé")
    
    def select_tolls_by_budget(
        self, 
        tolls_on_route: List[Dict], 
        budget_limit: float,
        route_coordinates: List[List[float]]
    ) -> Optional[Dict]:
        """
        Sélectionne les péages pour respecter un budget donné.
        
        Args:
            tolls_on_route: Liste des péages sur la route
            budget_limit: Budget maximum en euros
            route_coordinates: Coordonnées de la route de base
            
        Returns:
            Résultat de sélection ou None si impossible
        """
        print(f"💰 Sélection par budget : {budget_limit}€")
        
        # Vérifications de sécurité
        if budget_limit is None or budget_limit < 0:
            print(f"   ⚠️ Budget limite invalide: {budget_limit}")
            return self._create_no_toll_result("Budget limite invalide")
        
        # Cas spécial : budget = 0 → route sans péage
        if budget_limit == 0.0:
            print(f"   🚫 Budget = 0 → route sans péage")
            return self._create_no_toll_result("Budget 0 → aucun péage autorisé")
        
        if not tolls_on_route:
            return self._create_result([], 0.0, "Aucun péage sur route")
        
        # Calculer le coût initial avec le cache
        initial_cost = self._calculate_total_cost(tolls_on_route)
        
        # Vérification de sécurité pour le coût
        if initial_cost is None:
            print(f"   ⚠️ Impossible de calculer le coût initial")
            return self._create_no_toll_result("Calcul de coût impossible")
        
        print(f"   Coût initial : {initial_cost:.2f}€")
        
        if initial_cost <= budget_limit:
            # Convertir en objets avant de retourner
            converted_tolls = self._convert_tolls_to_objects(tolls_on_route)
            return self._create_result(
                converted_tolls, initial_cost, 
                f"Budget respecté ({initial_cost:.2f}€ <= {budget_limit}€)"
            )
        
        # Optimisation nécessaire
        return self._optimize_for_budget(
            tolls_on_route, budget_limit, route_coordinates
        )
    
    def _optimize_for_budget(
        self, 
        tolls_on_route: List[Dict], 
        budget_limit: float,
        route_coordinates: List[List[float]]
    ) -> Optional[Dict]:
        """
        Optimise la liste de péages pour respecter le budget.
        
        Args:
            tolls_on_route: Péages de base
            budget_limit: Budget limite
            route_coordinates: Coordonnées de route
            
        Returns:
            Résultat optimisé
        """
        print("   🔄 Optimisation par budget...")
        
        # Séparer ouverts et fermés
        open_tolls = [t for t in tolls_on_route if t.get('toll_type') == 'ouvert']
        closed_tolls = [t for t in tolls_on_route if t.get('toll_type') == 'fermé']
        
        if not closed_tolls:
            # Que des ouverts, teste le coût
            cost = self._calculate_total_cost(open_tolls)
            if cost is not None and cost <= budget_limit:
                # Convertir en objets avant de retourner
                converted_tolls = self._convert_tolls_to_objects(open_tolls)
                return self._create_result(converted_tolls, cost, "Ouverts seulement")
            else:
                return self._create_no_toll_result("Budget dépassé même avec ouverts")
        
        # Cas spécial : 1 seul fermé → route sans péage
        if len(closed_tolls) == 1:
            return self._handle_single_closed_toll(open_tolls, budget_limit)
        
        # Optimisation des fermés avec l'optimiseur
        return self.optimizer.optimize_for_budget(
            open_tolls, closed_tolls, budget_limit, 
            route_coordinates
        )
    
    def _handle_single_closed_toll(
        self, 
        open_tolls: List[Dict], 
        budget_limit: float
    ) -> Dict:
        """
        Gère le cas d'un seul péage fermé (règle des systèmes fermés).
        
        Args:
            open_tolls: Péages ouverts
            budget_limit: Budget limite
            
        Returns:
            Résultat approprié
        """
        if open_tolls:
            # Tester si les ouverts respectent le budget
            cost = self._calculate_total_cost(open_tolls)
            if cost is not None and cost <= budget_limit:
                # Convertir en objets avant de retourner
                converted_tolls = self._convert_tolls_to_objects(open_tolls)
                return self._create_result(
                    converted_tolls, cost, 
                    "Ouverts seulement (fermé isolé évité)"
                )
        
        # Sinon route sans péage
        return self._create_no_toll_result("Fermé isolé → route sans péage")
    
    def _create_result(
        self, 
        selected_tolls: List[Dict], 
        total_cost: float, 
        reason: str
    ) -> Dict:
        """
        Crée un résultat de sélection.
        
        Args:
            selected_tolls: Péages sélectionnés
            total_cost: Coût total
            reason: Raison de la sélection
            
        Returns:
            Dictionnaire de résultat
        """
        return {
            'selection_valid': True,
            'selected_tolls': selected_tolls,
            'total_cost': total_cost,
            'selection_reason': reason,
            'optimization_applied': len(selected_tolls) > 0
        }
    
    def _create_no_toll_result(self, reason: str) -> Dict:
        """
        Crée un résultat "route sans péage".
        
        Args:
            reason: Raison du choix
            
        Returns:
            Résultat sans péage
        """
        return {
            'selection_valid': True,
            'selected_tolls': [],
            'total_cost': 0.0,
            'selection_reason': f"Route sans péage : {reason}",
            'optimization_applied': True
        }

    def _calculate_total_cost(self, tolls: List[Dict]) -> float:
        """
        Calcule le coût total d'une liste de péages.
        
        Args:
            tolls: Liste des péages
            
        Returns:
            Coût total en euros
        """
        if not tolls:
            return 0.0
        
        if len(tolls) == 1:
            # Un seul péage, coût par défaut
            return 3.0
        
        try:
            # Convertir en objets pour utiliser CacheAccessor.calculate_total_cost
            converted_tolls = self._convert_tolls_to_objects(tolls)
            
            if len(converted_tolls) >= 2:
                # Utiliser le calcul par binômes consécutifs
                cost = CacheAccessor.calculate_total_cost(converted_tolls)
                return cost if cost is not None else 3.0 * len(tolls)
            else:
                # Fallback si conversion échoue
                return 3.0 * len(tolls)
                
        except Exception as e:
            print(f"   ⚠️ Erreur calcul coût total: {e}")
            # Coût par défaut en cas d'erreur
            return 3.0 * len(tolls)

    def _convert_tolls_to_objects(self, tolls_list: List[Dict]) -> List:
        """
        Convertit une liste de dictionnaires en objets TollBoothStation ou CompleteMotorwayLink.
        Garantit que seuls des objets (jamais des dicts) sont retournés.
        
        Args:
            tolls_list: Liste de dictionnaires de péages
            
        Returns:
            Liste d'objets TollBoothStation ou CompleteMotorwayLink uniquement
        """
        converted_tolls = []
        
        for toll in tolls_list:
            if isinstance(toll, dict) and 'toll' in toll:
                # C'est un résultat d'identification Shapely, extraire l'objet TollBoothStation
                converted_tolls.append(toll['toll'])
            elif isinstance(toll, dict):
                # Essayer de trouver l'objet TollBoothStation correspondant dans le cache
                toll_station = self._find_toll_station_in_cache(toll)
                if toll_station:
                    converted_tolls.append(toll_station)
                else:
                    print(f"     ⚠️ Impossible de convertir le péage {toll.get('name', 'Inconnu')} - IGNORÉ")
                    # Ne pas ajouter le dict - garantir que seuls les objets sont retournés
                    continue
            else:
                # C'est déjà un objet TollBoothStation ou CompleteMotorwayLink
                converted_tolls.append(toll)
        
        return converted_tolls

    def _find_toll_station_in_cache(self, toll_dict: Dict):
        """
        Trouve l'objet TollBoothStation correspondant dans le cache.
        
        Args:
            toll_dict: Dictionnaire représentant un péage
            
        Returns:
            TollBoothStation ou None
        """
        try:
            osm_id = toll_dict.get('osm_id')
            if not osm_id:
                return None
            
            # Chercher dans le cache V2
            toll_stations = CacheAccessor.get_toll_stations()
            for toll_booth in toll_stations:
                if toll_booth.osm_id == osm_id:
                    return toll_booth
            
            print(f"     ⚠️ Péage {osm_id} non trouvé dans le cache")
            return None
            
        except Exception as e:
            print(f"     ❌ Erreur recherche cache: {e}")
            return None
