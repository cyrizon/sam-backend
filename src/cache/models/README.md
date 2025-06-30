# 🏗️ Cache Models - Modèles de Données

## 📋 Vue d'ensemble

Les modèles de données définissent les structures fondamentales utilisées dans le système de cache SAM. Ils représentent les péages, liaisons autoroutières, tarifs et types de liens avec leurs propriétés et méthodes associées.

## 🏗️ Architecture

```
models/
├── toll_booth_station.py       # Station de péage OSM
├── motorway_link.py            # Liaison autoroutière de base
├── complete_motorway_link.py   # Liaison autoroutière complète
├── operator_pricing.py         # Modèle de tarification
├── link_types.py               # Types et énumérations
└── __init__.py
```

## 🧩 Modèles détaillés

### **1. TollBoothStation** - Station de Péage

Représente une station de péage avec toutes ses propriétés OSM et métadonnées.

#### **Structure**
```python
@dataclass
class TollBoothStation:
    osm_id: str                     # Identifiant OSM unique
    name: Optional[str]             # Nom du péage
    operator: Optional[str]         # Opérateur (ASF, APRR, etc.)
    operator_ref: Optional[str]     # Référence opérateur
    highway_ref: Optional[str]      # Référence autoroute (ex: "A 6")
    coordinates: List[float]        # [longitude, latitude]
    properties: Dict                # Propriétés OSM complètes
    toll_type: str = "F"           # "O" (ouvert) ou "F" (fermé)
```

#### **Propriétés calculées**
```python
# Types de péages
@property
def is_open_toll(self) -> bool:
    """Retourne True si c'est un péage ouvert (tarif fixe)."""
    return self.toll_type == "O"

@property  
def is_closed_toll(self) -> bool:
    """Retourne True si c'est un péage fermé (tarif au km)."""
    return self.toll_type == "F"

@property
def display_name(self) -> str:
    """Retourne le nom d'affichage optimal."""
    if self.name:
        return self.name
    elif self.operator_ref:
        return f"Péage {self.operator_ref}"
    else:
        return f"Péage {self.osm_id}"
```

#### **Utilisation**
```python
# Création d'une station de péage
toll = TollBoothStation(
    osm_id="node/123456789",
    name="Fontaine Larivière",
    operator="ASF",
    operator_ref="FL001",
    highway_ref="A 6",
    coordinates=[4.8567, 46.7892],
    properties={"highway": "toll_booth", "barrier": "toll_booth"},
    toll_type="O"  # Péage ouvert
)

# Utilisation des propriétés
print(f"Péage: {toll.display_name}")
print(f"Type: {'Ouvert' if toll.is_open_toll else 'Fermé'}")
print(f"Position: {toll.get_coordinates()}")
print(f"Opérateur: {toll.operator}")
```

#### **Exemples de données réelles**
```python
# Péage ouvert (tarif fixe)
fontaine_lariviere = TollBoothStation(
    osm_id="way/234567890",
    name="Fontaine Larivière", 
    operator="ASF",
    highway_ref="A 6",
    coordinates=[4.8567, 46.7892],
    toll_type="O"  # Tarif: 3.10€ (C1)
)

# Péage fermé (tarif au km)
peage_ferme = TollBoothStation(
    osm_id="way/345678901",
    name="Sortie Mâcon Sud",
    operator="APRR", 
    highway_ref="A 6",
    coordinates=[4.8234, 46.2891],
    toll_type="F"  # Tarif: 0.091€/km (C1)
)
```

---

### **2. MotorwayLink** - Liaison Autoroutière de Base

Représente un point de liaison autoroutière (entrée ou sortie).

#### **Structure**
```python
@dataclass
class MotorwayLink:
    osm_id: str                     # Identifiant OSM
    link_type: LinkType             # ENTRY, EXIT, INDETERMINATE
    highway_ref: str                # Référence autoroute
    coordinates: List[float]        # [longitude, latitude]
    properties: Dict                # Propriétés OSM
    junction_name: Optional[str]    # Nom de l'échangeur
    junction_ref: Optional[str]     # Référence de l'échangeur
```

#### **Types de liens**
```python
from enum import Enum

class LinkType(Enum):
    ENTRY = "entry"                 # Entrée d'autoroute
    EXIT = "exit"                   # Sortie d'autoroute  
    INDETERMINATE = "indeterminate" # Type indéterminé
```

#### **Utilisation**
```python
# Création d'une entrée d'autoroute
entry = MotorwayLink(
    osm_id="way/987654321",
    link_type=LinkType.ENTRY,
    highway_ref="A 6",
    coordinates=[4.8345, 46.7123],
    properties={"highway": "motorway_link", "oneway": "yes"},
    junction_name="Échangeur de Mâcon Nord",
    junction_ref="13"
)

# Vérification du type
if entry.link_type == LinkType.ENTRY:
    print(f"Point d'entrée: {entry.junction_name}")
```

---

### **3. CompleteMotorwayLink** - Liaison Autoroutière Complète

Représente un segment autoroutier complet avec entrée, sortie et péages associés.

