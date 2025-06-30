# 📊 Benchmark - Système de Monitoring des Performances

## 📋 Vue d'ensemble

Le module `benchmark` fournit un système complet de monitoring et d'analyse des performances pour le backend SAM. Il trace en temps réel les opérations d'optimisation d'itinéraires, mesure les temps d'exécution, compte les appels API et génère des rapports détaillés pour l'analyse des performances.

## 🏗️ Architecture

```
benchmark/
├── 📊 performance_tracker.py      # Tracker principal de performances
├── 📁 logs/                      # Logs et sessions de performance
│   ├── performance_YYYYMMDD.log  # Logs quotidiens des performances
│   └── session_route_*.json      # Sessions détaillées d'optimisation
└── 📄 __pycache__/               # Cache Python
```

## 🎯 Objectifs du système

### **Monitoring en temps réel**
- ⏱️ **Mesure des durées** : Tracking précis des temps d'exécution
- 📞 **Comptage API** : Suivi des appels vers OpenRouteService
- 🔍 **Détection de lenteurs** : Alertes automatiques pour opérations lentes
- 📊 **Métriques live** : Statistiques en temps réel pendant l'optimisation

### **Analyse et optimisation**
- 📈 **Identification des goulots** : Analyse automatique des bottlenecks
- 📋 **Rapports détaillés** : Summaries complets par session
- 🎯 **Recommandations** : Suggestions d'amélioration automatiques
- 📝 **Historique** : Conservation des métriques pour analyse long terme

## 🧩 Composants principaux

### **1. PerformanceTracker** - Tracker Principal

Classe principale gérant l'ensemble du système de monitoring avec thread-safety.

#### **Fonctionnalités core**
- 🔒 **Thread-safe** : Support des opérations concurrentes
- 📝 **Logging automatique** : Fichiers de logs quotidiens
- 💾 **Sessions JSON** : Sauvegarde détaillée de chaque optimisation
- ⚡ **Temps réel** : Affichage live des métriques pendant l'exécution

#### **Utilisation de base**
```python
from benchmark.performance_tracker import performance_tracker

# Le tracker est un singleton global, prêt à l'emploi
# Utilisé automatiquement par SmartRouteService

# Vérification de l'état
stats = performance_tracker.get_current_stats()
print(f"Opérations en cours: {stats.get('operations_count', 0)}")
```

---

### **2. Sessions d'optimisation** - Cycle de vie complet

Le système gère automatiquement des sessions complètes d'optimisation d'itinéraires.

#### **Démarrage de session**
```python
# Démarrage automatique dans SmartRouteService
session_id = performance_tracker.start_optimization_session(
    origin="48.259,7.446",      # Coordonnées origine (lat,lon)
    destination="45.785,3.114", # Coordonnées destination
    route_distance_km=462.3     # Distance estimée (optionnel)
)

print(f"Session démarrée: {session_id}")
# Exemple: "route_20250630_140257_162825"
```

#### **Fin de session avec résultat**
```python
# Fin automatique avec sauvegarde
optimization_result = {
    "status": "SUCCESS",
    "fastest": {"duration": 2847.5, "cost": 32.45},
    "cheapest": {"duration": 3124.1, "cost": 18.50},
    "min_tolls": {"duration": 3256.8, "cost": 12.30}
}

session_id = performance_tracker.end_optimization_session(optimization_result)
# → Génère automatiquement le rapport complet
```

#### **Exemple de rapport de session**
```
ROUTE OPTIMIZATION SESSION SUMMARY - route_20250630_140257_162825
================================================================
Route: 48.259,7.446 -> 45.785,3.114
Distance: 462.3 km
Total Duration: 2096.50ms (2.1s)
Operations Measured: 15
Total API Calls: 3
Toll Networks: ASF, APRR
Errors: 0

API CALLS BREAKDOWN:
  ORS_base_route: 2 calls (66.7%)
  ORS_avoid_tollways: 1 calls (33.3%)

PERFORMANCE BY OPERATION:
  ORS_avoid_tollways:
    Executions: 1x
    Total Time: 939.28ms (44.8% of total)
    Average: 939.28ms
    Min/Max: 939.28ms / 939.28ms

  ORS_base_route:
    Executions: 2x
    Total Time: 67.60ms (3.2% of total)
    Average: 33.80ms
    Min/Max: 12.67ms / 54.93ms

PERFORMANCE ANALYSIS:
  Slowest Single Operation: ORS_avoid_tollways (939.28ms)
  Most Time Consuming: ORS_avoid_tollways (939.28ms total)
  Most Frequent: ORS_base_route (2 executions)
  Average Time per API Call: 698.83ms
```

