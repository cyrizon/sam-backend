"""
Operator Pricing Model
---------------------

Represents pricing information for toll operators.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class OperatorPricing:
    """Grille de prix d'un opérateur par classe de véhicule."""
    operator: str
    c1: float  # Classe 1 (voitures)
    c2: float  # Classe 2 (motos, camping-cars)
    c3: float  # Classe 3 (camions 2 essieux)
    c4: float  # Classe 4 (camions 3+ essieux)
    c5: float  # Classe 5 (véhicules spéciaux)
    
    def get_price_per_km(self, vehicle_class: str) -> Optional[float]:
        """Retourne le prix au kilomètre pour une classe de véhicule donnée."""
        class_attr = f"c{vehicle_class}" if vehicle_class.isdigit() else vehicle_class.lower()
        return getattr(self, class_attr, None)
    
    def calculate_cost(self, distance_km: float, vehicle_class: str) -> Optional[float]:
        """Calcule le coût pour une distance et classe de véhicule données."""
        price_per_km = self.get_price_per_km(vehicle_class)
        if price_per_km is None:
            return None
        return distance_km * price_per_km


class OperatorPricingManager:
    """Gestionnaire des grilles de prix des opérateurs."""
    
    def __init__(self):
        self.pricing_data: Dict[str, OperatorPricing] = {}
    
    def load_from_csv(self, csv_path: str):
        """Charge les données de prix depuis un fichier CSV."""
        import csv
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                operator = row['operator']
                pricing = OperatorPricing(
                    operator=operator,
                    c1=float(row['c1']),
                    c2=float(row['c2']),
                    c3=float(row['c3']),
                    c4=float(row['c4']),
                    c5=float(row['c5'])
                )
                self.pricing_data[operator] = pricing
    
    def get_operator_pricing(self, operator: str) -> Optional[OperatorPricing]:
        """Retourne les données de prix d'un opérateur."""
        return self.pricing_data.get(operator)
    
    def get_available_operators(self) -> list:
        """Retourne la liste des opérateurs disponibles."""
        return list(self.pricing_data.keys())