#### **Structure**
```python
@dataclass
class CompleteMotorwayLink:
    link_id: str                    # Identifiant unique du lien
    entry_point: MotorwayLink       # Point d'entrée
    exit_point: MotorwayLink        # Point de sortie
    highway_ref: str                # Référence autoroute
    distance_km: float              # Distance du segment
    geometry: List[List[float]]     # Coordonnées du tracé
    associated_tolls: List[str]     # IDs des péages sur le segment
    operator: Optional[str]         # Opérateur principal
    metadata: Dict                  # Métadonnées du segment
```

#### **Propriétés calculées**
```python
@property
def segment_name(self) -> str:
    """Nom descriptif du segment."""
    entry_name = self.entry_point.junction_name or "Entrée"
    exit_name = self.exit_point.junction_name or "Sortie"
    return f"{self.highway_ref}: {entry_name} → {exit_name}"

@property
def has_tolls(self) -> bool:
    """Indique si le segment a des péages."""
    return len(self.associated_tolls) > 0

@property
def toll_count(self) -> int:
    """Nombre de péages sur le segment."""
    return len(self.associated_tolls)
```

#### **Utilisation**
```python
# Création d'un segment complet
complete_link = CompleteMotorwayLink(
    link_id="A6_MACON_NORD_SUD",
    entry_point=entry_macon_nord,
    exit_point=exit_macon_sud,
    highway_ref="A 6",
    distance_km=12.5,
    geometry=[[4.8345, 46.7123], [4.8234, 46.2891]],
    associated_tolls=["toll_123", "toll_456"],
    operator="APRR",
    metadata={"construction_year": 1970, "lanes": 2}
)

# Utilisation
print(f"Segment: {complete_link.segment_name}")
print(f"Distance: {complete_link.distance_km} km")
print(f"Péages: {complete_link.toll_count}")
print(f"Opérateur: {complete_link.operator}")
```

---

### **4. OperatorPricing** - Modèle de Tarification

Représente les tarifs d'un opérateur autoroutier pour toutes les catégories de véhicules.

#### **Structure**
```python
@dataclass
class OperatorPricing:
    operator_name: str              # Nom de l'opérateur (ASF, APRR, etc.)
    pricing_per_km: Dict[str, float]  # Prix au km par catégorie
    open_tolls: Dict[str, Dict[str, float]]  # Péages ouverts
    last_updated: str               # Date de dernière mise à jour
    currency: str = "EUR"           # Devise
    
    # Catégories standard: c1, c2, c3, c4, c5
    # c1: Véhicule léger, c2: Véhicule + remorque, 
    # c3: Autocar/Camion 2 essieux, c4: Camion 3+ essieux, c5: Moto
```

#### **Méthodes de calcul**
```python
def get_price_per_km(self, vehicle_category: str) -> float:
    """Retourne le prix au kilomètre pour une catégorie."""
    return self.pricing_per_km.get(vehicle_category, 0.0)

def get_open_toll_price(self, toll_name: str, vehicle_category: str) -> float:
    """Retourne le prix d'un péage ouvert."""
    if toll_name in self.open_tolls:
        return self.open_tolls[toll_name].get(vehicle_category, 0.0)
    return 0.0

def calculate_segment_cost(self, distance_km: float, vehicle_category: str) -> float:
    """Calcule le coût d'un segment autoroutier."""
    price_per_km = self.get_price_per_km(vehicle_category)
    return distance_km * price_per_km
```

#### **Utilisation**
```python
# Création des tarifs ASF
asf_pricing = OperatorPricing(
    operator_name="ASF",
    pricing_per_km={
        "c1": 0.12,   # 12 centimes/km pour véhicule léger
        "c2": 0.18,   # 18 centimes/km pour véhicule + remorque
        "c3": 0.29,   # 29 centimes/km pour autocar/camion 2 essieux
        "c4": 0.40,   # 40 centimes/km pour camion 3+ essieux
        "c5": 0.072   # 7.2 centimes/km pour moto
    },
    open_tolls={
        "Fontaine Larivière": {
            "c1": 3.10, "c2": 4.80, "c3": 7.80, "c4": 10.90, "c5": 1.90
        }
    },
    last_updated="2025-06-30"
)

# Calculs
cost_per_km_c1 = asf_pricing.get_price_per_km("c1")  # 0.12€
segment_cost = asf_pricing.calculate_segment_cost(45.0, "c1")  # 5.40€
toll_cost = asf_pricing.get_open_toll_price("Fontaine Larivière", "c1")  # 3.10€
```

---

### **5. LinkTypes** - Types et Énumérations

Définit les types et constantes utilisés dans le système.

#### **Types de liens**
```python
from enum import Enum

class LinkType(Enum):
    """Types de liaisons autoroutières."""
    ENTRY = "entry"                 # Point d'entrée
    EXIT = "exit"                   # Point de sortie
    INDETERMINATE = "indeterminate" # Type indéterminé

class TollType(Enum):
    """Types de péages."""
    OPEN = "O"                      # Péage ouvert (tarif fixe)
    CLOSED = "F"                    # Péage fermé (tarif au km)

class VehicleCategory(Enum):
    """Catégories de véhicules pour tarification."""
    C1 = "c1"  # Véhicule léger
    C2 = "c2"  # Véhicule + remorque légère  
    C3 = "c3"  # Autocar, camion 2 essieux
    C4 = "c4"  # Camion 3+ essieux
    C5 = "c5"  # Motocyclette
```

