"""
V2 Cache Manager with Toll Pricing
----------------------------------

Main manager that coordinates toll booth loading, pricing data, and cost calculations.
"""

import os
from typing import List, Optional, Dict, Any
from ..models.toll_booth_station import TollBoothStation
from ..models.operator_pricing import OperatorPricingManager
from ..managers.open_tolls_manager import OpenTollsManager
from ..parsers.toll_booth_parser import TollBoothParser
from ..services.toll_cost_calculator import TollCostCalculator


class CacheManagerWithPricing:
    """Gestionnaire principal du cache V2 avec logique de prix."""
    
    def __init__(self, data_dir: str):
        """
        Initialise le gestionnaire avec le répertoire des données.
        
        Args:
            data_dir: Répertoire racine des données
        """
        self.data_dir = data_dir
        self.osm_dir = os.path.join(data_dir, "osm")
        self.operators_dir = os.path.join(data_dir, "operators")
        
        # Composants
        self.toll_booths: List[TollBoothStation] = []
        self.open_tolls_manager = OpenTollsManager()
        self.pricing_manager = OperatorPricingManager()
        self.cost_calculator: Optional[TollCostCalculator] = None
        
        # État de chargement
        self.is_loaded = False
    
    def load_all(self) -> bool:
        """
        Charge toutes les données nécessaires.
        
        Returns:
            bool: True si le chargement a réussi
        """
        try:
            print("🔄 Chargement du cache V2 avec pricing...")
            
            # 1. Charger les péages ouverts
            self._load_open_tolls()
            
            # 2. Charger les données de prix des opérateurs
            self._load_operator_pricing()
            
            # 3. Charger les toll booths OSM
            self._load_toll_booths()
            
            # 4. Initialiser le calculateur de coûts
            self._initialize_cost_calculator()
            
            self.is_loaded = True
            print("✅ Cache V2 avec pricing chargé avec succès")
            self._print_statistics()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement du cache V2: {e}")
            return False
    
    def _load_open_tolls(self):
        """Charge la liste des péages ouverts."""
        open_tolls_path = os.path.join(self.operators_dir, "open_tolls.csv")
        self.open_tolls_manager.load_from_csv(open_tolls_path)
        print(f"📂 Péages ouverts chargés: {self.open_tolls_manager.get_open_tolls_count()}")
    
    def _load_operator_pricing(self):
        """Charge les grilles de prix des opérateurs."""
        pricing_path = os.path.join(self.operators_dir, "price_per_km.csv")
        if os.path.exists(pricing_path):
            self.pricing_manager.load_from_csv(pricing_path)
            operators = self.pricing_manager.get_available_operators()
            print(f"💰 Opérateurs de prix chargés: {len(operators)} ({', '.join(operators[:5])}...)")
        else:
            print(f"⚠️  Fichier de prix non trouvé: {pricing_path}")
    
    def _load_toll_booths(self):
        """Charge les toll booths OSM."""
        toll_booths_path = os.path.join(self.osm_dir, "toll_booths.geojson")
        if os.path.exists(toll_booths_path):
            parser = TollBoothParser(toll_booths_path, self.open_tolls_manager)
            self.toll_booths = parser.parse()
        else:
            print(f"⚠️  Fichier toll booths non trouvé: {toll_booths_path}")
    
    def _initialize_cost_calculator(self):
        """Initialise le calculateur de coûts."""
        self.cost_calculator = TollCostCalculator(self.pricing_manager, self.open_tolls_manager)
        print("🧮 Calculateur de coûts initialisé")
    
    def _print_statistics(self):
        """Affiche les statistiques de chargement."""
        open_count = sum(1 for tb in self.toll_booths if tb.is_open_toll)
        closed_count = sum(1 for tb in self.toll_booths if tb.is_closed_toll)
        
        print(f"📊 Statistiques:")
        print(f"   - Total toll booths: {len(self.toll_booths)}")
        print(f"   - Péages ouverts: {open_count}")
        print(f"   - Péages fermés: {closed_count}")
        print(f"   - Opérateurs disponibles: {len(self.pricing_manager.get_available_operators())}")
    
    def get_toll_booth_by_id(self, osm_id: str) -> Optional[TollBoothStation]:
        """Récupère un toll booth par son ID OSM."""
        for tb in self.toll_booths:
            if tb.osm_id == osm_id:
                return tb
        return None
    
    def get_toll_booths_by_operator(self, operator: str) -> List[TollBoothStation]:
        """Récupère tous les toll booths d'un opérateur."""
        return [tb for tb in self.toll_booths if tb.operator == operator]
    
    def calculate_toll_cost(
        self,
        from_id: str,
        to_id: str,
        vehicle_class: str = "1",
        distance_km: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calcule le coût de péage entre deux stations.
        
        Args:
            from_id: ID OSM du péage de départ
            to_id: ID OSM du péage d'arrivée
            vehicle_class: Classe de véhicule (1-5)
            distance_km: Distance en km (calculée si non fournie)
            
        Returns:
            Dict avec le détail du calcul ou None si impossible
        """
        if not self.is_loaded or not self.cost_calculator:
            print("❌ Cache non chargé ou calculateur non initialisé")
            return None
        
        toll_from = self.get_toll_booth_by_id(from_id)
        toll_to = self.get_toll_booth_by_id(to_id)
        
        if not toll_from or not toll_to:
            print(f"❌ Toll booth non trouvé: {from_id} ou {to_id}")
            return None
        
        return self.cost_calculator.get_cost_breakdown(
            toll_from, toll_to, vehicle_class, distance_km
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'état du cache."""
        return {
            "loaded": self.is_loaded,
            "toll_booths_count": len(self.toll_booths),
            "open_tolls_count": sum(1 for tb in self.toll_booths if tb.is_open_toll),
            "closed_tolls_count": sum(1 for tb in self.toll_booths if tb.is_closed_toll),
            "operators_count": len(self.pricing_manager.get_available_operators()),
            "available_operators": self.pricing_manager.get_available_operators()
        }