---

### **3. Mesure d'opérations** - Context Manager

Système élégant pour mesurer automatiquement les durées d'opération.

#### **Utilisation avec context manager**
```python
# Mesure automatique d'une opération
with performance_tracker.measure_operation("toll_identification"):
    tolls = identify_tolls_on_route(route_geometry)
    
# → Mesure automatique et logging si > 1s

# Avec détails supplémentaires
with performance_tracker.measure_operation(
    "route_calculation", 
    details={"coordinates_count": len(coordinates), "avoid_features": ["tollways"]}
):
    route = ors_service.call_ors(payload)
```

#### **Logging automatique des lenteurs**
```python
# Alertes automatiques selon la durée
# > 5000ms : WARNING log + alerte console
# > 1000ms : INFO log
# < 1000ms : Silencieux, stocké pour rapport final

# Exemple de logs automatiques:
# 2025-06-30 14:02:58 - WARNING - Slow operation: ORS_avoid_tollways took 939.28ms | Total API calls: 2
# 2025-06-30 14:02:59 - INFO - Operation: toll_identification took 1234.56ms | Total API calls: 3
```

---

### **4. Comptage des appels API** - Suivi intelligent

Comptage automatique avec logging périodique pour le suivi de progression.

#### **Comptage automatique**
```python
# Comptage simple
performance_tracker.count_api_call("ORS_base_route")
performance_tracker.count_api_call("ORS_avoid_tollways")

# Logging automatique tous les 10 appels
# Exemple: "API Progress: 20 total calls | Latest: ORS_base_route (#3)"
```

#### **Intégration dans ORSService**
```python
# Intégration automatique dans ors_service.py
class ORSService:
    def call_ors(self, payload):
        operation_name = ORSConfigManager.get_operation_name(payload)
        
        with performance_tracker.measure_operation(operation_name):
            performance_tracker.count_api_call(operation_name)
            response = requests.post(self.directions_url, json=payload)
            
        return response.json()
```

---

### **5. Gestion des erreurs** - Logging centralisé

Système de logging d'erreurs intégré aux sessions d'optimisation.

#### **Logging d'erreurs**
```python
# Erreur simple
performance_tracker.log_error("Route calculation failed: timeout")

# Erreur avec context
try:
    route = calculate_complex_route(coordinates)
except Exception as e:
    performance_tracker.log_error(f"Complex route calculation failed: {str(e)}")
    raise

# Les erreurs apparaissent dans le rapport final
```

---

### **6. Monitoring temps réel** - Statistiques live

Accès aux métriques en temps réel pendant l'optimisation.

#### **Statistiques en cours**
```python
# Affichage temps réel (appelé automatiquement)
stats = performance_tracker.get_current_stats()

# Sortie automatique:
# 📊 STATS TEMPS RÉEL:
#    Opérations: 8
#    Appels API: 3
#      - ORS_base_route: 2
#      - ORS_avoid_tollways: 1
#    Erreurs: 0
#    Temps écoulé: 1.8s
```

## 📊 Modèles de données

### **PerformanceMetric** - Métrique individuelle
```python
@dataclass
class PerformanceMetric:
    operation: str              # Nom de l'opération
    duration_ms: float          # Durée en millisecondes
    timestamp: str              # Timestamp ISO 8601
    thread_id: int              # ID du thread d'exécution
    details: Dict[str, Any]     # Détails supplémentaires
```

### **RouteOptimizationSession** - Session complète
```python
@dataclass
class RouteOptimizationSession:
    session_id: str             # ID unique de session
    start_time: str             # Début ISO 8601
    end_time: str               # Fin ISO 8601
    total_duration_ms: float    # Durée totale
    origin: str                 # Coordonnées origine
    destination: str            # Coordonnées destination
    route_distance_km: float    # Distance estimée
    metrics: List[PerformanceMetric]  # Toutes les métriques
    api_calls: Dict[str, int]   # Compteurs d'appels API
    toll_networks: List[str]    # Réseaux de péages utilisés
    optimization_result: Dict   # Résultat final d'optimisation
    errors: List[str]           # Erreurs rencontrées
```

