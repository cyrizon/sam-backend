"""
Route Assembler
===============

Module pour assembler les segments de route calculés.
Version simplifiée pour l'optimiseur de routes.
"""

from typing import List, Dict
from ..toll_analysis.toll_identifier import TollIdentifier


class RouteAssembler:
    """Assembleur de routes simplifié."""
    
    @staticmethod
    def assemble_final_route(
        segments: List[Dict], 
        target_tolls: int, 
        selected_tolls: List = None
    ) -> Dict:
        """
        Assemble la route finale à partir des segments calculés.
        
        Args:
            segments: Liste des segments calculés
            target_tolls: Nombre de péages demandé
            selected_tolls: Péages sélectionnés (optionnel)
            
        Returns:
            Route finale assemblée avec métadonnées
        """
        print("🔧 Étape 8: Assemblage de la route finale...")
        print(f"   📊 Assemblage de {len(segments)} segments")
        
        if not segments:
            print("❌ Aucun segment à assembler")
            return None
        
        # Extraire et assembler les données de tous les segments
        all_coords = []
        all_instructions = []
        total_distance = 0
        total_duration = 0
        
        for i, segment in enumerate(segments):
            # Utiliser les données extraites par segment_calculator
            coords = segment.get('coordinates', [])
            distance = segment.get('distance_m', 0)
            duration = segment.get('duration_s', 0)
            segments_detail = segment.get('segments_detail', [])
            
            print(f"   📍 Segment {i+1}: {distance/1000:.1f}km, {len(coords)} points")
            
            # Extraire les instructions depuis segments_detail
            instructions = []
            for seg_detail in segments_detail:
                steps = seg_detail.get('steps', [])
                for step in steps:
                    instructions.append({
                        'instruction': step.get('instruction', ''),
                        'name': step.get('name', ''),
                        'distance': step.get('distance', 0),
                        'duration': step.get('duration', 0)
                    })
            
            # Premier segment : ajouter tous les points
            if i == 0:
                all_coords.extend(coords)
                all_instructions.extend(instructions)
            else:
                # Segments suivants : éviter la duplication du premier point
                all_coords.extend(coords[1:] if coords else [])
                all_instructions.extend(instructions)
            
            total_distance += distance
            total_duration += duration
        
        # Construire la route finale
        final_route = RouteAssembler._build_route_geojson(
            all_coords, total_distance, total_duration, all_instructions
        )
        
        # RE-ANALYSE: Identifier les vrais péages empruntés sur la route finale
        print("   🔍 Re-analyse des péages sur la route finale...")
        try:
            toll_identifier = TollIdentifier()
            reanalysis_result = toll_identifier.identify_tolls_on_route(all_coords, None)
            
            if reanalysis_result.get('identification_success'):
                actual_tolls_on_route = reanalysis_result.get('tolls_on_route', [])
                print(f"   🎯 {len(actual_tolls_on_route)} péages réellement empruntés détectés")
                
                # Utiliser les péages re-analysés au lieu des sélectionnés pour le calcul des coûts
                toll_cost, actual_toll_count, toll_details = RouteAssembler._calculate_toll_costs_from_selected(
                    final_route, actual_tolls_on_route
                )
            else:
                print("   ⚠️ Échec re-analyse - utilisation des péages sélectionnés")
                # Fallback sur les péages sélectionnés
                toll_cost, actual_toll_count, toll_details = RouteAssembler._calculate_toll_costs_from_selected(
                    final_route, selected_tolls
                )
        except Exception as e:
            print(f"   ❌ Erreur re-analyse: {e} - utilisation des péages sélectionnés")
            # Fallback sur les péages sélectionnés
            toll_cost, actual_toll_count, toll_details = RouteAssembler._calculate_toll_costs_from_selected(
                final_route, selected_tolls
            )
        
        # Extraire les informations des péages pour toll_info
        toll_names = [toll.get('from_name', 'Péage') for toll in toll_details]
        if toll_details:  # Ajouter le dernier péage
            toll_names.append(toll_details[-1].get('to_name', 'Péage'))
        toll_systems = list(set(toll.get('operator', 'Inconnu') for toll in toll_details))
        toll_coordinates = [toll.get('from_coordinates', [0, 0]) for toll in toll_details]
        if toll_details:  # Ajouter les coordonnées du dernier péage
            toll_coordinates.append(toll_details[-1].get('to_coordinates', [0, 0]))
        
        print(f"✅ Route assemblée: {total_distance/1000:.1f}km, "
              f"{total_duration/60:.1f}min, {toll_cost}€, {actual_toll_count} péages")
        
        return {
            'route': final_route,
            'target_tolls': target_tolls,
            'found_solution': 'optimization_success',
            'respects_constraint': actual_toll_count >= target_tolls if target_tolls > 0 else True,
            'strategy_used': 'intelligent_optimization',
            'distance': total_distance,
            'duration': total_duration,
            'instructions': all_instructions,
            'cost': toll_cost,
            'toll_count': actual_toll_count,
            'tolls': toll_details,
            'segments': {
                'count': len(segments),
                'toll_segments': len([s for s in segments if s.get('has_tolls', False)]),
                'free_segments': len([s for s in segments if not s.get('has_tolls', False)])
            },
            'toll_info': {
                'selected_tolls': toll_names,
                'toll_systems': toll_systems,
                'coordinates': toll_coordinates
            }
        }
    
    @staticmethod
    def _build_route_geojson(
        coordinates: List[List[float]], 
        distance: float, 
        duration: float,
        instructions: List[Dict] = None
    ) -> Dict:
        """
        Construit le GeoJSON de la route finale.
        
        Args:
            coordinates: Coordonnées de la route
            distance: Distance totale en mètres
            duration: Durée totale en secondes
            instructions: Instructions de navigation
            
        Returns:
            GeoJSON de la route
        """
        properties = {
            "summary": {
                "distance": distance,
                "duration": duration
            }
        }
        
        if instructions:
            properties["instructions"] = instructions
        
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString", 
                    "coordinates": coordinates
                },
                "properties": properties
            }]
        }
    
    @staticmethod
    def _calculate_toll_costs(route: Dict) -> tuple:
        """
        Calcule les coûts de péages pour la route assemblée avec le cache V2 (binômes consécutifs).
        
        Args:
            route: Route au format GeoJSON
            
        Returns:
            Tuple (coût_total, détails_péages)
        """
        try:
            print("   💰 Identification des péages sur la route assemblée...")
            from ..utils.cache_accessor import CacheAccessor

            # Extraire les coordonnées de la route
            if route.get("type") == "FeatureCollection":
                features = route.get("features", [])
                if features and features[0].get("geometry", {}).get("type") == "LineString":
                    coordinates = features[0]["geometry"]["coordinates"]
                else:
                    print("   ⚠️ Pas de coordonnées LineString trouvées")
                    return 0.0, 0, []
            else:
                print("   ⚠️ Format de route non reconnu")
                return 0.0, 0, []

            # Utiliser le TollIdentifier pour identifier les péages
            toll_identifier = TollIdentifier()
            identification_result = toll_identifier.identify_tolls_on_route(coordinates)

            if not identification_result.get('identification_success'):
                print("   ⚠️ Échec identification des péages")
                return 0.0, 0, []

            tolls_on_route = identification_result.get('tolls_on_route', [])
            print(f"   ✅ {len(tolls_on_route)} péages identifiés sur la route")

            # Calcul du coût total par binômes consécutifs
            total_cost = 0.0
            toll_details = []
            vehicle_category = "1"  # Peut être paramétré

            # Récupérer les objets TollBoothStation
            toll_stations = [toll_data.get('toll') for toll_data in tolls_on_route if toll_data.get('toll')]
            print([toll.name for toll in toll_stations])

            for i in range(len(toll_stations) - 1):
                toll_from = toll_stations[i]
                toll_to = toll_stations[i + 1]
                print(toll_stations[i].name, toll_stations[i + 1].name)
                cost = CacheAccessor.calculate_toll_cost(toll_from, toll_to, vehicle_category)
                if cost is None:
                    cost = 0.0
                total_cost += cost
                # Ajout d'un détail pour chaque binôme
                toll_details.append({
                    'from_id': toll_from.osm_id,
                    'from_name': getattr(toll_from, 'display_name', getattr(toll_from, 'nom', 'Péage')),
                    'to_id': toll_to.osm_id,
                    'to_name': getattr(toll_to, 'display_name', getattr(toll_to, 'nom', 'Péage')),
                    'operator': toll_from.operator or "Inconnu",
                    'autoroute': toll_from.highway_ref or getattr(toll_from, 'autoroute', ''),
                    'from_coordinates': toll_from.coordinates,
                    'to_coordinates': toll_to.coordinates,
                    'type': 'ouvert' if toll_from.is_open_toll else 'fermé',
                    'cost': cost
                })

            print(f"   💰 Coût total calculé : {total_cost}€ pour {len(toll_details)} binômes de péages")
            
            # Retourner le coût total et le nombre réel de péages (pas les binômes)
            actual_toll_count = len(toll_stations)
            
            # Créer une structure pour le retour : (coût, nombre_péages, détails_binômes)
            return total_cost, actual_toll_count, toll_details

        except Exception as e:
            print(f"   ❌ Erreur calcul coûts péages : {e}")
            return 0.0, 0, []
    
    @staticmethod
    def _calculate_toll_costs_from_selected(route: Dict, selected_tolls: List = None) -> tuple:
        """
        Calcule les coûts de péages basés sur les péages sélectionnés plutôt que ré-identifiés.
        
        Args:
            route: Route au format GeoJSON
            selected_tolls: Liste des péages sélectionnés (TollBoothStation objects)
            
        Returns:
            Tuple (coût_total, nombre_péages, détails_péages)
        """
        if not selected_tolls:
            print("   💰 Aucun péage sélectionné - route sans péage")
            return 0.0, 0, []
        
        try:
            print(f"   💰 Calcul des coûts pour {len(selected_tolls)} péages sélectionnés...")
            from ..utils.cache_accessor import CacheAccessor

            # Filtrer pour ne garder que les TollBoothStation ou convertir les dictionnaires
            toll_stations = []
            for toll_data in selected_tolls:
                toll_station = None
                
                # Cas 1: Dict avec 'toll' (résultat de ré-analyse)
                if isinstance(toll_data, dict) and 'toll' in toll_data:
                    toll_station = toll_data['toll']
                    
                # Cas 2: Objet TollBoothStation direct
                elif hasattr(toll_data, 'osm_id') and hasattr(toll_data, 'name'):
                    toll_station = toll_data
                    
                # Cas 3: Dict simple (péages sélectionnés) - convertir en cherchant dans le cache
                elif isinstance(toll_data, dict) and 'osm_id' in toll_data:
                    osm_id = toll_data['osm_id']
                    # Chercher l'objet TollBoothStation correspondant dans le cache
                    toll_station = RouteAssembler._find_toll_in_cache(toll_data)
                    if not toll_station:
                        print(f"   ⚠️ Péage {toll_data.get('name', osm_id)} non trouvé dans le cache")
                        continue
                
                if toll_station and hasattr(toll_station, 'osm_id') and hasattr(toll_station, 'name'):
                    toll_stations.append(toll_station)
                    print(f"   📍 Péage ajouté: {toll_station.name}")
            
            print(f"   ✅ {len(toll_stations)} stations de péage à traiter")

            # Calcul du coût total par binômes consécutifs
            total_cost = 0.0
            toll_details = []
            vehicle_category = "1"  # Peut être paramétré

            if len(toll_stations) == 0:
                return 0.0, 0, []
            elif len(toll_stations) == 1:
                # Un seul péage - coût fixe ou pas de coût
                print("   ⚠️ Un seul péage - pas de binôme possible")
                return 0.0, 1, [{
                    'from_name': toll_stations[0].name,
                    'to_name': toll_stations[0].name,
                    'cost': 0.0,
                    'operator': getattr(toll_stations[0], 'operator', 'Inconnu'),
                    'from_coordinates': toll_stations[0].coordinates,
                    'to_coordinates': toll_stations[0].coordinates
                }]

            # Calcul par binômes pour plusieurs péages
            for i in range(len(toll_stations) - 1):
                toll_from = toll_stations[i]
                toll_to = toll_stations[i + 1]
                
                print(f"   💳 Binôme: {toll_from.name} → {toll_to.name}")
                cost = CacheAccessor.calculate_toll_cost(toll_from, toll_to, vehicle_category)
                if cost is None:
                    cost = 0.0
                
                total_cost += cost
                
                # Ajout d'un détail pour chaque binôme
                toll_details.append({
                    'from_name': toll_from.name,
                    'to_name': toll_to.name,
                    'cost': cost,
                    'operator': getattr(toll_from, 'operator', 'Inconnu'),
                    'from_coordinates': toll_from.coordinates,
                    'to_coordinates': toll_to.coordinates
                })
                
                print(f"     💰 Coût: {cost}€")

            print(f"   ✅ Coût total calculé: {total_cost}€ pour {len(toll_details)} binômes")
            return total_cost, len(toll_stations), toll_details

        except Exception as e:
            print(f"   ❌ Erreur calcul coûts sélectionnés: {e}")
            return 0.0, 0, []
    
    @staticmethod
    def format_base_route_as_result(base_route: Dict, target_tolls: int) -> Dict:
        """
        Formate une route de base comme résultat final.
        Utilisé quand l'optimisation n'est pas nécessaire.
        Identifie également les péages sur cette route de base.
        
        Args:
            base_route: Route de base (réponse ORS directe)
            target_tolls: Nombre de péages demandé
            
        Returns:
            Route formatée comme résultat d'optimisation avec péages identifiés
        """
        print("   📋 Formatage de la route de base avec identification des péages...")
        
        # Extraire les données de la réponse ORS
        feature = base_route.get('features', [{}])[0]
        properties = feature.get('properties', {})
        summary = properties.get('summary', {})
        
        distance = summary.get('distance', 0)
        duration = summary.get('duration', 0)
        
        # Extraire les instructions depuis les segments
        instructions = []
        segments = properties.get('segments', [])
        for segment in segments:
            steps = segment.get('steps', [])
            for step in steps:
                instructions.append({
                    'instruction': step.get('instruction', ''),
                    'name': step.get('name', ''),
                    'distance': step.get('distance', 0),
                    'duration': step.get('duration', 0)
                })
        
        print("   💰 Identification des péages sur la route assemblée...")
        # Identifier et calculer les coûts de péages avec le système V2
        toll_cost, actual_toll_count, toll_details = RouteAssembler._calculate_toll_costs(base_route)
        
        # Extraire les noms des péages pour toll_info
        toll_names = [toll.get('from_name', 'Péage') for toll in toll_details]
        if toll_details:  # Ajouter le dernier péage
            toll_names.append(toll_details[-1].get('to_name', 'Péage'))
        toll_coordinates = [toll.get('from_coordinates', [0, 0]) for toll in toll_details]
        if toll_details:  # Ajouter les coordonnées du dernier péage
            toll_coordinates.append(toll_details[-1].get('to_coordinates', [0, 0]))
        
        print(f"   ✅ Route de base formatée : {distance/1000:.1f}km, {actual_toll_count} péages")
        
        return {
            'route': base_route,
            'target_tolls': target_tolls,
            'found_solution': 'base_route_sufficient',
            'respects_constraint': actual_toll_count >= target_tolls if target_tolls > 0 else True,
            'strategy_used': 'base_route',
            'distance': distance,
            'duration': duration,
            'instructions': instructions,
            'cost': toll_cost,
            'toll_count': actual_toll_count,
            'tolls': toll_details,
            'segments': {'count': 1, 'toll_segments': 1 if toll_details else 0, 'free_segments': 1 if not toll_details else 0},
            'toll_info': {
                'selected_tolls': toll_names,
                'toll_systems': list(set(toll.get('operator', 'Inconnu') for toll in toll_details)),
                'coordinates': toll_coordinates
            }
        }
    
    @staticmethod
    def _find_toll_in_cache(toll_dict_or_osm_id):
        """
        Trouve un objet TollBoothStation dans le cache à partir d'un dictionnaire ou osm_id.
        
        Args:
            toll_dict_or_osm_id: Dictionnaire péage ou osm_id string
            
        Returns:
            TollBoothStation ou None
        """
        try:
            from ..utils.cache_accessor import CacheAccessor
            
            # Extraire l'osm_id
            if isinstance(toll_dict_or_osm_id, dict):
                osm_id = toll_dict_or_osm_id.get('osm_id')
            else:
                osm_id = toll_dict_or_osm_id
            
            if not osm_id:
                return None
            
            # Chercher dans le cache V2
            toll_stations = CacheAccessor.get_toll_stations()
            for toll_booth in toll_stations:
                if toll_booth.osm_id == osm_id:
                    return toll_booth
            
            print(f"   ⚠️ Péage {osm_id} non trouvé dans le cache ({len(toll_stations)} péages disponibles)")
            return None
            
        except Exception as e:
            print(f"   ❌ Erreur recherche cache: {e}")
            return None
