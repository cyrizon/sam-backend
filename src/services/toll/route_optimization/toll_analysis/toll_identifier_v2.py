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
        
        # Vérification Shapely pour plus de précision (optionnel)
        if tollway_segments and len(core_result['tolls_on_route']) > 0:
            verified_result = self._enhance_with_shapely_verification(
                core_result, route_coordinates, tollway_segments
            )
            return verified_result
        
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
            # Vérifier les péages sur route avec Shapely
            verified_tolls = []
            for toll_data in core_result['tolls_on_route']:
                if self.verifier.verify_toll_on_route(
                    toll_data['coordinates'], 
                    route_coordinates,
                    tolerance_m=100
                ):
                    verified_tolls.append(toll_data)
            
            # Mettre à jour le résultat
            core_result['tolls_on_route'] = verified_tolls
            core_result['total_tolls_on_route'] = len(verified_tolls)
            core_result['verification_applied'] = True
            
            print(f"   ✅ Vérification Shapely : {len(verified_tolls)} péages confirmés")
            
        except Exception as e:
            print(f"   ⚠️ Erreur vérification Shapely : {e}")
            core_result['verification_applied'] = False
        
        return core_result
    
    def get_spatial_index_stats(self) -> Dict:
        """Retourne les statistiques des index spatiaux."""
        return self.core_identifier.get_spatial_index_stats()
