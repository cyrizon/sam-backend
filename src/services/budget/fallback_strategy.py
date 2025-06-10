"""
fallback_strategy.py
-------------------

Stratégie de fallback simplifiée pour gérer les cas où aucune solution ne respecte le budget.
Responsabilité unique : fournir deux alternatives simples et fiables.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.common.result_formatter import ResultFormatter
from src.services.budget.route_calculator import BudgetRouteCalculator as RouteCalculator
from src.services.budget.error_handler import BudgetErrorHandler
from src.services.ors_config_manager import ORSConfigManager
from src.services.toll_locator import locate_tolls


class BudgetFallbackStrategy:
    """
    Stratégie de fallback simplifiée pour l'optimisation budgétaire.
    Fournit uniquement deux alternatives simples : route sans péage et route de base.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def handle_budget_failure(self, coordinates, budget_limit, budget_type, base_route=None, base_cost=None, base_duration=None, base_toll_count=None, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Gère l'échec de respecter une contrainte budgétaire en proposant deux alternatives simples.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            budget_limit: Limite budgétaire originale (peut être None)
            budget_type: Type de budget ("zero", "absolute", "percentage", "none")
            base_route: Route de base déjà calculée (optionnel)
            base_cost: Coût de la route de base (optionnel)
            base_duration: Durée de la route de base (optionnel)
            base_toll_count: Nombre de péages de la route de base (optionnel)
            veh_class: Classe de véhicule
            
        Returns:
            dict: Résultat de fallback formaté avec deux options simples
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return BudgetErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation(Config.Operations.HANDLE_BUDGET_FAILURE):
            print(f"=== Stratégie de fallback simplifiée pour budget {budget_type} ===")
            
            try:
                # Option 1: Essayer d'obtenir une route sans péage
                print("Recherche d'une route sans péage...")
                toll_free_route = self._get_toll_free_route(coordinates, veh_class)
                
                # Option 2: Route de base (réutiliser si fournie, sinon calculer)
                print("Préparation de la route de base...")
                base_route_data = self._get_base_route_data(
                    coordinates, veh_class, base_route, base_cost, base_duration, base_toll_count
                )
                
                # Construire le résultat avec les deux options
                return self._build_fallback_result(toll_free_route, base_route_data, budget_type, budget_limit)
                    
            except Exception as e:
                print(f"Erreur lors du fallback budgétaire: {e}")
                return BudgetErrorHandler.handle_ors_error(e, Config.Operations.HANDLE_BUDGET_FAILURE)
    
    def _get_toll_free_route(self, coordinates, veh_class):
        """
        Tente d'obtenir une route sans péage.
        
        Returns:
            dict: Route formatée ou None si impossible
        """
        try:
            # Demander une route évitant les péages
            toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
            
            if toll_free_route:
                # Vérifier si la route contient vraiment des péages
                tolls_dict = self.route_calculator.locate_and_cost_tolls(toll_free_route, veh_class)
                tolls_on_route = tolls_dict["on_route"]
                
                if not tolls_on_route:
                    # Route vraiment gratuite
                    duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
                    print("✅ Route 100% gratuite trouvée")
                    return ResultFormatter.format_route_result(toll_free_route, 0, duration, 0)
                else:
                    # Il y a encore des péages, calculer le coût
                    cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
                    toll_count = len(tolls_on_route)
                    print(f"⚠️  Route 'sans péage' contient encore {toll_count} péage(s), coût: {cost}€")
                    return ResultFormatter.format_route_result(toll_free_route, cost, duration, toll_count)
                    
        except Exception as e:
            print(f"❌ Impossible d'obtenir une route sans péage: {e}")
            
        return None
    
    def _get_base_route_data(self, coordinates, veh_class, base_route=None, base_cost=None, base_duration=None, base_toll_count=None):
        """
        Obtient les données de la route de base, en réutilisant celles fournies si possible.
        
        Returns:
            dict: Route de base formatée ou None si impossible
        """
        # Si toutes les données de base sont fournies, les réutiliser
        if all([base_route is not None, base_cost is not None, base_duration is not None, base_toll_count is not None]):
            print(f"✅ Réutilisation de la route de base: {base_cost}€, {base_toll_count} péage(s)")
            return ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
        
        # Sinon, calculer la route de base
        if base_route is None:
            try:
                print("Calcul de la route de base...")
                base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
                
                # Calculer les métriques
                tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                tolls_on_route = tolls_dict["on_route"]
                
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                toll_count = len(tolls_on_route)
                
                print(f"✅ Route de base calculée: {cost}€, {toll_count} péage(s)")
                return ResultFormatter.format_route_result(base_route, cost, duration, toll_count)
                
            except Exception as e:
                print(f"❌ Erreur lors du calcul de la route de base: {e}")
                return None
        
        return None
    
    def _build_fallback_result(self, toll_free_route, base_route_data, budget_type, budget_limit):
        """
        Construit le résultat final avec les deux options disponibles.
        
        Returns:
            dict: Résultat formaté avec les meilleures alternatives
        """
        # Déterminer les statuts selon les routes disponibles
        if toll_free_route and base_route_data:
            # Les deux options sont disponibles
            if toll_free_route["cost"] == 0:
                status = Config.StatusCodes.FREE_ALTERNATIVE_FOUND
                print("✅ Fallback réussi : route gratuite + route de base disponibles")
            else:
                status = Config.StatusCodes.LIMITED_ALTERNATIVES_FOUND
                print(f"⚠️  Fallback partiel : route 'sans péage' ({toll_free_route['cost']}€) + route de base disponibles")
        elif toll_free_route:
            # Seulement route sans péage
            status = Config.StatusCodes.FREE_ALTERNATIVE_FOUND if toll_free_route["cost"] == 0 else Config.StatusCodes.LIMITED_ALTERNATIVES_FOUND
            print("✅ Route sans péage disponible uniquement")
        elif base_route_data:
            # Seulement route de base
            status = Config.StatusCodes.ONLY_BASE_ROUTE_AVAILABLE
            print("⚠️  Route de base disponible uniquement")
        else:
            # Aucune option disponible
            status = Config.StatusCodes.NO_ALTERNATIVE_FOUND
            print("❌ Aucune alternative trouvée")
        
        # Choisir les meilleures options pour fastest, cheapest, min_tolls
        fastest = self._select_fastest(toll_free_route, base_route_data)
        cheapest = self._select_cheapest(toll_free_route, base_route_data)
        min_tolls = self._select_min_tolls(toll_free_route, base_route_data)
        
        # Afficher le résumé
        self._log_fallback_summary(fastest, cheapest, min_tolls, budget_type, budget_limit)
        
        return ResultFormatter.format_optimization_results(
            fastest=fastest,
            cheapest=cheapest,
            min_tolls=min_tolls,
            status=status
        )
    
    def _select_fastest(self, toll_free_route, base_route_data):
        """Sélectionne la route la plus rapide."""
        options = [r for r in [toll_free_route, base_route_data] if r is not None]
        if not options:
            return None
        return min(options, key=lambda r: r["duration"])
    
    def _select_cheapest(self, toll_free_route, base_route_data):
        """Sélectionne la route la moins chère."""
        options = [r for r in [toll_free_route, base_route_data] if r is not None]
        if not options:
            return None
        return min(options, key=lambda r: r["cost"])
    
    def _select_min_tolls(self, toll_free_route, base_route_data):
        """Sélectionne la route avec le moins de péages."""
        options = [r for r in [toll_free_route, base_route_data] if r is not None]
        if not options:
            return None
        return min(options, key=lambda r: r["toll_count"])
    
    def _log_fallback_summary(self, fastest, cheapest, min_tolls, budget_type, budget_limit):
        """Affiche un résumé des options de fallback."""
        print("\n=== RÉSUMÉ DU FALLBACK ===")
        
        if budget_limit is not None:
            print(f"Budget original {budget_type}: {budget_limit}")
        
        if fastest:
            print(f"Plus rapide: {fastest['duration']/60:.1f}min, {fastest['cost']}€, {fastest['toll_count']} péage(s)")
        
        if cheapest:
            print(f"Moins cher: {cheapest['cost']}€, {cheapest['duration']/60:.1f}min, {cheapest['toll_count']} péage(s)")
        
        if min_tolls:
            print(f"Moins de péages: {min_tolls['toll_count']} péage(s), {min_tolls['cost']}€, {min_tolls['duration']/60:.1f}min")
        
        print("=" * 30)