#### **Constantes**
```python
# Distances maximales pour associations
MAX_LINKING_DISTANCE_M = 2.0        # Distance max pour lier entrée/sortie
MAX_TOLL_ASSOCIATION_DISTANCE_M = 1.5  # Distance max pour associer péages

# Opérateurs français standards
FRENCH_OPERATORS = [
    "ASF", "APRR", "SANEF", "AREA", "COFIROUTE", 
    "ESCOTA", "SAPN", "SFTRF", "ATMB", "ALICORNE",
    "ARCOUR", "ALIENOR", "ALIS", "ATLANDES", "CEVM"
]

# Catégories de véhicules avec descriptions
VEHICLE_CATEGORIES = {
    "c1": "Véhicule léger (< 3.5t, hauteur < 2m)",
    "c2": "Véhicule léger + remorque ou caravane", 
    "c3": "Autocar, camion 2 essieux (3.5-12t)",
    "c4": "Camion 3+ essieux (> 12t)",
    "c5": "Motocyclette, cyclomoteur"
}
```

## 🔧 Utilisation pratique

### **Création et manipulation des modèles**
```python
# Import des modèles
from src.cache.models.toll_booth_station import TollBoothStation
from src.cache.models.complete_motorway_link import CompleteMotorwayLink
from src.cache.models.operator_pricing import OperatorPricing
from src.cache.models.link_types import LinkType, TollType, VehicleCategory

# Création d'un péage complet
toll = TollBoothStation(
    osm_id="node/123456789",
    name="Péage de Villefranche",
    operator="ASF",
    coordinates=[4.7234, 45.9876],
    toll_type=TollType.OPEN.value,
    properties={"highway": "toll_booth"}
)

# Vérifications
print(f"Péage ouvert: {toll.is_open_toll}")
print(f"Nom d'affichage: {toll.display_name}")
```

### **Calculs de coûts avec les modèles**
```python
# Création du modèle de tarification
pricing = OperatorPricing(
    operator_name="APRR",
    pricing_per_km={"c1": 0.091, "c2": 0.14},
    open_tolls={"Mâcon Péage": {"c1": 2.50, "c2": 3.80}},
    last_updated="2025-06-30"
)

# Calculs
distance = 85.5  # km
category = VehicleCategory.C1.value

# Coût du segment autoroutier
segment_cost = pricing.calculate_segment_cost(distance, category)
print(f"Coût segment: {segment_cost:.2f}€")

# Coût du péage ouvert
toll_cost = pricing.get_open_toll_price("Mâcon Péage", category)
print(f"Coût péage: {toll_cost:.2f}€")

# Coût total
total_cost = segment_cost + toll_cost
print(f"Coût total: {total_cost:.2f}€")
```

### **Travail avec les liaisons complètes**
```python
# Création d'un segment autoroutier complet
segment = CompleteMotorwayLink(
    link_id="A6_MACON_VILLEFRANCHE",
    entry_point=macon_entry,
    exit_point=villefranche_exit,
    highway_ref="A 6",
    distance_km=35.2,
    geometry=route_coordinates,
    associated_tolls=["toll_macon", "toll_villefranche"],
    operator="APRR"
)

# Analyse du segment
print(f"Segment: {segment.segment_name}")
print(f"A des péages: {segment.has_tolls}")
print(f"Nombre de péages: {segment.toll_count}")

# Coût du segment (avec l'opérateur pricing)
if segment.operator in pricing_managers:
    operator_pricing = pricing_managers[segment.operator]
    cost = operator_pricing.calculate_segment_cost(
        segment.distance_km, 
        VehicleCategory.C1.value
    )
    print(f"Coût estimé: {cost:.2f}€")
```

## 📊 Validation et contrôles

### **Validation des modèles**
```python
def validate_toll_booth(toll: TollBoothStation) -> List[str]:
    """Valide une station de péage."""
    errors = []
    
    if not toll.osm_id:
        errors.append("OSM ID manquant")
    
    if not toll.coordinates or len(toll.coordinates) != 2:
        errors.append("Coordonnées invalides")
    
    if toll.toll_type not in ["O", "F"]:
        errors.append("Type de péage invalide")
    
    if toll.operator and toll.operator not in FRENCH_OPERATORS:
        errors.append(f"Opérateur inconnu: {toll.operator}")
    
    return errors

def validate_complete_link(link: CompleteMotorwayLink) -> List[str]:
    """Valide une liaison autoroutière complète."""
    errors = []
    
    if link.distance_km <= 0:
        errors.append("Distance invalide")
    
    if not link.highway_ref:
        errors.append("Référence autoroute manquante")
    
    if not link.geometry or len(link.geometry) < 2:
        errors.append("Géométrie insuffisante")
    
    return errors
```
