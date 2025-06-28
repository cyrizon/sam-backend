"""
Shapely Verifier
================

Vérification précise des péages avec Shapely (méthode de l'ancienne version).
Responsabilité unique : vérification Shapely pour rattraper les péages manqués.
"""

from typing import List, Dict, Tuple
from shapely.geometry import Point, LineString


class ShapelyVerifier:
    """Vérificateur de péages avec Shapely ultra-précis."""
    
    # Seuil strict pour péages SUR la route avec Shapely
    SHAPELY_ON_ROUTE_THRESHOLD = 5.0  # 5 mètres
    
    @staticmethod
    def verify_tolls_with_shapely(
        tolls_on_route: List[Dict], 
        tolls_around: List[Dict], 
        route_coordinates: List[List[float]]
    ) -> Dict:
        """
        Phase 4: Vérification Shapely précise de tous les péages.
        
        Args:
            tolls_on_route: Péages détectés "sur route" par l'algorithme optimisé
            tolls_around: Péages détectés "autour" par l'algorithme optimisé  
            route_coordinates: Coordonnées de la route
            
        Returns:
            Résultats de la vérification Shapely
        """
        print("🔍 Phase 4: Vérification Shapely précise...")
        
        if not route_coordinates or len(route_coordinates) < 2:
            print("❌ Coordonnées invalides pour Shapely")
            return ShapelyVerifier._create_empty_verification()
        
        # Créer la LineString Shapely
        try:
            route_line = LineString(route_coordinates)
        except Exception as e:
            print(f"❌ Erreur création LineString : {e}")
            return ShapelyVerifier._create_empty_verification()
        
        # Vérifier tous les péages (on_route + around)
        all_tolls_to_verify = []
        
        # Ajouter péages "sur route" avec leur source
        for toll_data in tolls_on_route:
            toll = toll_data.get('toll') if isinstance(toll_data, dict) else toll_data
            all_tolls_to_verify.append({
                'toll': toll,
                'source': 'optimized_on_route'
            })
        
        # Ajouter péages "autour" avec leur source  
        for toll_data in tolls_around:
            toll = toll_data.get('toll') if isinstance(toll_data, dict) else toll_data
            all_tolls_to_verify.append({
                'toll': toll,
                'source': 'optimized_around'
            })
        
        print(f"   🎯 Vérification Shapely de {len(all_tolls_to_verify)} péages...")
        
        # Vérification Shapely pour tous
        verified_results = ShapelyVerifier._verify_tolls_batch(
            all_tolls_to_verify, route_line
        )
        
        return verified_results
    
    @staticmethod
    def _verify_tolls_batch(
        tolls_to_verify: List[Dict], 
        route_line: LineString
    ) -> Dict:
        """
        Vérification par lot avec Shapely.
        
        Args:
            tolls_to_verify: Liste des péages à vérifier
            route_line: LineString Shapely de la route
            
        Returns:
            Résultats de vérification
        """
        results = {
            'shapely_on_route': [],      # < 5m avec Shapely
            'shapely_around': [],        # >= 5m avec Shapely
            'verification_stats': {
                'total_verified': 0,
                'confirmed_on_route': 0,
                'moved_to_around': 0,
                'promoted_to_route': 0,
                'shapely_errors': 0
            }
        }
        
        for toll_item in tolls_to_verify:
            toll = toll_item['toll']
            source = toll_item['source']
            
            try:
                # Vérification Shapely précise
                shapely_distance = ShapelyVerifier._calculate_shapely_distance(
                    toll, route_line
                )
                
                if shapely_distance is None:
                    results['verification_stats']['shapely_errors'] += 1
                    continue
                
                # Classification selon seuil Shapely (5m)
                if shapely_distance <= ShapelyVerifier.SHAPELY_ON_ROUTE_THRESHOLD:
                    results['shapely_on_route'].append({
                        'toll': toll,
                        'shapely_distance': shapely_distance,
                        'source': source,
                        'verification_method': 'shapely'
                    })
                    results['verification_stats']['confirmed_on_route'] += 1
                    
                    # Statistique : promu depuis "around" ?
                    if source == 'optimized_around':
                        results['verification_stats']['promoted_to_route'] += 1
                    
                else:
                    results['shapely_around'].append({
                        'toll': toll,
                        'shapely_distance': shapely_distance,
                        'source': source,
                        'verification_method': 'shapely'
                    })
                    
                    # Statistique : rétrogradé depuis "on_route" ?
                    if source == 'optimized_on_route':
                        results['verification_stats']['moved_to_around'] += 1
                
                results['verification_stats']['total_verified'] += 1
                
            except Exception as e:
                print(f"   ⚠️ Erreur vérification péage {toll.osm_name}: {e}")
                results['verification_stats']['shapely_errors'] += 1
        
        ShapelyVerifier._print_verification_summary(results)
        return results
    
    @staticmethod
    def _calculate_shapely_distance(toll, route_line: LineString) -> float:
        """
        Calcule la distance Shapely précise toll → route.
        
        Args:
            toll: Objet péage avec coordonnées
            route_line: LineString Shapely
            
        Returns:
            Distance en mètres, None si erreur
        """
        try:
            # Extraire coordonnées du péage
            if hasattr(toll, 'osm_coordinates'):
                coords = toll.osm_coordinates
            elif hasattr(toll, 'coordinates'):
                coords = toll.coordinates
            else:
                return None
            
            if not coords or len(coords) < 2:
                return None
            
            # Créer Point Shapely
            toll_point = Point(coords[0], coords[1])
            
            # Distance Shapely en degrés
            distance_degrees = route_line.distance(toll_point)
            
            # Conversion degrés → mètres (approximation)
            distance_meters = distance_degrees * 111139  # 1 degré ≈ 111139m
            
            return distance_meters
            
        except Exception as e:
            print(f"   ❌ Erreur calcul Shapely : {e}")
            return None
    
    @staticmethod
    def _create_empty_verification() -> Dict:
        """Crée un résultat de vérification vide."""
        return {
            'shapely_on_route': [],
            'shapely_around': [],
            'verification_stats': {
                'total_verified': 0,
                'confirmed_on_route': 0,
                'moved_to_around': 0,
                'promoted_to_route': 0,
                'shapely_errors': 0
            }
        }
    
    @staticmethod
    def _print_verification_summary(results: Dict) -> None:
        """Affiche le résumé de la vérification Shapely."""
        stats = results['verification_stats']
        
        print(f"   ✅ Vérification Shapely terminée:")
        print(f"      📊 {stats['total_verified']} péages vérifiés")
        print(f"      🎯 {stats['confirmed_on_route']} confirmés SUR route (<5m)")
        print(f"      📍 {stats['promoted_to_route']} promus vers route")
        print(f"      📉 {stats['moved_to_around']} rétrogradés vers autour")
        if stats['shapely_errors'] > 0:
            print(f"      ⚠️ {stats['shapely_errors']} erreurs de vérification")