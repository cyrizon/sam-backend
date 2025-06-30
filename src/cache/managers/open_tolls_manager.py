"""
Open Tolls Manager
-----------------

Manages the list of open tolls and their identification.
"""

from typing import Set, Optional, Dict
import csv
import os
from dataclasses import dataclass


@dataclass
class OpenTollPricing:
    """Coûts d'un péage ouvert par classe de véhicule."""
    name: str
    c1: float
    c2: float
    c3: float
    c4: float
    c5: float
    
    def get_cost(self, vehicle_class: str) -> Optional[float]:
        """Retourne le coût pour une classe de véhicule donnée."""
        class_attr = f"c{vehicle_class}" if vehicle_class.isdigit() else vehicle_class.lower()
        return getattr(self, class_attr, None)


class OpenTollsManager:
    """Gestionnaire des péages ouverts."""
    
    def __init__(self):
        self.open_toll_names: Set[str] = set()
        self.open_toll_pricing: Dict[str, OpenTollPricing] = {}
    
    def load_from_csv(self, csv_path: str):
        """Charge la liste des péages ouverts depuis un fichier CSV."""
        if not os.path.exists(csv_path):
            print(f"Warning: Open tolls file not found: {csv_path}")
            return
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Le fichier contient name,c1,c2,c3,c4,c5
                toll_name = row.get('name')
                if toll_name:
                    toll_name = toll_name.strip()
                    self.open_toll_names.add(toll_name)
                    
                    # Stocker aussi les coûts
                    pricing = OpenTollPricing(
                        name=toll_name,
                        c1=float(row['c1']),
                        c2=float(row['c2']),
                        c3=float(row['c3']),
                        c4=float(row['c4']),
                        c5=float(row['c5'])
                    )
                    self.open_toll_pricing[toll_name] = pricing
    
    def is_toll_open(self, toll_name: str) -> bool:
        """Vérifie si un péage est ouvert en utilisant son nom."""
        return toll_name in self.open_toll_names
    
    def get_toll_type(self, toll_name: str) -> str:
        """Retourne le type de péage ('O' pour ouvert, 'F' pour fermé)."""
        return "O" if self.is_toll_open(toll_name) else "F"
    
    def get_open_tolls_count(self) -> int:
        """Retourne le nombre de péages ouverts."""
        return len(self.open_toll_names)
    
    def get_open_toll_cost(self, toll_name: str, vehicle_class: str) -> Optional[float]:
        """Retourne le coût d'un péage ouvert pour une classe de véhicule."""
        pricing = self.open_toll_pricing.get(toll_name)
        if pricing:
            return pricing.get_cost(vehicle_class)
        return None
