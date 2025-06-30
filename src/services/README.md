# 🔧 Services - Services Métier SAM Backend

## 📋 Vue d'ensemble

Le module `services` constitue le cœur métier du backend SAM, orchestrant l'optimisation d'itinéraires sous contraintes de péages et de budget. Il s'interface avec OpenRouteService (ORS) et intègre les données de cache pour fournir des solutions d'itinéraires intelligentes.

## 🏗️ Architecture

```
src/services/
├── 📁 common/                    # Constantes et utilitaires partagés
├── 📁 optimization/              # Moteur d'optimisation d'itinéraires
├── 🔌 ors_service.py            # Interface OpenRouteService
├── 🛠️ ors_config_manager.py     # Gestionnaire de configuration ORS
├── 📦 ors_payload_builder.py    # Constructeur de requêtes ORS
├── 🧠 smart_route.py            # Service principal de routage intelligent
└── 📄 README.md                # Documentation du module
```

## 🎯 Objectifs du système

### **Optimisation intelligente**
- 🎯 **Contraintes de péages** : Limitation du nombre de péages sur l'itinéraire
- 💰 **Contraintes de budget** : Respect d'un budget maximum de péages
- ⚡ **Performances** : Algorithmes optimisés pour réponse rapide (< 3s)
- 🛣️ **Alternatives** : Génération de multiples solutions optimales

### **Intégration robuste**
- 🔌 **API OpenRouteService** : Communication fiable avec timeout adaptatif
- 🗄️ **Cache SAM** : Utilisation des données de péages et tarifs
- 📊 **Tracking** : Métriques de performance et monitoring
- 🛡️ **Gestion d'erreurs** : Récupération gracieuse et fallbacks

## 🧩 Composants principaux

### **1. SmartRouteService** - Orchestrateur Principal

Service de haut niveau qui coordonne l'optimisation d'itinéraires avec contraintes.

#### **Fonctionnalités**
- 🎯 **Optimisation par contrainte** : Péages ou budget maximum
- 🚀 **Algorithmes intelligents** : Stratégies adaptatives selon le contexte
- 📊 **Métriques** : Tracking des performances et statistiques
- 🔄 **Sessions** : Gestion complète du cycle de vie des optimisations

#### **Utilisation**
```python
from src.services.smart_route import SmartRouteService

# Initialisation
smart_route = SmartRouteService()

# Optimisation avec limite de péages
result = smart_route.compute_route_with_toll_limit(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]],  # Lyon → Paris
    max_tolls=3,
    veh_class="c1"
)

# Optimisation avec budget maximum
result = smart_route.compute_route_with_budget_limit(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]],
    max_price=25.00,  # 25€ maximum
    veh_class="c1"
)
```

#### **Structure des résultats**
```python
{
    "status": "SUCCESS",                    # Statut de l'optimisation
    "fastest": {                           # Route la plus rapide
        "duration": 2847.5,
        "distance": 462350.2,
        "cost": 32.45,
        "toll_count": 5,
        "geojson": {...}
    },
    "cheapest": {                          # Route la moins chère
        "duration": 3124.1,
        "distance": 478230.1,
        "cost": 18.50,
        "toll_count": 2,
        "geojson": {...}
    },
    "min_tolls": {                         # Route avec minimum de péages
        "duration": 3256.8,
        "distance": 485120.3,
        "cost": 12.30,
        "toll_count": 1,
        "geojson": {...}
    },
    "performance": {
        "total_duration_ms": 2847,
        "ors_calls": 3,
        "combinations_tested": 15
    }
}
```

---

### **2. ORSService** - Interface OpenRouteService

Interface robuste pour communiquer avec l'instance OpenRouteService auto-hébergée.

#### **Responsabilités**
- 🔌 **Appels API** : Communication HTTP avec gestion d'erreurs
- ⏱️ **Timeouts adaptatifs** : Délais calculés selon la complexité
- 📊 **Tracking** : Métriques de performance des appels
- 🛡️ **Validation** : Vérification des réponses et gestion d'échecs

