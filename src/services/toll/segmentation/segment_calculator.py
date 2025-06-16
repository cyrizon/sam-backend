"""
segment_calculator.py
--------------------

Responsabilité : Calculer et valider un segment individuel de route.
Gère l'évitement des péages non désirés sur un segment spécifique.
"""

from src.services.toll_locator import locate_tolls
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.constants import TollOptimizationConfig as Config
from src.utils.poly_utils import avoidance_multipolygon


class SegmentCalculator:
    """
    Calculateur de segments de route.
    Responsabilité unique : calculer et valider un segment entre deux points.
    """
    
    def __init__(self, ors_service):
        """
        Initialise le calculateur de segments.
        Args:            ors_service: Service ORS pour les appels API        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def calculate_segment(self, from_point, to_point, veh_class=Config.DEFAULT_VEH_CLASS, max_avoidance_attempts=5, tolls_to_avoid=None, no_avoidance=False):
        """
        Calcule un segment de route entre deux points.
        Gère automatiquement l'évitement des péages non désirés.
        
        Args:
            from_point: Point de départ [lon, lat] ou péage dict
            to_point: Point d'arrivée [lon, lat] ou péage dict  
            veh_class: Classe de véhicule
            max_avoidance_attempts: Maximum de tentatives d'évitement
            tolls_to_avoid: Liste des péages spécifiques à éviter (optionnel)
            no_avoidance: Si True, aucun évitement ne sera tenté (route directe)
            
        Returns:
            dict: {
                'success': bool,
                'segment_data': dict ou None,
                'error': str ou None
            }
        """
        # Extraire les coordonnées si ce sont des objets péages
        from_coords = self._extract_coordinates(from_point)
        to_coords = self._extract_coordinates(to_point)
        
        print(f"🔧 Calcul segment : {from_coords} → {to_coords}")
        # Si no_avoidance=True, faire seulement le calcul direct
        if no_avoidance:
            print(f"🚀 Calcul direct sans évitement")
            result = self._attempt_segment_calculation(from_coords, to_coords, veh_class)
            if result['success']:
                # Détecter les péages pour information mais ne pas les éviter
                segment_data = result['segment_data']
                detected_tolls = self._detect_tolls_on_segment(segment_data, veh_class)
                print(f"✅ Segment direct calculé avec succès")
            return result
        
        # Si des péages spécifiques à éviter sont fournis, les utiliser directement
        if tolls_to_avoid:
            print(f"🚫 Évitement de {len(tolls_to_avoid)} péages spécifiés")
            return self._calculate_segment_with_avoidance(
                from_coords, to_coords, tolls_to_avoid, veh_class, max_avoidance_attempts
            )
        
        # Sinon, comportement normal : calcul puis détection/évitement automatique
        # Tentative initiale sans évitement
        result = self._attempt_segment_calculation(from_coords, to_coords, veh_class)
        if not result['success']:
            return result
        # Vérifier les péages sur le segment calculé
        segment_data = result['segment_data']
        detected_tolls = self._detect_tolls_on_segment(segment_data, veh_class)
        
        # Si aucun péage détecté, le segment est OK
        if not detected_tolls:
            print(f"✅ Segment sans péage calculé avec succès")
            return result
        
        # Affichage détaillé des péages détectés
        toll_ids = [toll.get('id', 'NO_ID') for toll in detected_tolls]
        print(f"⚠️ {len(detected_tolls)} péages détectés : {toll_ids}")
        
        # Essayer d'éviter les péages détectés
        avoidance_result = self._calculate_segment_with_avoidance(
            from_coords, to_coords, detected_tolls, veh_class, max_avoidance_attempts
        )
        
        if avoidance_result['success']:
            return avoidance_result
        
        # Si l'évitement a échoué, retourner le segment original avec avertissement
        print(f"⚠️ Impossible d'éviter tous les péages, segment original conservé")
        return result
    
    def _extract_coordinates(self, point):
        """
        Extrait les coordonnées d'un point (peut être [lon,lat] ou objet péage).
        
        Args:
            point: [lon, lat] ou dict péage
            
        Returns:
            list: [lon, lat]
        """
        if isinstance(point, list) and len(point) == 2:
            return point
        elif isinstance(point, dict):
            # Assumons que c'est un péage avec lat/lon
            return [point.get('lon', point.get('longitude', 0)), 
                   point.get('lat', point.get('latitude', 0))]
        else:
            raise ValueError(f"Format de point invalide: {point}")
    def _attempt_segment_calculation(self, from_coords, to_coords, veh_class, avoid_polygons=None):
        """
        Tente de calculer un segment avec polygones d'évitement optionnels.
        
        Args:
            from_coords: Coordonnées de départ
            to_coords: Coordonnées d'arrivée
            veh_class: Classe de véhicule
            avoid_polygons: Polygones à éviter (optionnel)
            
        Returns:
            dict: Résultat de la tentative
        """
        try:
            coordinates = [from_coords, to_coords]
            
            # Appel ORS avec ou sans évitement
            if avoid_polygons:
                route_data = self.ors.get_route_avoiding_polygons(coordinates, avoid_polygons, include_tollways=True)
            else:
                route_data = self.ors.get_base_route(coordinates, include_tollways=True)
            
            # Vérifier si la réponse est valide
            if not route_data or 'features' not in route_data or not route_data['features']:
                return {
                    'success': False,
                    'segment_data': None,
                    'error': 'Aucune route trouvée par ORS'
                }
            
            # Extraire les données du segment (format GeoJSON)
            feature = route_data['features'][0]
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            segment_data = {
                'geometry': geometry,
                'summary': properties.get('summary', {}),
                'distance': properties.get('summary', {}).get('distance', 0),
                'duration': properties.get('summary', {}).get('duration', 0),
                'coordinates': coordinates,
                'route_data': route_data,  # Garder les données complètes pour analyse
                'properties': properties  # Inclure toutes les propriétés
            }
            
            return {
                'success': True,
                'segment_data': segment_data,
                'error': None
            }
            
        except Exception as e:            
            return {
                'success': False,
                'segment_data': None,
                'error': f'Erreur ORS: {str(e)}'
            }
    
    def _detect_tolls_on_segment(self, segment_data, veh_class):
        """
        Détecte les péages sur un segment calculé.
        Args:
            segment_data: Données du segment calculé
            veh_class: Classe de véhicule
            
        Returns:
            list: Liste des péages détectés
        """
        try:
            # Utiliser la fonction existante de localisation des péages
            route_data = segment_data['route_data']
            tolls_dict = locate_tolls(route_data)
            # Extraire seulement les péages "on_route"
            detected_tolls = tolls_dict.get("on_route", [])
            
            # Afficher les détails des péages trouvés de manière concise
            if detected_tolls:
                toll_details = []
                for toll in detected_tolls:
                    toll_id = toll.get('id', 'NO_ID')
                    toll_name = toll.get('name_base', toll.get('name', 'NO_NAME'))
                    toll_details.append(f"{toll_id}({toll_name})")
                print(f"   🎯 Péages: {', '.join(toll_details)}")
            
            return detected_tolls
            
        except Exception as e:
            print(f"⚠️ Erreur détection péages: {e}")
            return []
    
    def _calculate_segment_with_avoidance(self, from_coords, to_coords, tolls_to_avoid, veh_class, max_attempts):
        """
        Calcule un segment en évitant des péages spécifiques avec des rayons progressifs.
        
        LOGIQUE INSPIRÉE DE intelligent_avoidance :
        - Tentatives avec rayons croissants : [250, 500, 800, 1200, 1500]
        - Chaque tentative augmente le rayon d'évitement
        - Correspond à la logique de la stratégie simple
        
        Args:
            from_coords: Coordonnées de départ
            to_coords: Coordonnées d'arrivée
            tolls_to_avoid: Péages à éviter
            veh_class: Classe de véhicule
            max_attempts: Maximum de tentatives
            
        Returns:
            dict: Résultat final après évitement
        """        # Rayons progressifs comme dans intelligent_avoidance  
        radius_sequence = [250, 500, 800, 1200, 1500]
        
        best_result = None
        best_toll_count = float('inf')  # On veut le minimum de péages
        
        for attempt in range(max_attempts):
            try:
                # Utiliser le rayon correspondant à la tentative
                current_radius = radius_sequence[min(attempt, len(radius_sequence) - 1)]
                print(f"🔧 Tentative {attempt + 1}/{max_attempts} avec rayon {current_radius}m")
                
                # Créer polygones d'évitement avec le rayon actuel
                avoid_polygons = avoidance_multipolygon(tolls_to_avoid, radius_m=current_radius)
                
                # Tenter le calcul avec évitement
                result = self._attempt_segment_calculation(
                    from_coords, to_coords, veh_class, avoid_polygons
                )
                
                if not result['success']:
                    print(f"❌ Tentative {attempt + 1}: Échec ORS")
                    continue
                
                # Vérifier s'il reste des péages à éviter
                segment_data = result['segment_data']
                remaining_tolls = self._detect_tolls_on_segment(segment_data, veh_class)
                
                # Garder le meilleur résultat (celui avec le moins de péages)
                if len(remaining_tolls) < best_toll_count:
                    best_result = result
                    best_toll_count = len(remaining_tolls)
                
                if not remaining_tolls:
                    print(f"✅ Évitement réussi à la tentative {attempt + 1}")
                    return result
                
                # Il reste des péages, continuer les tentatives
                print(f"🔄 Tentative {attempt + 1}: {len(remaining_tolls)} péages restants")
                tolls_to_avoid = remaining_tolls
                
            except Exception as e:
                print(f"⚠️ Erreur tentative {attempt + 1}: {e}")
                continue
        
        # Si on a trouvé un résultat amélioré, le retourner même s'il n'est pas parfait
        if best_result and best_toll_count < float('inf'):
            print(f"✅ Meilleur résultat trouvé avec {best_toll_count} péages")
            return best_result
        
        # Toutes les tentatives ont échoué
        return {
            'success': False,
            'segment_data': None,
            'error': f'Impossible d\'éviter les péages après {max_attempts} tentatives'
        }
    
    def calculate_segment_with_smart_avoidance(self, from_point, to_point, allowed_tolls, veh_class=Config.DEFAULT_VEH_CLASS, max_avoidance_attempts=5):
        """
        Calcule un segment en évitant intelligemment les péages non autorisés.
        
        Args:
            from_point: Point de départ [lon, lat] ou péage dict
            to_point: Point d'arrivée [lon, lat] ou péage dict  
            allowed_tolls: Liste des péages autorisés (à ne pas éviter)
            veh_class: Classe de véhicule
            max_avoidance_attempts: Maximum de tentatives d'évitement
            
        Returns:
            dict: Résultat du calcul avec évitement intelligent
        """
        # Extraire les coordonnées
        from_coords = self._extract_coordinates(from_point)
        to_coords = self._extract_coordinates(to_point)
        
        print(f"🔧 Calcul segment avec évitement intelligent : {from_coords} → {to_coords}")
        
        # 1. Calcul initial direct
        result = self._attempt_segment_calculation(from_coords, to_coords, veh_class)
        if not result['success']:
            return result
        
        # 2. Détecter les péages sur le segment
        segment_data = result['segment_data']
        detected_tolls = self._detect_tolls_on_segment(segment_data, veh_class)
        
        if not detected_tolls:
            print(f"✅ Segment sans péage calculé avec succès")
            return result
        
        # 3. Identifier les péages à éviter (ceux non autorisés)
        allowed_ids = set()
        for toll in allowed_tolls:
            if isinstance(toll, dict):
                allowed_ids.add(toll.get('id'))
            else:
                allowed_ids.add(str(toll))
        
        tolls_to_avoid = []
        tolls_to_keep = []
        for toll in detected_tolls:
            toll_id = toll.get('id') if isinstance(toll, dict) else str(toll)
            if toll_id in allowed_ids:
                tolls_to_keep.append(toll)
            else:
                tolls_to_avoid.append(toll)
        
        print(f"🎯 Péages autorisés détectés: {[t.get('id', 'NO_ID') for t in tolls_to_keep]}")
        print(f"🚫 Péages à éviter: {[t.get('id', 'NO_ID') for t in tolls_to_avoid]}")
        
        # 4. Si aucun péage à éviter, retourner le résultat direct
        if not tolls_to_avoid:
            print(f"✅ Tous les péages sont autorisés")
            return result
        # 5. Essayer d'éviter les péages non autorisés (approche progressive)
        print(f"🔄 Tentative d'évitement des {len(tolls_to_avoid)} péages non autorisés...")
        
        # Stratégie 1: Essayer d'éviter tous ensemble
        avoidance_result = self._calculate_segment_with_avoidance(
            from_coords, to_coords, tolls_to_avoid, veh_class, max_avoidance_attempts
        )
        
        if avoidance_result['success']:
            # Vérifier si on a vraiment amélioré la situation
            new_segment_data = avoidance_result['segment_data']
            new_detected_tolls = self._detect_tolls_on_segment(new_segment_data, veh_class)
            
            new_tolls_to_avoid = []
            for toll in new_detected_tolls:
                toll_id = toll.get('id') if isinstance(toll, dict) else str(toll)
                if toll_id not in allowed_ids:
                    new_tolls_to_avoid.append(toll)
            
            if len(new_tolls_to_avoid) < len(tolls_to_avoid):
                print(f"✅ Évitement partiel réussi: {len(tolls_to_avoid)} → {len(new_tolls_to_avoid)} péages non autorisés")
                return avoidance_result
            else:
                print(f"🔄 Évitement complet réussi")
                return avoidance_result
        
        # Stratégie 2: Si l'évitement global échoue, essayer péage par péage (les plus problématiques d'abord)
        print(f"🔄 Évitement global échoué, tentative péage par péage...")
        best_result = result  # Garder le résultat original par défaut
        best_avoided_count = 0
        for toll_to_avoid in tolls_to_avoid:
            print(f"   🎯 Test évitement de {toll_to_avoid.get('id', 'NO_ID')}...")
            single_avoidance = self._calculate_segment_with_avoidance(
                from_coords, to_coords, [toll_to_avoid], veh_class, 3  # Moins de tentatives
            )
            
            # Examiner le résultat même s'il n'est pas marqué comme "success"
            # Car il peut y avoir une amélioration partielle
            if single_avoidance.get('segment_data'):
                single_segment_data = single_avoidance['segment_data']
                single_detected_tolls = self._detect_tolls_on_segment(single_segment_data, veh_class)
                
                single_tolls_to_avoid = []
                for toll in single_detected_tolls:
                    toll_id = toll.get('id') if isinstance(toll, dict) else str(toll)
                    if toll_id not in allowed_ids:
                        single_tolls_to_avoid.append(toll)
                
                avoided_count = len(tolls_to_avoid) - len(single_tolls_to_avoid)
                print(f"     → {avoided_count} péages évités avec cette approche")
                
                if avoided_count > best_avoided_count:
                    # Forcer success=True si on a une amélioration
                    single_avoidance['success'] = True
                    best_result = single_avoidance
                    best_avoided_count = avoided_count
            else:
                print(f"     → Échec complet pour ce péage")
        
        if best_avoided_count > 0:
            print(f"✅ Évitement partiel optimal: {best_avoided_count} péages évités")
            return best_result
        
        # 6. Si l'évitement a échoué, retourner le segment original avec avertissement
        print(f"⚠️ Évitement impossible, segment original conservé")
        return result
