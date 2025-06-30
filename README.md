# 🚗 SAM Backend - Optimisation d'Itinéraires avec Péages

Backend Python intelligent pour l'optimisation d'itinéraires en France avec gestion avancée des péages d'autoroute. Le système SAM (**S**mart **A**uto **M**apper) propose des routes optimisées selon le nombre de péages souhaité ou le budget disponible.

## 🎯 Objectifs du système

SAM est conçu pour résoudre un problème concret : **optimiser les trajets autoroutiers selon les contraintes de péages**. Contrairement aux solutions classiques qui proposent seulement "route rapide" vs "route sans péage", SAM permet de spécifier précisément :

- 🎯 **Nombre de péages maximum** : "Je veux traverser au maximum 2 péages"
- 💰 **Budget péages maximum** : "Je ne veux pas dépenser plus de 15€ en péages"
- 🚗 **Optimisation intelligente** : Remplacement automatique des péages fermés par des entrées/sorties d'autoroute

## 🏗️ Architecture technique

### **🧠 Moteur d'optimisation en 8 étapes**

```
1. 🔌 BaseRouteProvider     → Routes de base avec informations péages
2. 🔌 BaseRouteProvider     → Route alternative sans péages (fallback)
3. 🔍 TollIdentifier        → Identification spatiale des péages sur route  
4. 📊 [Analyse interne]     → Évaluation automatique des contraintes
5. 🎯 TollSelector          → Sélection intelligente des péages à éviter
6. 🔧 SegmentCreator        → Création des segments d'évitement géographiques
7. 📈 SegmentCalculator     → Calcul des routes alternatives optimisées
8. 🎨 RouteAssembler        → Assemblage et formatage des résultats finaux
```

### **🗂️ Modules principaux**

```
sam-backend/
├── 🌐 src/routes.py                    # API REST principale
├── 🧠 src/services/smart_route.py      # Service d'orchestration intelligent
├── ⚙️ src/services/optimization/       # Moteur d'optimisation (8 étapes)
├── 💾 src/cache/                       # Système de cache V2 avec linking
├── ⚙️ src/config/                      # Configuration environnement/ORS
├── 📊 benchmark/                       # Monitoring et analyse des performances
└── 🧪 tests/                          # Tests d'intégration et API
```

## 🚀 Fonctionnalités principales

### **🎯 Optimisation par nombre de péages**
```bash
POST /api/smart-route/tolls
{
  "coordinates": [[7.448, 48.262], [3.114, 45.785]],
  "max_tolls": 2
}
```

### **💰 Optimisation par budget** (à venir)
```bash
POST /api/smart-route/budget  
{
  "coordinates": [[7.448, 48.262], [3.114, 45.785]], 
  "max_budget": 15.0
}
```

### **🔍 Identification avancée de péages**
```bash
POST /api/tolls
{
  "type": "FeatureCollection",
  "features": [...]  # GeoJSON de route
}
```

## 🎯 Comment ça marche

### **1. Intelligence spatiale**
- 🗺️ **Cache V2 enrichi** : Base de données complète des péages français (ouverts/fermés)
- 🔗 **Linking avancé** : Connexions entre péages, entrées et sorties d'autoroute
- 📐 **Analyse géométrique** : Détection précise des péages sur trajectoire

### **2. Optimisation intelligente**
- 🎯 **Sélection par priorité** : Péages fermés évités en premier (plus coûteux)
- 🔄 **Remplacement automatique** : Péages fermés → entrées/sorties optimisées
- 📊 **Segments adaptatifs** : Zones d'évitement calculées géométriquement

### **3. Performance et monitoring**
- ⚡ **Sessions de performance** : Tracking automatique de chaque optimisation
- 📈 **Métriques temps réel** : Suivi des appels ORS et temps d'exécution
- 🔍 **Analyse des bottlenecks** : Identification automatique des lenteurs

## 📋 Installation et démarrage

### **1. Prérequis**
```bash
# Python 3.8+ requis
python --version

# Vérifier la disponibilité d'une instance OpenRouteService
curl "http://your-ors-instance:8080/ors/v2/directions/driving-car" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### **2. Installation**
```bash
# Cloner le repository
git clone https://github.com/cyrizon/sam-backend.git
cd sam-backend

# Installer les dépendances
pip install -r requirements.txt

