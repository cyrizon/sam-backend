"""
Toll Identifier V2
==================

Identifieur de péages refactorisé avec cache V2.
Utilise CoreTollIdentifier pour les opérations principales.
ÉTAPE 3 de l'algorithme d'optimisation.
"""

from typing import List, Dict, Optional
from .core_identifier import CoreTollIdentifier
from .verification.shapely_verifier import ShapelyVerifier


class TollIdentifier:
    """
    Identifieur de péages optimisé et modulaire.
    Responsabilité : ÉTAPE 3 de l'algorithme d'optimisation.
    """
    
    def __init__(self):
        """Initialise l'identifieur avec les nouveaux composants."""
        self.core_identifier = CoreTollIdentifier()
        self.verifier = ShapelyVerifier()
        print("🔍 Toll Identifier V2 initialisé")
    
    def identify_tolls_on_route(
        self, 
        route_coordinates: List[List[float]], 
        tollway_segments: List[Dict] = None
    ) -> Dict:
        """
        ÉTAPE 3: Identifie les péages sur la route et autour.
        
        Args:
            route_coordinates: Coordonnées de la route
            tollway_segments: Segments tollways de la route (optionnel)
            
        Returns:
            Dictionnaire complet avec péages détectés
        """
        # Identification de base avec le core identifier
        core_result = self.core_identifier.identify_tolls_on_route(
            route_coordinates, tollway_segments
        )
        
        # Si pas de péages trouvés, retourner le résultat de base
        if not core_result.get('identification_success'):
            return core_result
        
        # Vérification Shapely pour plus de précision (toujours appliquée si péages trouvés)
        print(f"   🔍 Debug Shapely: tollway_segments={tollway_segments is not None}, tolls_count={len(core_result['tolls_on_route'])}")
        if len(core_result['tolls_on_route']) > 0:
            verified_result = self._enhance_with_shapely_verification(
                core_result, route_coordinates, tollway_segments
            )
            return verified_result
        else:
            print(f"   ⚠️ Vérification Shapely ignorée: aucun péage trouvé")

        return core_result
    
    def _enhance_with_shapely_verification(
        self, 
        core_result: Dict, 
        route_coordinates: List[List[float]], 
        tollway_segments: List[Dict]
    ) -> Dict:
        """Améliore le résultat avec une vérification Shapely."""
        print("   🔍 Vérification Shapely pour précision...")
        
        try:
            # Utiliser la méthode disponible dans ShapelyVerifier
            shapely_result = self.verifier.verify_tolls_with_shapely(
                core_result['tolls_on_route'],
                core_result.get('nearby_tolls', []),
                route_coordinates
            )
            
            # Mettre à jour le résultat avec les données Shapely
            if 'shapely_on_route' in shapely_result:
                core_result['tolls_on_route'] = shapely_result['shapely_on_route']
                core_result['total_tolls_on_route'] = len(core_result['tolls_on_route'])
                core_result['verification_applied'] = True
                
                print(f"   ✅ Vérification Shapely : {len(core_result['tolls_on_route'])} péages confirmés")
            else:
                core_result['verification_applied'] = False
            
        except Exception as e:
            print(f"   ⚠️ Erreur vérification Shapely : {e}")
            core_result['verification_applied'] = False
        
        return core_result
    
    def get_spatial_index_stats(self) -> Dict:
        """Retourne les statistiques des index spatiaux."""
        return self.core_identifier.get_spatial_index_stats()
