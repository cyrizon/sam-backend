"""
result_formatter.py
------------------

Formatage centralisé des résultats d'optimisation de routes.
Responsabilité unique : transformer les données de route en formats de sortie standardisés.
"""

from src.services.toll.constants import TollOptimizationConfig as Config


class ResultFormatter:
    """Formatage centralisé pour les résultats d'optimisation."""
    
    @staticmethod
    def format_route_result(route, cost, duration, toll_count, toll_id=None):
        """
        Formate un résultat de route selon le format standard.
        
        Args:
            route: Données de la route (GeoJSON)
            cost: Coût total en euros
            duration: Durée en secondes
            toll_count: Nombre de péages
            toll_id: ID du péage principal (optionnel)
            
        Returns:
            dict: Résultat formaté
        """
        result = {
            "route": route,
            "cost": round(cost, 2) if cost else 0,
            "duration": duration,
            "toll_count": toll_count
        }
        
        if toll_id:
            result["toll_id"] = toll_id
            
        return result
    
    @staticmethod
    def format_optimization_results(fastest, cheapest, min_tolls, status):
        """
        Formate les résultats d'optimisation multi-critères.
        
        Args:
            fastest: Route la plus rapide
            cheapest: Route la moins chère
            min_tolls: Route avec le minimum de péages
            status: Code de statut
            
        Returns:
            dict: Résultats formatés avec status
        """
        return {
            "fastest": fastest,
            "cheapest": cheapest, 
            "min_tolls": min_tolls,
            "status": status
        }
    
    @staticmethod
    def format_error_result(error_message, status_code, operation_name=None):
        """
        Formate un résultat d'erreur.
        
        Args:
            error_message: Message d'erreur
            status_code: Code de statut d'erreur
            operation_name: Nom de l'opération qui a échoué (optionnel)
            
        Returns:
            dict: Résultat d'erreur formaté
        """
        error_result = {
            "error": True,
            "message": error_message,
            "status": status_code
        }
        
        if operation_name:
            error_result["operation"] = operation_name
            
        return error_result
    
    @staticmethod
    def format_uniform_result(single_route, status):
        """
        Crée un résultat uniforme à partir d'une seule route.
        Utile quand une seule solution existe pour tous les critères.
        
        Args:
            single_route: Route unique
            status: Code de statut
            
        Returns:
            dict: Résultat uniforme
        """
        return ResultFormatter.format_optimization_results(
            fastest=single_route,
            cheapest=single_route,
            min_tolls=single_route,
            status=status
        )
    
    @staticmethod
    def format_summary_metrics(route_result):
        """
        Extrait les métriques principales d'un résultat de route.
        
        Args:
            route_result: Résultat de route formaté
            
        Returns:
            dict: Métriques principales
        """
        if not route_result or not route_result.get("route"):
            return {
                "cost": None,
                "duration_minutes": None,
                "toll_count": None,
                "toll_id": None
            }
        
        return {
            "cost": route_result.get("cost", 0),
            "duration_minutes": round(route_result.get("duration", 0) / 60, 1),
            "toll_count": route_result.get("toll_count", 0),
            "toll_id": route_result.get("toll_id", None)
        }
    
    @staticmethod
    def format_comparison_summary(optimization_results):
        """
        Crée un résumé comparatif des différentes optimisations.
        
        Args:
            optimization_results: Résultats d'optimisation formatés
            
        Returns:
            dict: Résumé comparatif
        """
        fastest_metrics = ResultFormatter.format_summary_metrics(optimization_results.get("fastest"))
        cheapest_metrics = ResultFormatter.format_summary_metrics(optimization_results.get("cheapest"))
        min_tolls_metrics = ResultFormatter.format_summary_metrics(optimization_results.get("min_tolls"))
        
        return {
            "fastest": fastest_metrics,
            "cheapest": cheapest_metrics,
            "min_tolls": min_tolls_metrics,
            "status": optimization_results.get("status"),
            "has_valid_routes": any([
                fastest_metrics["cost"] is not None,
                cheapest_metrics["cost"] is not None,
                min_tolls_metrics["cost"] is not None
            ])
        }