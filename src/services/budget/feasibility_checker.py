"""
feasibility_checker.py
---------------------

Vérificateur de faisabilité budgétaire précoce.
Responsabilité unique : déterminer si un budget est réalisable avant calculs coûteux.
"""

from src.services.budget.route_calculator import BudgetRouteCalculator
from src.services.budget.constants import BudgetOptimizationConfig as Config


class BudgetFeasibilityChecker:
    """Vérificateur de faisabilité budgétaire pour éviter les calculs inutiles."""
    
    def __init__(self, ors_service):
        self.ors = ors_service
    def should_check_feasibility(self, max_price, max_price_percent):
        """Détermine si on doit faire une vérification de faisabilité budgétaire."""
        # Faire la vérification pour TOUS les budgets absolus
        # Ne PAS faire pour les budgets en pourcentage car on ne connaît pas encore le coût de base
        return (max_price is not None and max_price > 0)
    
    def check_budget_feasibility_early(self, coordinates, max_price, max_price_percent, veh_class):
        """
        Vérification précoce : le budget demandé est-il réalisable par rapport aux péages disponibles ?
        
        Returns:
            bool: True si fallback nécessaire (budget impossible), False sinon
        """
        try:
            print("🔍 Vérification précoce de faisabilité budgétaire...")
            
            # Calculer la route de base pour analyser les péages
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
                budget_limit = base_cost * max_price_percent
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
    
    def check_percentage_budget_feasibility(self, base_cost, max_price_percent, tolls_dict):
        """
        Vérification de faisabilité spécifique aux budgets en pourcentage.
        Appelée APRÈS le calcul de la route de base.
        
        Args:
            base_cost: Coût de la route de base en euros
            max_price_percent: Pourcentage de budget demandé (0.4 = 40%)
            tolls_dict: Dictionnaire des péages trouvés {"on_route": [...], "nearby": [...]}
            
        Returns:
            bool: True si budget impossible (déclencher fallback), False sinon
        """
        try:
            print("🔍 Vérification de faisabilité pour budget pourcentage...")
            
            # Calculer le budget effectif en euros
            budget_limit = base_cost * max_price_percent
            print(f"💰 Budget effectif: {budget_limit:.2f}€ ({max_price_percent*100:.1f}% de {base_cost:.2f}€)")
            
            # Récupérer tous les péages (sur route + proximité)
            all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
            
            if not all_tolls:
                print("📍 Aucun péage trouvé - Budget probablement réalisable")
                return False
            
            # Calculer le coût minimal possible
            min_cost = self._calculate_minimum_possible_cost(all_tolls)
            print(f"💡 Coût minimal possible: {min_cost:.2f}€")
            
            # Vérification de faisabilité
            if budget_limit < min_cost:
                print(f"🚫 Budget pourcentage ({budget_limit:.2f}€) < Coût minimal possible ({min_cost:.2f}€)")
                print("→ Budget impossible à respecter - Fallback justifié")
                return True  # Budget impossible, déclencher fallback
            else:
                print(f"✅ Budget pourcentage ({budget_limit:.2f}€) >= Coût minimal possible ({min_cost:.2f}€)")
                print("→ Budget potentiellement réalisable, optimisation justifiée")
                return False  # Budget possible, continuer optimisation
                
        except Exception as e:
            print(f"⚠️  Erreur lors de la vérification de faisabilité pourcentage: {e}")
            return False  # En cas d'erreur, ne pas déclencher fallback précoce

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