#### **Utilisation**
```python
from src.services.ors_service import ORSService

# Initialisation (utilise ORS_BASE_URL de l'environnement)
ors = ORSService()

# Vérification de la configuration
if ors.test_all_set():
    print("✅ ORS configuré correctement")

# Route simple entre deux points
route = ors.get_route(
    start=[4.8345, 46.7123],    # Lyon
    end=[2.3522, 48.8566]       # Paris
)

# Route de base avec informations de péages
route = ors.get_base_route(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]],
    include_tollways=True
)

# Route évitant les autoroutes à péage
route_no_toll = ors.get_route_avoid_tollways(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]]
)

# Appel personnalisé avec payload complet
custom_payload = {
    "coordinates": [[4.8345, 46.7123], [2.3522, 48.8566]],
    "options": {"avoid_features": ["tollways"]},
    "extra_info": ["tollways", "surface"],
    "language": "fr"
}
result = ors.call_ors(custom_payload)
```

---

### **3. ORSConfigManager** - Gestionnaire de Configuration

Gestionnaire centralisé pour la validation et l'optimisation des requêtes ORS.

#### **Fonctionnalités**
- ✅ **Validation** : Contrôle des coordonnées et paramètres
- ⏱️ **Timeouts adaptatifs** : Calcul selon la complexité de la requête
- 🏷️ **Classification** : Identification du type d'opération
- 🔧 **Optimisation** : Amélioration automatique des payloads

#### **Utilisation**
```python
from src.services.ors_config_manager import ORSConfigManager

# Validation de coordonnées
coordinates = [[4.8345, 46.7123], [2.3522, 48.8566]]
ORSConfigManager.validate_coordinates(coordinates)  # Raises ValueError si invalides

# Calcul de timeout adaptatif
payload = {
    "coordinates": coordinates,
    "options": {"avoid_features": ["tollways"]},
    "extra_info": ["tollways"]
}
timeout = ORSConfigManager.calculate_timeout(payload)  # 15s pour cette complexité

# Identification de l'opération
operation = ORSConfigManager.get_operation_name(payload)  # "ORS_avoid_tollways"

# Optimisation du payload
optimized = ORSConfigManager.optimize_payload(payload)
```

#### **Configuration des timeouts**
```python
# Timeouts adaptatifs selon la complexité
BASE_TIMEOUT = 10       # Routes simples (2 points)
COMPLEX_TIMEOUT = 20    # Routes avec évitement ou waypoints
MAX_TIMEOUT = 30        # Limite absolue

# Facteurs d'ajustement
+ (nombre_points - 2) * 2s     # Points supplémentaires
+ 5s si avoid_features         # Évitement de caractéristiques  
+ nombre_extra_info * 2s       # Informations supplémentaires
```

---

### **4. ORSPayloadBuilder** - Constructeur de Requêtes

Constructeur centralisé pour assembler les payloads ORS de manière uniforme.

#### **Responsabilités**
- 📦 **Construction standardisée** : Payloads uniformes et validés
- 🎯 **Templates prédéfinis** : Configurations courantes pré-assemblées
- 🔧 **Personnalisation** : Options avancées pour cas spécifiques
- 📊 **Enrichissement** : Métadonnées pour tracking et debugging

#### **Utilisation**
```python
from src.services.ors_payload_builder import ORSPayloadBuilder

coordinates = [[4.8345, 46.7123], [2.3522, 48.8566]]

# Payload de base avec informations de péages
base_payload = ORSPayloadBuilder.build_base_payload(
    coordinates=coordinates,
    include_tollways=True
)

# Payload pour éviter les péages
avoid_payload = ORSPayloadBuilder.build_avoid_tollways_payload(
    coordinates=coordinates
)

# Payload personnalisé
custom_payload = ORSPayloadBuilder.build_custom_payload(
    coordinates=coordinates,
    options={
        "avoid_features": ["tollways", "ferries"],
        "vehicle_type": "car"
    },
    extra_info=["tollways", "surface", "steepness"]
)

# Enrichissement pour tracking
enhanced = ORSPayloadBuilder.enhance_payload_for_tracking(
    payload=base_payload,
    operation_context="route_optimization"
)
```

