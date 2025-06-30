# 🗄️ Cache System - Système de Cache Avancé

## 📋 Vue d'ensemble

Le système de cache de SAM est un composant sophistiqué qui gère le stockage, la sérialisation et l'accès aux données géospatiales critiques pour l'optimisation d'itinéraires. Il combine données OSM, informations de péages, tarifications et liaisons autoroutières dans un système haute performance.

## 🏗️ Architecture

```
src/cache/
├── 📁 managers/           # Gestionnaires de cache avec logique métier
├── 📁 models/             # Modèles de données (péages, liaisons, tarifs)
├── 📁 linking/            # Système de liaison autoroutière
├── 📁 parsers/            # Parseurs de données externes
├── 📁 pricing/            # Gestion des tarifs et coûts
├── 📁 serialization/      # Sérialisation binaire haute performance
├── 📁 services/           # Services spécialisés (association péages)
└── 📁 utils/              # Utilitaires partagés
```

## 🎯 Objectifs du système

### **Performance**
- ⚡ **Chargement rapide** : Sérialisation binaire pour des temps de démarrage < 2s
- 🧠 **Mémoire optimisée** : Structures de données compactes
- 🔍 **Recherche spatiale** : Index Rtree pour requêtes géospatiales sub-millisecondes

### **Complétude des données**
- 🛣️ **Péages français** : Tous les péages ouverts et fermés
- 💰 **Tarifs réels** : 15+ opérateurs avec tarifs à jour
- 🔗 **Liaisons autoroutières** : Segments complets avec connectivité
- 🗺️ **Données OSM** : Géométries et métadonnées enrichies

### **Fiabilité**
- ✅ **Validation des données** : Contrôles d'intégrité automatiques
- 🔄 **Mise à jour incrémentale** : Rechargement sans interruption
- 📊 **Statistiques détaillées** : Monitoring des performances

## 🧩 Composants principaux

### **1. Managers - Orchestrateurs du cache**

#### **CacheManagerWithLinking** (Gestionnaire principal)
```python
# Chargement complet avec liaisons autoroutières
cache = CacheManagerWithLinking(data_dir)
success = cache.load_all_including_motorway_linking()

# Accès aux données
toll_booths = cache.toll_booths           # Liste des péages
operators = cache.get_available_operators() # Opérateurs disponibles
links = cache.complete_motorway_links      # Liaisons complètes
```

**Fonctionnalités** :
- 🔗 **Liaison autoroutière** : Construction de segments complets
- 💰 **Gestion des prix** : Intégration des tarifs par opérateur
- 📊 **Statistiques** : Métriques de performance et validation
- 🎯 **Association péages** : Liaison péages ↔ segments autoroutiers

#### **CacheManagerWithPricing** (Gestionnaire des tarifs)
- 💶 **Calcul des coûts** : Prix par catégorie de véhicule
- 🏢 **Opérateurs** : Gestion de 15+ opérateurs français
- 📈 **Tarifs dynamiques** : Prix au km et péages ouverts

### **2. Models - Structures de données**

#### **TollBoothStation** (Station de péage)
```python
@dataclass
class TollBoothStation:
    osm_id: str                    # Identifiant OSM unique
    name: Optional[str]            # Nom du péage
    operator: Optional[str]        # Opérateur (ASF, APRR, etc.)
    coordinates: List[float]       # [longitude, latitude]
    toll_type: str                 # "O" (ouvert) ou "F" (fermé)
    
    @property
    def is_open_toll(self) -> bool:
        return self.toll_type == "O"
```

#### **CompleteMotorwayLink** (Liaison autoroutière complète)
- 🛣️ **Segments connectés** : Entrées et sorties liées
- 📏 **Distance** : Longueur précise du segment
- 🎯 **Péages associés** : Liste des péages sur le segment
- 🗺️ **Géométrie** : Coordonnées du tracé

### **3. Linking - Système de liaison**

#### **MotorwayLinkOrchestrator**
```python
orchestrator = MotorwayLinkOrchestrator(max_distance_m=2.0)
complete_links = orchestrator.build_complete_links(entries, exits)
```

**Processus** :
1. **Analyse spatiale** : Détection des correspondances entrée/sortie
2. **Validation géométrique** : Vérification des distances
3. **Construction des liens** : Création des segments complets
4. **Optimisation** : Élimination des doublons et orphelins

### **4. Serialization - Performance**

#### **CacheSerializer** (Sérialisation principale)
```python
serializer = CacheSerializer("cache_directory")

# Sauvegarde
serializer.save_cache_data(toll_booths, operators_data)

# Chargement
toll_booths, operators = serializer.load_cache_data()
```

