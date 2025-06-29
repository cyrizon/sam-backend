"""
Segment Calculator
==================

Calcul des segments de route via les appels ORS optimisés.
ÉTAPE 7 de l'algorithme d'optimisation.
"""

from typing import List, Dict


class SegmentCalculator:
    """
    Calculateur de segments optimisés.
    Responsabilité : ÉTAPE 7 de l'algorithme d'optimisation.
    """
    
    def __init__(self, ors_service):
        """
        Initialise le calculateur avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """
        self.ors = ors_service
    
    def calculate_segments_routes(
        self,
        segments_config: List[Dict],
        creation_result: Dict
    ) -> List[Dict]:
        """
        ÉTAPE 7: Calcule les routes pour chaque segment via ORS.
        
        Args:
            segments_config: Configuration des segments à calculer (depuis segment_creator)
            creation_result: Résultat de la création de segments (étape 6)
            
        Returns:
            Liste des segments calculés avec leurs routes
        """
        print("🛣️ Étape 7: Calcul des routes par segment...")
        
        if not segments_config:
            print("❌ Aucun segment à calculer")
            return []
        
        calculated_segments = []
        
        for i, segment in enumerate(segments_config):
            print(f"   📍 Calcul segment {i+1}/{len(segments_config)}...")
            
            # Récupérer les coordonnées début/fin
            start_point = segment.get('start_point')
            end_point = segment.get('end_point')
            avoid_tolls = segment.get('avoid_tolls', False)
            
            if not start_point or not end_point:
                print(f"   ❌ Coordonnées manquantes pour segment {i+1}")
                continue
            
            try:
                # Appeler ORS selon le flag péage
                if avoid_tolls:
                    # Éviter les péages
                    print(f"     🚫 Éviter péages : {start_point} -> {end_point}")
                    route = self.ors.get_route_avoid_tollways([start_point, end_point])
                else:
                    # Autoriser les péages
                    print(f"     💰 Avec péages : {start_point} -> {end_point}")
                    route = self.ors.get_base_route([start_point, end_point])
                
                if route:
                    # Extraire les informations utiles de la réponse ORS
                    segment_result = self._extract_segment_info(route, segment, i, avoid_tolls)
                    calculated_segments.append(segment_result)
                    print(f"     ✅ Segment {i+1} calculé")
                else:
                    print(f"     ❌ Échec ORS pour segment {i+1}")
                    
            except Exception as e:
                print(f"     ❌ Erreur calcul segment {i+1}: {e}")
        
        print(f"✅ {len(calculated_segments)} segments calculés sur {len(segments_config)}")
        return calculated_segments
    
    def _extract_segment_info(self, ors_response: Dict, segment_config: Dict, index: int, avoid_tolls: bool) -> Dict:
        """
        Extrait les informations utiles de la réponse ORS.
        
        Args:
            ors_response: Réponse complète d'ORS
            segment_config: Configuration du segment
            index: Index du segment
            avoid_tolls: Flag éviter péages
            
        Returns:
            Segment avec informations extraites
        """
        try:
            # Extraire les données principales du premier feature
            feature = ors_response.get('features', [{}])[0]
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            # Informations de résumé
            summary = properties.get('summary', {})
            distance = summary.get('distance', 0)  # en mètres
            duration = summary.get('duration', 0)  # en secondes
            
            # Informations sur les péages
            extras = properties.get('extras', {})
            tollways_info = extras.get('tollways', {})
            tollways_summary = tollways_info.get('summary', [])
            
            # Coordonnées de la géométrie
            coordinates = geometry.get('coordinates', [])
            
            # Segments détaillés
            segments = properties.get('segments', [])
            
            return {
                'segment_id': segment_config.get('segment_id', index),
                'segment_type': segment_config.get('segment_type', 'direct'),
                'start_point': segment_config.get('start_point'),
                'end_point': segment_config.get('end_point'),
                'has_tolls': not avoid_tolls,
                'calculation_method': 'avoid_tolls' if avoid_tolls else 'with_tolls',
                
                # Données extraites d'ORS
                'distance_m': distance,
                'duration_s': duration,
                'distance_km': round(distance / 1000, 2),
                'duration_min': round(duration / 60, 1),
                
                # Géométrie complète
                'geometry': geometry,
                'coordinates': coordinates,
                
                # Informations péages
                'tollways_info': tollways_summary,
                'segments_detail': segments,
                
                # Réponse ORS complète (si besoin pour debug)
                'ors_response': ors_response
            }
            
        except Exception as e:
            print(f"     ⚠️ Erreur extraction données ORS: {e}")
            # Fallback avec données minimales
            return {
                'segment_id': segment_config.get('segment_id', index),
                'segment_type': segment_config.get('segment_type', 'direct'),
                'start_point': segment_config.get('start_point'),
                'end_point': segment_config.get('end_point'),
                'has_tolls': not avoid_tolls,
                'calculation_method': 'avoid_tolls' if avoid_tolls else 'with_tolls',
                'error': str(e),
                'ors_response': ors_response
            }

