"""
Budget Calculator
================

Calculateur de coûts spécialisé pour les segments et distances entre péages.
Le calcul des coûts totaux se fait via le cache V2.
"""

from typing import List, Dict, Any
from ...utils.cache_accessor import CacheAccessor


class BudgetCalculator:
    """
    Calculateur de coûts pour la sélection par budget.
    Spécialisé dans le calcul des distances et segments entre péages.
    """
    def calculate_segment_costs(
        self, 
        tolls: List[Dict], 
        segments_info: List[Dict] = None
    ) -> List[float]:
        """
        Calcule les coûts par segment entre péages consécutifs.
        
        Args:
            tolls: Liste ordonnée des péages
            segments_info: Informations des segments (optionnel)
            
        Returns:
            Liste des coûts par segment
        """
        if not tolls:
            return []
        
        segment_costs = []
        
        for i, toll in enumerate(tolls):
            if i == 0:
                # Premier péage : coût d'entrée (généralement 0 ou coût fixe)
                segment_costs.append(0.0)
            else:
                # Péages suivants : coût de distance depuis le précédent
                prev_toll = tolls[i-1]
                cost = self.calculate_distance_cost(prev_toll, toll)
                segment_costs.append(cost)
        
        return segment_costs
    
    def calculate_distance_cost(self, toll1: Dict, toll2: Dict) -> float:
        """
        Calcule le coût de distance entre deux péages en utilisant le cache V2.
        
        Args:
            toll1: Premier péage
            toll2: Deuxième péage
            
        Returns:
            Coût de distance calculé par le cache
        """
        try:
            # Récupérer les données des péages associés
            toll1_data = toll1.get('associated_toll')
            toll2_data = toll2.get('associated_toll')
            
            if not toll1_data or not toll2_data:
                print(f"     ⚠️ Données de péage manquantes pour le calcul")
                return 3.0  # Fallback
            
            # Calculer la distance entre les deux points si nécessaire
            coords1 = toll1.get('coordinates', [])
            coords2 = toll2.get('coordinates', [])
            distance_km = None
            
            if coords1 and coords2:
                distance_km = self._calculate_distance_between_points(coords1, coords2)
            
            # Utiliser le CacheAccessor pour calculer le coût
            cost = CacheAccessor.calculate_toll_cost(
                toll_from=toll1_data, 
                toll_to=toll2_data, 
                vehicle_category="1", 
                distance_km=distance_km
            )
            
            if cost is not None:
                print(f"     💰 Coût distance: {cost:.2f}€")
                return cost
            else:
                print(f"     ⚠️ Calcul cache échoué")
                # Fallback avec estimation basée sur la distance
                if distance_km:
                    return distance_km * 0.15  # ~15 centimes/km
                else:
                    return 3.0
                
        except Exception as e:
            print(f"     ⚠️ Erreur calcul coût distance: {e}")
            return 3.0  # Fallback sûr
    
    def _calculate_distance_between_points(self, coords1: List[float], coords2: List[float]) -> float:
        """
        Calcule la distance entre deux points en kilomètres.
        
        Args:
            coords1: [longitude, latitude] du point 1
            coords2: [longitude, latitude] du point 2
            
        Returns:
            Distance en kilomètres
        """
        import math
        
        # Conversion en radians
        lat1, lon1 = math.radians(coords1[1]), math.radians(coords1[0])
        lat2, lon2 = math.radians(coords2[1]), math.radians(coords2[0])
        
        # Formule de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Rayon de la Terre en km
        earth_radius = 6371.0
        
        distance = earth_radius * c
        return distance