**Formats** :
- 📦 **Binaire** : Pickle optimisé pour les structures complexes
- 📄 **JSON** : Métadonnées et configurations
- 🗜️ **Compression** : Réduction de l'espace disque

## 🔧 Utilisation

### **Initialisation complète**
```python
from src.cache.managers.cache_manager_with_linking import CacheManagerWithLinking

# Initialisation
data_dir = "path/to/data"
cache = CacheManagerWithLinking(data_dir)

# Chargement complet
success = cache.load_all_including_motorway_linking()

if success:
    print(f"✅ {len(cache.toll_booths)} péages chargés")
    print(f"✅ {len(cache.complete_motorway_links)} liaisons créées")
    print(f"✅ {len(cache.get_available_operators())} opérateurs disponibles")
```

### **Recherche de péages**
```python
# Péages dans une zone
nearby_tolls = cache.find_tolls_near_point(longitude, latitude, radius_m=1000)

# Péages ouverts seulement
open_tolls = [t for t in cache.toll_booths if t.is_open_toll]

# Par opérateur
aprr_tolls = [t for t in cache.toll_booths if t.operator == "APRR"]
```

### **Calcul de coûts**
```python
# Prix pour une liaison autoroutière
link = cache.complete_motorway_links[0]
cost = cache.pricing_manager.calculate_link_cost(link, vehicle_category="c1")

# Coût d'un péage ouvert
open_toll = cache.get_open_toll_by_name("Fontaine Larivière")
toll_cost = cache.pricing_manager.get_open_toll_price(open_toll, "c1")
```

## 📊 Métriques de performance

### **Temps de chargement typiques**
- 🚀 **Cache à froid** : ~1.5-2.0 secondes
- ⚡ **Cache chaud** : ~0.3-0.5 secondes
- 🔗 **Construction des liaisons** : ~0.8-1.2 secondes
- 💰 **Chargement des tarifs** : ~0.1-0.2 secondes

### **Utilisation mémoire**
- 📦 **Péages** : ~2-3 MB (800+ stations)
- 🛣️ **Liaisons** : ~5-8 MB (segments complets)
- 💶 **Tarifs** : ~0.5-1 MB (15+ opérateurs)
- 🗺️ **Géométries** : ~10-15 MB (données OSM)

## 🛠️ Configuration

### **Variables d'environnement**
```bash
# Répertoire des données
DATA_DIR=/path/to/data

# Répertoire de cache
CACHE_DIR=/path/to/cache

# Seuils de distance (mètres)
MAX_LINKING_DISTANCE=2.0
MAX_TOLL_ASSOCIATION_DISTANCE=1.5
```

### **Structure des données attendue**
```
data/
├── osm/
│   ├── toll_stations.geojson     # Péages OSM
│   └── motorway_segments.geojson # Segments autoroutiers
└── operators/
    ├── open_tolls.csv            # Tarifs péages ouverts
    └── price_per_km.csv          # Prix au kilomètre
```

## 🔍 Debugging et monitoring

### **Logs détaillés**
```python
# Activation du logging détaillé
import logging
logging.getLogger('cache').setLevel(logging.DEBUG)

# Statistiques de chargement
stats = cache.get_loading_statistics()
print(f"Péages chargés: {stats['toll_booths_count']}")
print(f"Liaisons créées: {stats['complete_links_count']}")
print(f"Temps total: {stats['total_loading_time_ms']}ms")
```

### **Validation des données**
```python
# Contrôle d'intégrité
validation_result = cache.validate_data_integrity()
if not validation_result.is_valid:
    print("❌ Erreurs détectées:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

## 🚀 Extensions futures

### **Améliorations prévues**
- 🌍 **Support multi-pays** : Extension au-delà de la France
- 🕐 **Tarifs variables** : Gestion des tarifs par période
- 🔄 **Mise à jour automatique** : Synchronisation avec sources externes
- 📱 **API REST** : Accès distant aux données de cache

### **Optimisations techniques**
- 🧠 **Cache distribué** : Support multi-instance
- ⚡ **Chargement parallèle** : Optimisation des performances
- 🗜️ **Compression avancée** : Réduction de l'empreinte mémoire

---

## 📚 Documentation des sous-modules

- **[Managers](./managers/README.md)** - Gestionnaires de cache
- **[Models](./models/README.md)** - Modèles de données
- **[Linking](./linking/README.md)** - Système de liaison
- **[Serialization](./serialization/README.md)** - Sérialisation
- **[Services](./services/README.md)** - Services spécialisés
- **[Utils](./utils/README.md)** - Utilitaires

---

*Dernière mise à jour : Juin 2025*