#### **Payloads générés**
```python
# Base payload
{
    "coordinates": [[4.8345, 46.7123], [2.3522, 48.8566]],
    "language": "fr",
    "extra_info": ["tollways"]
}

# Avoid tollways payload  
{
    "coordinates": [[4.8345, 46.7123], [2.3522, 48.8566]],
    "options": {"avoid_features": ["tollways"]},
    "extra_info": ["tollways"],
    "language": "fr"
}
```

## 🔧 Configuration

### **Variables d'environnement**
```bash
# Configuration ORS obligatoire
ORS_BASE_URL=http://localhost:8082/ors    # URL de l'instance ORS

# Configuration optionnelle
ORS_TIMEOUT=30                            # Timeout par défaut (secondes)
ORS_API_KEY=your-api-key                  # Clé API si requise
```

### **Configuration avancée**
```python
# Timeouts personnalisés
class CustomORSConfig(ORSConfigManager):
    BASE_TIMEOUT = 15
    MAX_TIMEOUT = 45
    
    @staticmethod
    def calculate_timeout(payload):
        # Logique personnalisée
        return min(payload_complexity * 5, CustomORSConfig.MAX_TIMEOUT)
```

## 📊 Métriques et monitoring

### **Tracking automatique**
- ⏱️ **Durées d'exécution** : Temps total et par étape
- 🔢 **Compteurs d'appels** : Statistiques des appels ORS
- 📈 **Taux de succès** : Ratios de réussite par opération
- 🎯 **Performances** : Métriques d'optimisation

### **Sessions d'optimisation**
```python
# Session automatique dans SmartRouteService
session_id = performance_tracker.start_optimization_session(
    origin="46.712,4.835",
    destination="48.857,2.352", 
    route_distance_km=462
)

# Métriques collectées automatiquement
performance_tracker.end_optimization_session(result)
```

## 🛠️ Utilisation avancée

### **Optimisation personnalisée**
```python
# Configuration des algorithmes
from src.services.optimization.constants import TollOptimizationConfig

TollOptimizationConfig.TOLL_DETECTION_BUFFER_M = 100.0  # Buffer de détection
TollOptimizationConfig.EARLY_STOP_ZERO_COST = True      # Arrêt anticipé
```

### **Intégration avec le cache**
```python
# Le SmartRouteService utilise automatiquement le cache SAM
# pour les données de péages et tarifs
smart_route = SmartRouteService()  # Cache intégré

# Accès au cache si nécessaire
cache = smart_route.intelligent_optimizer.toll_identifier.cache
toll_booths = cache.toll_booths  # Accès aux péages
```

### **Gestion d'erreurs**
```python
try:
    result = smart_route.compute_route_with_toll_limit(coordinates, max_tolls=2)
    
    if result["status"] == "SUCCESS":
        fastest = result["fastest"]
        cheapest = result["cheapest"]
    elif result["status"] == "NO_VALID_ROUTE_WITH_MAX_TOLLS":
        print("Aucune route trouvée avec cette contrainte")
    
except ValueError as e:
    print(f"Erreur de validation: {e}")
except Exception as e:
    print(f"Erreur système: {e}")
```

## 🚀 Points d'entrée principaux

### **Pour l'API REST**
```python
# Dans les contrôleurs Flask
from src.services.smart_route import SmartRouteService

smart_route = SmartRouteService()

@app.route('/api/routes/optimize')
def optimize_route():
    result = smart_route.compute_route_with_toll_limit(
        coordinates=request.json['coordinates'],
        max_tolls=request.json['max_tolls'],
        veh_class=request.json.get('veh_class', 'c1')
    )
    return jsonify(result)
```

### **Pour l'intégration**
```python
# Utilisation directe dans d'autres modules
from src.services.ors_service import ORSService

ors = ORSService()
if ors.test_all_set():
    route = ors.get_base_route(coordinates, include_tollways=True)
```