## 🔧 Configuration et utilisation

### **Configuration automatique**
```python
# Configuration par défaut (modifiable)
tracker = PerformanceTracker(log_dir="benchmark/logs")

# Le tracker global est pré-configuré
from benchmark.performance_tracker import performance_tracker
# Prêt à l'emploi, aucune configuration requise
```

### **Structure des fichiers de logs**
```
benchmark/logs/
├── performance_20250630.log                    # Log quotidien
├── session_route_20250630_140257_162825.json  # Session détaillée
├── session_route_20250630_140340_523146.json  # Autre session
└── session_route_20250630_141205_789432.json  # ...
```

### **Format des logs quotidiens**
```log
2025-06-30 14:02:57 - performance_tracker - INFO - Started optimization session route_20250630_140257_162825: 48.259,7.446 -> 45.785,3.114
2025-06-30 14:02:58 - performance_tracker - WARNING - Slow operation: ORS_avoid_tollways took 939.28ms | Total API calls: 2
2025-06-30 14:02:59 - performance_tracker - INFO - [RAPPORT COMPLET DE SESSION]
```

### **Format des sessions JSON**
```json
{
  "session_id": "route_20250630_140257_162825",
  "start_time": "2025-06-30T14:02:57.162874",
  "end_time": "2025-06-30T14:02:59.259377", 
  "total_duration_ms": 2096.50,
  "origin": "48.259,7.446",
  "destination": "45.785,3.114",
  "route_distance_km": 462.3,
  "metrics": [...],
  "api_calls": {"ORS_base_route": 2, "ORS_avoid_tollways": 1},
  "toll_networks": ["ASF", "APRR"],
  "optimization_result": {...},
  "errors": []
}
```

## 📈 Analyse des performances

### **Analyse automatique des bottlenecks**
```python
# Analyse d'une session spécifique
bottlenecks = performance_tracker.analyze_performance_bottlenecks(
    session_file="session_route_20250630_140257_162825.json"
)

print("🔍 Opérations les plus lentes:")
for op in bottlenecks['slowest_operations'][:5]:
    print(f"  - {op['operation']}: {op['duration_ms']:.2f}ms")

print("📊 Opérations les plus fréquentes:")
for op, count in bottlenecks['most_frequent_operations'][:5]:
    print(f"  - {op}: {count}x")

print("💡 Recommandations:")
for rec in bottlenecks['recommendations']:
    print(f"  - {rec}")
```

### **Seuils d'alerte automatiques**
```python
# Alertes automatiques selon les seuils configurés:

# Opérations lentes
if duration_ms > 5000:  # 5 secondes
    log.warning("Slow operation detected")
elif duration_ms > 1000:  # 1 seconde  
    log.info("Notable operation duration")

# Trop d'appels API
if total_api_calls > 100:
    recommendations.append("High number of API calls - consider caching")

# Optimisation trop longue
if total_duration_ms > 60000:  # 1 minute
    recommendations.append("Optimization taking too long - consider timeout limits")
```

## 🚀 Intégration système

### **Intégration automatique**
Le système est déjà intégré dans tous les composants critiques :

- ✅ **SmartRouteService** - Sessions automatiques
- ✅ **ORSService** - Mesure des appels API  
- ✅ **IntelligentOptimizer** - Tracking des étapes
- ✅ **TollIdentifier** - Mesure de l'analyse spatiale
- ✅ **RouteCalculation** - Performance des calculs

### **Utilisation dans les contrôleurs**
```python
# Dans les contrôleurs Flask, le tracking est automatique
@app.route('/api/routes/optimize')
def optimize_route():
    # La session démarre automatiquement dans SmartRouteService
    result = smart_route_service.compute_route_with_toll_limit(
        coordinates=request.json['coordinates'],
        max_tolls=request.json['max_tolls']
    )
    # → Session se termine automatiquement avec logging complet
    
    return jsonify(result)
```

### **Monitoring de production**
```python
# Surveillance des performances en production
def monitor_performance():
    stats = performance_tracker.get_current_stats()
    
    if stats.get('elapsed_time_ms', 0) > 30000:  # 30 secondes
        alert_admin("Route optimization taking too long")
    
    if stats.get('errors_count', 0) > 0:
        alert_admin("Errors detected in route optimization")
```