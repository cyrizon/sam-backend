"""
Toll Cost Calculator
-------------------

Calculates toll costs between two toll booths based on operator pricing, 
toll types, and distance.
"""

import math
from typing import Optional, Tuple
from ..models.toll_booth_station import TollBoothStation
from ..models.operator_pricing import OperatorPricingManager
from ..managers.open_tolls_manager import OpenTollsManager


class TollCostCalculator:
    """Calculateur de coûts de péage entre deux stations."""
    
    # Groupe d'opérateurs considérés comme équivalents
    EQUIVALENT_OPERATORS = {"ASF", "COFIROUTE", "ESCOTA"}
    
    def __init__(self, operator_pricing_manager: OperatorPricingManager, open_tolls_manager: Optional[OpenTollsManager] = None):
        """
        Initialise le calculateur avec un gestionnaire de prix d'opérateurs.
        
        Args:
            operator_pricing_manager: Gestionnaire des prix des opérateurs
            open_tolls_manager: Gestionnaire des péages ouverts (optionnel)
        """
        self.pricing_manager = operator_pricing_manager
        self.open_tolls_manager = open_tolls_manager
    
    def calculate_cost(
        self, 
        toll_from: TollBoothStation,
        toll_to: TollBoothStation,
        vehicle_class: str = "1",
        distance_km: Optional[float] = None
    ) -> Tuple[Optional[float], str]:
        """
        Calcule le coût entre deux péages.
        
        Args:
            toll_from: Station de péage de départ
            toll_to: Station de péage d'arrivée
            vehicle_class: Classe de véhicule (1-5)
            distance_km: Distance en km (calculée si non fournie)
            
        Returns:
            Tuple[Optional[float], str]: (coût, message d'explication)
        """
        # Règles de calcul selon les types de péages
        if toll_from.is_open_toll and toll_to.is_open_toll:
            # Deux péages ouverts : somme des coûts fixes
            return self._calculate_open_tolls_cost(toll_from, toll_to, vehicle_class)
        
        if toll_from.is_closed_toll and toll_to.is_closed_toll:
            # Péage fermé vers péage fermé : vérifier même opérateur puis coût de la distance
            return self._calculate_closed_to_closed_cost(toll_from, toll_to, vehicle_class, distance_km)
        
        if toll_from.is_open_toll and toll_to.is_closed_toll:
            # Péage ouvert vers péage fermé : coût fixe du péage ouvert
            return self._calculate_open_toll_cost(toll_from, vehicle_class)
        
        if toll_from.is_closed_toll and toll_to.is_open_toll:
            # Péage fermé vers péage ouvert : coût fixe du péage ouvert
            return self._calculate_open_toll_cost(toll_to, vehicle_class)
        
        return None, "Configuration de péages non supportée"
    
    def _calculate_distance_cost(
        self,
        toll_from: TollBoothStation,
        toll_to: TollBoothStation,
        vehicle_class: str,
        distance_km: Optional[float] = None
    ) -> Tuple[Optional[float], str]:
        """Calcule le coût basé sur la distance."""
        # Déterminer l'opérateur à utiliser
        operator = self._determine_operator(toll_from, toll_to)
        if not operator:
            return None, "Aucun opérateur déterminé"
        
        # Obtenir les prix de l'opérateur
        pricing = self.pricing_manager.get_operator_pricing(operator)
        if not pricing:
            return None, f"Grille de prix non trouvée pour l'opérateur {operator}"
        
        # Calculer la distance si non fournie
        if distance_km is None:
            distance_km = self._calculate_distance(toll_from, toll_to)
        
        # Calculer le coût
        cost = pricing.calculate_cost(distance_km, vehicle_class)
        if cost is None:
            return None, f"Classe de véhicule {vehicle_class} non supportée"
        
        return cost, f"Coût calculé avec {operator} sur {distance_km:.2f} km"
    
    def _determine_operator(self, toll_from: TollBoothStation, toll_to: TollBoothStation) -> Optional[str]:
        """
        Détermine l'opérateur à utiliser pour le calcul.
        
        Priorité:
        1. Opérateur du péage de destination
        2. Opérateur du péage de départ
        3. Aucun opérateur
        """
        if toll_to.operator:
            return toll_to.operator
        if toll_from.operator:
            return toll_from.operator
        return None
    
    def _calculate_distance(self, toll_from: TollBoothStation, toll_to: TollBoothStation) -> float:
        """
        Calcule la distance entre deux péages en utilisant la formule de Haversine.
        
        Returns:
            float: Distance en kilomètres
        """
        try:
            # S'assurer que les coordonnées sont des float
            coords_from = toll_from.coordinates
            coords_to = toll_to.coordinates
            
            # Conversion sécurisée en float si nécessaire
            if isinstance(coords_from[0], str):
                lon1, lat1 = float(coords_from[0]), float(coords_from[1])
            else:
                lon1, lat1 = coords_from[0], coords_from[1]
                
            if isinstance(coords_to[0], str):
                lon2, lat2 = float(coords_to[0]), float(coords_to[1])
            else:
                lon2, lat2 = coords_to[0], coords_to[1]
        
        except (ValueError, IndexError, TypeError) as e:
            print(f"❌ Erreur conversion coordonnées: {e}")
            print(f"   From: {toll_from.coordinates}")
            print(f"   To: {toll_to.coordinates}")
            return 0.0
        
        # Formule de Haversine
        R = 6371  # Rayon terrestre en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_cost_breakdown(
        self,
        toll_from: TollBoothStation,
        toll_to: TollBoothStation,
        vehicle_class: str = "1",
        distance_km: Optional[float] = None
    ) -> dict:
        """
        Retourne un détail complet du calcul de coût.
        
        Returns:
            dict: Détail du calcul avec métadonnées
        """
        cost, explanation = self.calculate_cost(toll_from, toll_to, vehicle_class, distance_km)
        
        if distance_km is None:
            distance_km = self._calculate_distance(toll_from, toll_to)
        
        operator = self._determine_operator(toll_from, toll_to)
        pricing = self.pricing_manager.get_operator_pricing(operator) if operator else None
        price_per_km = pricing.get_price_per_km(vehicle_class) if pricing else None
        
        return {
            "cost": cost,
            "explanation": explanation,
            "from_toll": {
                "id": toll_from.osm_id,
                "name": toll_from.display_name,
                "type": toll_from.toll_type,
                "operator": toll_from.operator
            },
            "to_toll": {
                "id": toll_to.osm_id,
                "name": toll_to.display_name,
                "type": toll_to.toll_type,
                "operator": toll_to.operator
            },
            "calculation_details": {
                "distance_km": distance_km,
                "vehicle_class": vehicle_class,
                "operator_used": operator,
                "price_per_km": price_per_km
            }
        }
    
    def _calculate_open_tolls_cost(
        self,
        toll_from: TollBoothStation,
        toll_to: TollBoothStation,
        vehicle_class: str
    ) -> Tuple[Optional[float], str]:
        """Calcule le coût pour deux péages ouverts (somme des coûts fixes)."""
        cost_from, msg_from = self._calculate_open_toll_cost(toll_from, vehicle_class)
        cost_to, msg_to = self._calculate_open_toll_cost(toll_to, vehicle_class)
        
        if cost_from is None or cost_to is None:
            failed_toll = toll_from.display_name if cost_from is None else toll_to.display_name
            return None, f"Coût du péage ouvert {failed_toll} non disponible"
        
        total_cost = cost_from + cost_to
        return total_cost, f"Coût cumulé des péages ouverts: {toll_from.display_name} + {toll_to.display_name}"
    
    def _calculate_open_toll_cost(
        self,
        toll: TollBoothStation,
        vehicle_class: str
    ) -> Tuple[Optional[float], str]:
        """Calcule le coût fixe d'un péage ouvert depuis les données de pricing."""
        if not toll.name:
            return None, f"Nom du péage {toll.osm_id} non disponible"
        
        # Utiliser l'OpenTollsManager pour récupérer le coût
        if self.open_tolls_manager:
            cost = self.open_tolls_manager.get_open_toll_cost(toll.name, vehicle_class)
            if cost is not None:
                return cost, f"Coût fixe du péage ouvert {toll.display_name} (classe {vehicle_class})"
        
        # Fallback si pas de gestionnaire ou coût non trouvé
        return None, f"Coût du péage ouvert {toll.display_name} non disponible"
    
    def _calculate_closed_to_closed_cost(
        self,
        toll_from: TollBoothStation,
        toll_to: TollBoothStation,
        vehicle_class: str,
        distance_km: Optional[float] = None
    ) -> Tuple[Optional[float], str]:
        """Calcule le coût entre deux péages fermés (opérateurs compatibles requis)."""
        # Vérifier que les deux péages ont des opérateurs
        if not toll_from.operator or not toll_to.operator:
            return 0.0, "Opérateur manquant sur l'un des péages"
        
        # Vérifier la compatibilité des opérateurs
        if not self._are_operators_compatible(toll_from.operator, toll_to.operator):
            return 0.0, f"Opérateurs incompatibles: {toll_from.operator} vs {toll_to.operator}"
        
        # Opérateurs compatibles : calculer le coût basé sur la distance
        return self._calculate_distance_cost(toll_from, toll_to, vehicle_class, distance_km)
    
    def _are_operators_compatible(self, operator1: Optional[str], operator2: Optional[str]) -> bool:
        """
        Vérifie si deux opérateurs sont compatibles pour le calcul de coût.
        
        Args:
            operator1: Premier opérateur
            operator2: Deuxième opérateur
            
        Returns:
            bool: True si les opérateurs sont compatibles
        """
        # Si l'un des opérateurs est None, pas compatible
        if not operator1 or not operator2:
            return False
        
        # Même opérateur exact
        if operator1 == operator2:
            return True
        
        # Vérifier si les deux sont dans le groupe d'équivalents
        if operator1 in self.EQUIVALENT_OPERATORS and operator2 in self.EQUIVALENT_OPERATORS:
            return True
        
        return False