# Configuration environnement
cp copy.env .env
# Éditer .env avec vos paramètres ORS
```

### **3. Configuration des données**
```bash
# Vérifier la présence des fichiers de cache dans data/
ls -la data/
# Doit contenir : toll_data.json, operators/, osm/

# Le cache V2 se charge automatiquement au démarrage
python app.py
# ✅ Cache V2 complet avec linking chargé avec succès
```

### **4. Démarrage**
```bash
# Mode développement
python app.py

# Mode production  
gunicorn app:app --bind 0.0.0.0:5000
```

## ⚙️ Configuration

### **Variables d'environnement (.env)**
```env
# OpenRouteService
ORS_API_URL=http://your-ors-instance:8080/ors/v2/directions
ORS_API_KEY=your-api-key-here

# Cache et données  
DATA_DIR=./data
CACHE_DIR=./osm_cache_test
```

### **Structure des données requises**
```
data/
├── toll_data.json              # Base de péages française
├── operators/                  # Tarifs par opérateur (ASF, APRR, etc.)
│   ├── ASF.json
│   ├── APRR.json
│   └── ...
└── osm/                        # Données OpenStreetMap
    ├── motorway_junctions.json
    └── complete_motorway_links.bin
```

## 🧪 Tests et validation

### **Tests d'intégration**
```bash
# Test complet d'optimisation 
pytest tests/test_api_optimization.py -v

# Test identification de péages
pytest tests/test_complete_object_system.py -v

# Tests de performance
pytest tests/test_ors_service.py -v
```

### **Monitoring des performances**
```bash
# Analyser les sessions du jour
python benchmark/analyze_performance.py

# Analyser une session spécifique  
python benchmark/analyze_performance.py benchmark/logs/session_route_20250630_140257.json
```

## 📊 Métriques et performance

### **Benchmarks typiques**
- ⚡ **Optimisation moyenne** : ~2-3 secondes
- 📞 **Appels ORS moyens** : 2-4 par optimisation  
- 🎯 **Taux de succès** : >95% sur routes françaises
- 💾 **Cache hit rate** : >90% sur péages français

### **Analyse automatique**
```bash
📊 STATS TEMPS RÉEL:
   Opérations: 8
   Appels API: 3
     - ORS_base_route: 2  
     - ORS_avoid_tollways: 1
   Erreurs: 0
   Temps écoulé: 1.8s
```

## 🔧 Développement et contribution

### **Architecture modulaire**
- 🧩 **Composants découplés** : Chaque étape est testable indépendamment
- 📝 **Documentation complète** : README détaillé dans chaque module
- 🔄 **Intégration continue** : Tests automatisés sur chaque modification

### **Points d'extension**
- 🌍 **Nouveaux pays** : Adapter le cache pour d'autres pays européens
- 💰 **Modes d'optimisation** : Ajouter optimisation par émissions CO2
- 🚛 **Classes de véhicules** : Support camions et véhicules lourds

## 📚 Documentation détaillée

- 📖 **[Services d'optimisation](src/services/optimization/README.md)** - Architecture du moteur
- 💾 **[Système de cache](src/cache/README.md)** - Gestion des données péages  
- ⚙️ **[Configuration](src/config/README.md)** - Paramétrage ORS et environnement
- 📊 **[Benchmark](benchmark/README.md)** - Monitoring et analyse des performances
- 🧪 **[Tests](tests/README.md)** - Suite de tests et validation

## 🚗 Exemples d'utilisation

### **Route Sélestat → Clermont-Ferrand (max 2 péages)**
```json
{
  "success": true,
  "strategy_used": "intelligent_optimization", 
  "toll_count": 2,
  "respects_constraint": true,
  "cost": 18.50,
  "distance": 462.3,
  "duration": 52.1,
  "route": { "type": "Feature", "geometry": {...} }
}
```

### **Péages automatiquement évités**
- **Départ**
- 🚫 **Péage de Fontaine-Larivière** (ouvert)
- 🚫 **Péage de Saint-Maurice** (fermé)
- 🚫 **Péage de Villefranche-Limas** (fermé)
- ✅ **Entrée Péage de Tarare-Est** (fermé, entrée optimisée sur système fermé)
- ✅ **Sortie Péage des Martres-d'Artière** (fermé)
- **Arrivée**
