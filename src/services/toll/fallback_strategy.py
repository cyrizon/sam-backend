"""
fallback_strategy.py
-------------------

Stratégie de fallback simplifiée pour gérer les cas où aucune stratégie spécialisée ne trouve de solution.
Responsabilité unique : fournir deux alternatives simples et fiables.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.common.result_formatter import ResultFormatter
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.error_handler import TollErrorHandler
from src.services.ors_config_manager import ORSConfigManager


class TollFallbackStrategy:
    """
    Stratégie de fallback simplifiée pour l'optimisation de péages.
    Fournit uniquement deux alternatives simples : route sans péage et route de base.
    """
    
    def __init__(self, ors_service):
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def handle_toll_failure(self, coordinates, max_tolls, base_route=None, base_cost=None, base_duration=None, base_toll_count=None, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Gère l'échec de respecter une contrainte de péages en proposant deux alternatives simples.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Limite de péages originale
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
            return TollErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation(Config.Operations.HANDLE_TOLL_FAILURE):
            print(f"=== Stratégie de fallback simplifiée pour max_tolls={max_tolls} ===")
            
            try:
                # Option 1: Essayer d'obtenir une route sans péage
                print("Recherche d'une route sans péage...")
                no_toll_route = self._get_no_toll_route(coordinates, veh_class)
                
                # Option 2: Route de base (réutiliser si fournie, sinon calculer)
                print("Préparation de la route de base...")
                base_route_data = self._get_base_route_data(
                    coordinates, veh_class, base_route, base_cost, base_duration, base_toll_count
                )
                
                # Construire le résultat avec les deux options
                return self._build_fallback_result(no_toll_route, base_route_data, max_tolls)
                    
            except Exception as e:
                print(f"Erreur lors du fallback de péages: {e}")
                return TollErrorHandler.handle_ors_error(e, Config.Operations.HANDLE_TOLL_FAILURE)
    
    def _get_no_toll_route(self, coordinates, veh_class):
        """Tente d'obtenir une route sans péage."""
        try:
            with performance_tracker.measure_operation("get_no_toll_route_fallback"):
                # Utiliser l'option avoid_features de ORS
                no_toll_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
                
                # Vérifier s'il y a encore des péages
                tolls_dict = self.route_calculator.locate_and_cost_tolls(no_toll_route, veh_class)
                tolls_on_route = tolls_dict["on_route"]
                
                if not tolls_on_route:
                    # Vraiment sans péage
                    cost = 0
                    duration = no_toll_route["features"][0]["properties"]["summary"]["duration"]
                    print("✅ Route sans péage trouvée")
                    return ResultFormatter.format_route_result(no_toll_route, cost, duration, 0)
                else:
                    # Il y a encore des péages, calculer le coût
                    cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    duration = no_toll_route["features"][0]["properties"]["summary"]["duration"]
                    toll_count = len(tolls_on_route)
                    print(f"⚠️  Route 'sans péage' contient encore {toll_count} péage(s), coût: {cost}€")
                    return ResultFormatter.format_route_result(no_toll_route, cost, duration, toll_count)
                    
        except Exception as e:
            print(f"❌ Impossible d'obtenir une route sans péage: {e}")
            
        return None
    
    def _get_base_route_data(self, coordinates, veh_class, base_route=None, base_cost=None, base_duration=None, base_toll_count=None):
        """Obtient ou réutilise les données de la route de base."""
        # Si toutes les données sont fournies, les réutiliser
        if all(param is not None for param in [base_route, base_cost, base_duration, base_toll_count]):
            print(f"✅ Réutilisation des données de route de base: {base_cost}€, {base_toll_count} péage(s)")
            return ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
        
        # Sinon, calculer la route de base si nécessaire
        if base_route is None:
            try:
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
    
    def _build_fallback_result(self, no_toll_route, base_route_data, max_tolls):
        """
        Construit le résultat final avec les deux options disponibles.
        
        Returns:
            dict: Résultat formaté avec les meilleures alternatives
        """
        # Déterminer les statuts selon les routes disponibles
        if no_toll_route and base_route_data:
            # Les deux options sont disponibles
            if no_toll_route["cost"] == 0:
                status = Config.StatusCodes.NO_TOLL_ALTERNATIVE_FOUND
                print("✅ Fallback réussi : route gratuite + route de base disponibles")
            else:
                status = Config.StatusCodes.LIMITED_ALTERNATIVES_FOUND
                print(f"⚠️  Fallback partiel : route 'sans péage' ({no_toll_route['cost']}€) + route de base disponibles")
        elif no_toll_route:
            # Seulement route sans péage
            status = Config.StatusCodes.NO_TOLL_ALTERNATIVE_FOUND if no_toll_route["cost"] == 0 else Config.StatusCodes.LIMITED_ALTERNATIVES_FOUND
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
        fastest = self._select_fastest(no_toll_route, base_route_data)
        cheapest = self._select_cheapest(no_toll_route, base_route_data)
        min_tolls = self._select_min_tolls(no_toll_route, base_route_data)
        
        # Afficher le résumé
        self._log_fallback_summary(fastest, cheapest, min_tolls, max_tolls)
        
        return ResultFormatter.format_optimization_results(
            fastest=fastest,
            cheapest=cheapest,
            min_tolls=min_tolls,
            status=status
        )
    
    def _select_fastest(self, no_toll_route, base_route_data):
        """Sélectionne la route la plus rapide."""
        options = [r for r in [no_toll_route, base_route_data] if r is not None]
        if not options:
            return None
        return min(options, key=lambda r: r["duration"])
    
    def _select_cheapest(self, no_toll_route, base_route_data):
        """Sélectionne la route la moins chère."""
        options = [r for r in [no_toll_route, base_route_data] if r is not None]
        if not options:
            return None
        return min(options, key=lambda r: r["cost"])
    
    def _select_min_tolls(self, no_toll_route, base_route_data):
        """Sélectionne la route avec le moins de péages."""
        options = [r for r in [no_toll_route, base_route_data] if r is not None]
        if not options:
            return None
        return min(options, key=lambda r: r["toll_count"])
    def _log_fallback_summary(self, fastest, cheapest, min_tolls, max_tolls):
        """Affiche un résumé des options de fallback."""
        print("=" * 50)
        print("📊 RÉSUMÉ DU FALLBACK TOLL")
        print("=" * 50)
        print(f"Contrainte originale : max_tolls = {max_tolls}")
        
        if fastest:
            print(f"⚡ Plus rapide : {fastest['duration']/60:.1f}min, {fastest['cost']}€, {fastest['toll_count']} péage(s)")
        if cheapest:
            print(f"💰 Moins chère : {cheapest['duration']/60:.1f}min, {cheapest['cost']}€, {cheapest['toll_count']} péage(s)")
        if min_tolls:
            print(f"🛣️  Moins de péages : {min_tolls['duration']/60:.1f}min, {min_tolls['cost']}€, {min_tolls['toll_count']} péage(s)")
        
        print("=" * 50)