"""
route_alternative_generator.py
------------------------------

Responsabilité : Générer des routes alternatives en évitant des péages spécifiques.
Gère les appels ORS et la validation des routes alternatives.
"""

from src.services.toll.route_calculator import RouteCalculator
from src.services.common.result_formatter import ResultFormatter
from src.utils.poly_utils import avoidance_multipolygon


class RouteAlternativeGenerator:
    """
    Générateur de routes alternatives.
    Responsabilité unique : créer des routes alternatives en évitant des péages spécifiques.
    """
    
    def __init__(self, ors_service):
        """
        Initialise le générateur de routes alternatives.
        Args:
            ors_service: Service ORS pour les appels API
        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def generate_alternative_route(self, coordinates, tolls_to_avoid, veh_class, max_attempts=3):
        """
        Génère une route alternative en évitant des péages spécifiques.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            tolls_to_avoid: Liste des péages à éviter
            veh_class: Classe de véhicule
            max_attempts: Nombre maximum de tentatives avec rayons différents
            
        Returns:
            dict: Route alternative formatée ou None si échec
        """
        if not tolls_to_avoid:
            return None
        
        # Rayons progressifs pour l'évitement
        radii = [300, 600, 1000]
        
        for attempt, radius in enumerate(radii[:max_attempts], 1):
            try:
                print(f"   🔄 Tentative {attempt}/{max_attempts} (rayon {radius}m)")
                
                # Créer les polygones d'évitement
                avoid_polygons = avoidance_multipolygon(tolls_to_avoid, radius_m=radius)
                
                # Calculer la route avec évitement
                alternative_route = self.ors.get_route_avoiding_polygons(
                    coordinates, avoid_polygons, include_tollways=True
                )
                
                if not alternative_route or 'features' not in alternative_route:
                    print(f"   ❌ Tentative {attempt}: Pas de route ORS")
                    continue
                
                # Analyser la route alternative
                analysis = self._analyze_alternative_route(alternative_route, tolls_to_avoid, veh_class)
                
                if analysis['success']:
                    print(f"   ✅ Tentative {attempt}: {analysis['toll_count']} péages, {analysis['cost']:.2f}€")
                    return analysis['formatted_result']
                else:
                    print(f"   ⚠️ Tentative {attempt}: {analysis['message']}")
                    
            except Exception as e:
                print(f"   ❌ Tentative {attempt}: Erreur {e}")
                continue
        
        print(f"   ❌ Toutes les tentatives ont échoué")
        return None
    
    def _analyze_alternative_route(self, route_data, tolls_to_avoid, veh_class):
        """
        Analyse une route alternative pour vérifier qu'elle évite bien les péages voulus.
        
        Args:
            route_data: Données de route GeoJSON
            tolls_to_avoid: Péages qu'on voulait éviter
            veh_class: Classe de véhicule
            
        Returns:
            dict: Résultats de l'analyse
        """
        try:
            # Détecter les péages sur la route alternative
            tolls_dict = self.route_calculator.locate_and_cost_tolls(route_data, veh_class)
            route_tolls = tolls_dict.get("on_route", [])
            
            # Vérifier quels péages ont été évités
            avoided_toll_ids = set(t.get('id') for t in tolls_to_avoid)
            remaining_toll_ids = set(t.get('id') for t in route_tolls)
            
            successfully_avoided = avoided_toll_ids - remaining_toll_ids
            still_present = avoided_toll_ids & remaining_toll_ids
            
            # Calculer les métriques
            route_cost = sum(t.get("cost", 0) for t in route_tolls)
            route_duration = route_data["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(route_tolls)
            
            # Déterminer si c'est un succès
            success = len(successfully_avoided) > 0  # Au moins un péage évité
            
            if success:
                message = f"Évités: {len(successfully_avoided)}, Restants: {len(still_present)}"
            else:
                message = f"Aucun péage évité ({len(still_present)} restants)"
            
            # Formater le résultat
            formatted_result = None
            if success:
                formatted_result = ResultFormatter.format_route_result(
                    route_data, route_cost, route_duration, toll_count
                )
            
            return {
                'success': success,
                'toll_count': toll_count,
                'cost': route_cost,
                'duration': route_duration,
                'avoided_count': len(successfully_avoided),
                'still_present_count': len(still_present),
                'message': message,
                'formatted_result': formatted_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur analyse: {e}',
                'formatted_result': None
            }
    
    def batch_generate_alternatives(self, coordinates, avoidance_combinations, veh_class):
        """
        Génère plusieurs routes alternatives en lot.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            avoidance_combinations: Liste des combinaisons d'évitement à tester
            veh_class: Classe de véhicule
            
        Returns:
            list: Routes alternatives réussies, triées par qualité
        """
        successful_alternatives = []
        
        for i, combination in enumerate(avoidance_combinations[:10], 1):  # Limiter à 10 tests
            tolls_to_avoid = combination['tolls_to_avoid']
            expected_tolls = combination['expected_tolls']
            
            print(f"🔍 Test {i}: Éviter {len(tolls_to_avoid)} péages → {expected_tolls} attendus")
            
            alternative = self.generate_alternative_route(coordinates, tolls_to_avoid, veh_class)
            
            if alternative:
                # Ajouter des métadonnées sur la qualité
                alternative['avoidance_info'] = {
                    'tolls_avoided': len(tolls_to_avoid),
                    'expected_tolls': expected_tolls,
                    'priority_score': combination['priority']
                }
                successful_alternatives.append(alternative)
                
                # Si on a trouvé le nombre de péages attendu, on peut s'arrêter
                actual_tolls = alternative.get('toll_count', 0)
                if actual_tolls <= expected_tolls:
                    print(f"✅ Solution optimale trouvée: {actual_tolls} péages")
                    break
        
        # Trier par nombre de péages puis par coût
        successful_alternatives.sort(key=lambda x: (x.get('toll_count', 999), x.get('cost', 999)))
        
        return successful_alternatives
