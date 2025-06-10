"""
budget_strategies.py
------------------

Orchestrateur pour l'optimisation budgétaire - délégation pure comme toll_strategies.py
Responsabilité unique : déléguer aux stratégies spécialisées sans logique métier.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.zero_budget_strategy import ZeroBudgetStrategy
from src.services.budget.percentage_budget_strategy import PercentageBudgetStrategy
from src.services.budget.absolute_budget_strategy import AbsoluteBudgetStrategy
from src.services.budget.fallback_strategy import BudgetFallbackStrategy
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.budget.error_handler import BudgetErrorHandler


class BudgetRouteOptimizer:
    """
    Orchestrateur d'itinéraires avec contraintes budgétaires.
    Délégation pure aux stratégies spécialisées - aucune logique métier.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.zero_budget_strategy = ZeroBudgetStrategy(ors_service)
        self.percentage_budget_strategy = PercentageBudgetStrategy(ors_service)
        self.absolute_budget_strategy = AbsoluteBudgetStrategy(ors_service)
        self.fallback_strategy = BudgetFallbackStrategy(ors_service)
    
    def compute_route_with_budget_limit(
        self,
        coordinates,
        max_price=None,
        max_price_percent=None,
        veh_class=Config.DEFAULT_VEH_CLASS,
        max_comb_size=Config.DEFAULT_MAX_COMB_SIZE
    ):
        """
        Calcule un itinéraire avec contrainte budgétaire - délégation pure.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_price: Prix maximum en euros (absolu)
            max_price_percent: Pourcentage du coût de base (0.8 = 80%)
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        
        BudgetErrorHandler.log_operation_start(
            "compute_route_with_budget_limit",
            max_price=max_price,
            max_price_percent=max_price_percent,
            veh_class=veh_class
        )
        
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_WITH_BUDGET_LIMIT):
            try:                  # Validation précoce
                validation_error = BudgetErrorHandler.handle_budget_validation_error(max_price, max_price_percent)
                if validation_error:
                    BudgetErrorHandler.log_operation_failure("compute_route_with_budget_limit", "Validation failed")
                    return validation_error
                
                # Vérification précoce de faisabilité budgétaire AVANT les calculs coûteux
                if self._should_check_budget_feasibility(max_price, max_price_percent):
                    early_fallback_needed = self._check_budget_feasibility_early(coordinates, max_price, max_price_percent, veh_class)
                    if early_fallback_needed:
                        print("🚫 Budget manifestement trop bas - Fallback immédiat (économie de calculs)")
                        return self._handle_strategy_failure_with_base_data(
                            coordinates, max_price, max_price_percent, veh_class, max_comb_size, None
                        )
                  # Délégation pure - aucune logique métier (seulement si budget potentiellement faisable)
                result = self._delegate_to_strategy(coordinates, max_price, max_price_percent, veh_class, max_comb_size)
                
                # Fallback automatique si échec ou si statut indique que le fallback est nécessaire
                if not result or self._should_trigger_fallback(result):
                    # Essayer d'extraire les données de route de base du résultat de la stratégie
                    base_data = self._extract_base_route_data_from_result(result)
                    result = self._handle_strategy_failure_with_base_data(
                        coordinates, max_price, max_price_percent, veh_class, max_comb_size, base_data
                    )
                
                BudgetErrorHandler.log_operation_success("compute_route_with_budget_limit", f"Status: {result.get('status', 'SUCCESS')}")
                return result
                
            except Exception as e:
                BudgetErrorHandler.log_operation_failure("compute_route_with_budget_limit", str(e))
                return self._handle_critical_failure(coordinates, max_price, max_price_percent, veh_class, max_comb_size, str(e))
    
    def _delegate_to_strategy(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size):
        """Délègue à la stratégie appropriée selon les contraintes."""
        
        # Budget zéro
        if max_price == 0 or max_price_percent == 0:
            return self.zero_budget_strategy.handle_zero_budget_route(coordinates, veh_class)
        
        # Budget en pourcentage
        elif max_price_percent is not None:
            return self.percentage_budget_strategy.handle_percentage_budget_route(
                coordinates, max_price_percent, veh_class, max_comb_size
            )
        
        # Budget absolu
        elif max_price is not None:
            return self.absolute_budget_strategy.handle_absolute_budget_route(
                coordinates, max_price, veh_class, max_comb_size
            )        # Aucune contrainte - meilleure solution globale
        else:
            return self.fallback_strategy.handle_budget_failure(
                coordinates, None, "none", veh_class=veh_class
            )
    
    def _should_trigger_early_fallback(self, result, coordinates, max_price, max_price_percent, veh_class):
        """
        Vérifie si le budget demandé est trop bas par rapport aux coûts minimaux possibles.
        
        Logique : Si le budget est inférieur au péage le moins cher ou à la combinaison
        la moins chère possible, on déclenche directement le fallback.
        """
        # Ne faire cette vérification que pour les budgets avec contraintes
        if max_price is None and max_price_percent is None:
            return False
        
        # Ne faire cette vérification que si on a un résultat qui indique un échec budgétaire
        if not result or result.get("status") not in [
            Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST,
            Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET
        ]:
            return False
        
        try:
            print("🔍 Vérification de faisabilité budgétaire...")
            
            # Utiliser la route de base du résultat ou la calculer
            base_route = None
            if result:
                # Essayer d'extraire la route de base du résultat
                for route_type in ["fastest", "cheapest", "min_tolls"]:
                    route_data = result.get(route_type)
                    if route_data and route_data.get("route"):
                        base_route = route_data.get("route")
                        break
            
            # Si pas de route de base dans le résultat, la calculer
            if not base_route:
                from src.services.budget.route_calculator import BudgetRouteCalculator
                route_calculator = BudgetRouteCalculator(self.ors)
                base_route = route_calculator.get_base_route_with_tracking(coordinates)
            
            if not base_route:
                return False
            
            # Localiser et coûter tous les péages sur et autour de la route
            from src.services.budget.route_calculator import BudgetRouteCalculator
            route_calculator = BudgetRouteCalculator(self.ors)
            tolls_dict = route_calculator.locate_and_cost_tolls(base_route, veh_class)
            
            all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
            if not all_tolls:
                print("📍 Aucun péage trouvé, pas de problème de faisabilité")
                return False  # Pas de péages, pas de problème de faisabilité
            
            # Calculer le coût minimal possible
            min_cost = self._calculate_minimum_possible_cost(all_tolls)
            
            # Déterminer le budget effectif
            if max_price is not None:
                budget_limit = max_price
                budget_type = "absolu"
            else:
                # Pour le pourcentage, calculer le coût de base pour déterminer le budget effectif
                base_cost = sum(t.get("cost", 0) for t in tolls_dict["on_route"])
                budget_limit = base_cost * (max_price_percent / 100)
                budget_type = "pourcentage"
            
            # Vérifier si le budget est inférieur au coût minimal possible
            if budget_limit < min_cost:
                print(f"🚫 Budget {budget_type} ({budget_limit:.2f}€) < Coût minimal possible ({min_cost:.2f}€)")
                print("→ Impossible de respecter ce budget, déclenchement du fallback précoce")
                return True
            else:
                print(f"✅ Budget {budget_type} ({budget_limit:.2f}€) >= Coût minimal possible ({min_cost:.2f}€)")
                print("→ Budget potentiellement réalisable, mais autres contraintes non satisfaites")
                return False
                
        except Exception as e:
            print(f"⚠️  Erreur lors de la vérification précoce de faisabilité: {e}")
            return False  # En cas d'erreur, ne pas déclencher le fallback précoce
    
    def _calculate_minimum_possible_cost(self, all_tolls):
        """
        Calcule le coût minimal possible parmi tous les péages disponibles.
        
        Returns:
            float: Le coût du péage ouvert le moins cher ou 0 si route sans péage possible
        """
        from src.utils.route_utils import is_toll_open_system
        
        if not all_tolls:
            return 0
        
        # Filtrer les péages ouverts (coût fixe)
        open_tolls = [toll for toll in all_tolls if is_toll_open_system(toll["id"])]
        
        if open_tolls:
            # Trouver le péage ouvert le moins cher
            min_open_cost = min(toll.get("cost", float('inf')) for toll in open_tolls)
            print(f"💰 Péage ouvert le moins cher: {min_open_cost:.2f}€")
            return min_open_cost
        else:
            # Si pas de péages ouverts, prendre le péage fermé le moins cher
            min_closed_cost = min(toll.get("cost", float('inf')) for toll in all_tolls)
            print(f"💰 Péage fermé le moins cher: {min_closed_cost:.2f}€")
            return min_closed_cost
        
    def _should_trigger_fallback(self, result):
        """Détermine si le fallback doit être déclenché selon le statut du résultat."""
        if not result:
            return True
        
        # Statuts qui indiquent un échec nécessitant un fallback
        failure_statuses = {
            Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET,
            Config.StatusCodes.NO_TOLLS_FOUND,
            Config.StatusCodes.NO_ALTERNATIVE_FOUND
        }
        
        return result.get("status") in failure_statuses
    
    def _extract_base_route_data_from_result(self, result):
        """Extrait les données de route de base d'un résultat de stratégie."""
        if not result:
            return None
        
        # Essayer d'extraire la route de base du fastest, cheapest ou min_tolls
        for key in ["fastest", "cheapest", "min_tolls"]:
            route_data = result.get(key)
            if route_data and route_data.get("route"):
                return {
                    "base_route": route_data["route"],
                    "base_cost": route_data.get("cost"),
                    "base_duration": route_data.get("duration"),
                    "base_toll_count": route_data.get("toll_count")
                }
        
        return None
    
    def _handle_strategy_failure_with_base_data(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size, base_data):
        """Gère l'échec des stratégies avec données de base optionnelles."""
        budget_type = self._determine_budget_type(max_price, max_price_percent)
        budget_limit = max_price or max_price_percent
        
        # Utiliser les données de base si disponibles, sinon calculer
        if base_data:
            print(f"📋 Utilisation des données de route de base extraites du résultat de stratégie")
            return self.fallback_strategy.handle_budget_failure(
                coordinates, budget_limit, budget_type,
                base_route=base_data.get("base_route"),
                base_cost=base_data.get("base_cost"),
                base_duration=base_data.get("base_duration"),
                base_toll_count=base_data.get("base_toll_count"),
                veh_class=veh_class
            )
        else:
            # Fallback vers l'ancienne méthode si pas de données de base
            return self._handle_strategy_failure(coordinates, max_price, max_price_percent, veh_class, max_comb_size)

    def _handle_strategy_failure(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size):
        """Gère l'échec des stratégies principales avec fallback."""
        budget_type = self._determine_budget_type(max_price, max_price_percent)
        budget_limit = max_price or max_price_percent
        
        # Calcul de la route de base pour éviter de la recalculer dans le fallback
        try:
            base_route = None
            base_cost = None
            base_duration = None
            base_toll_count = None
              # Essayer de calculer la route de base une seule fois
            base_route = self.absolute_budget_strategy.route_calculator.get_base_route_with_tracking(coordinates)
            if base_route:
                # Calculer les métriques de base
                tolls_dict = self.absolute_budget_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                tolls_on_route = tolls_dict["on_route"]
                
                base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
                base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                base_toll_count = len(tolls_on_route)
                
                print(f"📋 Route de base calculée pour fallback: {base_cost}€, {base_toll_count} péage(s)")
        except Exception as e:
            print(f"⚠️  Impossible de calculer la route de base pour le fallback: {e}")
        
        return self.fallback_strategy.handle_budget_failure(
            coordinates, budget_limit, budget_type, 
            base_route=base_route, base_cost=base_cost, 
            base_duration=base_duration, base_toll_count=base_toll_count,
            veh_class=veh_class
        )

    def _handle_critical_failure(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size, error_message):
        """Gère les erreurs critiques avec fallback ultime."""
        try:
            budget_type = self._determine_budget_type(max_price, max_price_percent)
            budget_limit = max_price or max_price_percent
            
            # Essayer de calculer la route de base pour le fallback même en cas d'erreur critique
            base_route = None
            base_cost = None
            base_duration = None
            base_toll_count = None
            
            try:
                base_route = self.absolute_budget_strategy.route_calculator.get_base_route_with_tracking(coordinates)
                if base_route:
                    tolls_dict = self.absolute_budget_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                    tolls_on_route = tolls_dict["on_route"]
                    
                    base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                    base_toll_count = len(tolls_on_route)
                    
                    print(f"📋 Route de base calculée pour fallback critique: {base_cost}€, {base_toll_count} péage(s)")
            except Exception as base_error:
                print(f"⚠️  Impossible de calculer la route de base pour le fallback critique: {base_error}")
            
            return self.fallback_strategy.handle_budget_failure(
                coordinates, budget_limit, "error", 
                base_route=base_route, base_cost=base_cost,
                base_duration=base_duration, base_toll_count=base_toll_count,
                veh_class=veh_class
            )
        except Exception:
            # Fallback ultime - route de base avec statut d'erreur critique
            return {
                "fastest": None,
                "cheapest": None,
                "min_tolls": None,
                "status": Config.StatusCodes.CRITICAL_ERROR,
                "error": error_message
            }
    
    def _determine_budget_type(self, max_price, max_price_percent):
        """Détermine le type de contrainte budgétaire."""
        if max_price == 0 or max_price_percent == 0:
            return "zero"
        elif max_price_percent is not None:
            return "percentage"
        elif max_price is not None:
            return "absolute"
        else:
            return "none"
    
    def _should_check_budget_feasibility(self, max_price, max_price_percent):
        """Détermine si on doit faire une vérification de faisabilité budgétaire."""
        # Faire la vérification seulement pour les contraintes budgétaires strictes
        return (max_price is not None and max_price > 0) or (max_price_percent is not None and max_price_percent > 0)
    
    def _check_budget_feasibility_early(self, coordinates, max_price, max_price_percent, veh_class):
        """
        Vérification précoce : le budget demandé est-il réalisable par rapport aux péages disponibles ?
        
        Returns:
            bool: True si fallback nécessaire (budget impossible), False sinon
        """
        try:
            print("🔍 Vérification précoce de faisabilité budgétaire...")
            
            # Calculer la route de base pour analyser les péages
            from src.services.budget.route_calculator import BudgetRouteCalculator
            route_calculator = BudgetRouteCalculator(self.ors)
            base_route = route_calculator.get_base_route_with_tracking(coordinates)
            
            if not base_route:
                print("⚠️  Impossible de calculer la route de base pour la vérification")
                return False  # En cas d'échec, ne pas déclencher le fallback précoce
            
            # Localiser et coûter tous les péages sur et autour de la route
            tolls_dict = route_calculator.locate_and_cost_tolls(base_route, veh_class)
            all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
            
            if not all_tolls:
                print("📍 Aucun péage trouvé - Budget probablement réalisable")
                return False  # Pas de péages, budget potentiellement réalisable
            
            # Calculer le coût minimal possible
            min_cost = self._calculate_minimum_possible_cost(all_tolls)
            
            # Déterminer le budget effectif selon le type de contrainte
            if max_price is not None:
                budget_limit = max_price
                budget_type = "absolu"
            else:
                # Pour le pourcentage, calculer le coût de base
                base_cost = sum(t.get("cost", 0) for t in tolls_dict["on_route"])
                budget_limit = base_cost * (max_price_percent / 100)
                budget_type = "pourcentage"
            
            # Comparaison budget vs coût minimal
            if budget_limit < min_cost:
                print(f"🚫 Budget {budget_type} ({budget_limit:.2f}€) < Coût minimal possible ({min_cost:.2f}€)")
                print("→ Budget impossible à respecter - Fallback immédiat justifié")
                return True  # Déclencher le fallback précoce
            else:
                print(f"✅ Budget {budget_type} ({budget_limit:.2f}€) >= Coût minimal possible ({min_cost:.2f}€)")
                print("→ Budget potentiellement réalisable - Poursuite avec les stratégies")
                return False  # Continuer avec les stratégies normales
                
        except Exception as e:
            print(f"⚠️  Erreur lors de la vérification précoce: {e}")
            return False  # En cas d'erreur, ne pas déclencher le fallback précoce
