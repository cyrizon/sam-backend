# 🔧 Services Common - Constantes et Utilitaires Partagés

## 📋 Vue d'ensemble

Le module `common` centralise les constantes, configurations et utilitaires partagés par tous les services d'optimisation. Il fournit une base commune pour maintenir la cohérence et faciliter la maintenance des paramètres système.

## 🏗️ Architecture

```
src/services/common/
├── 📊 base_constants.py    # Constantes de base pour l'optimisation
└── 📄 README.md           # Documentation du module
```

## 🎯 Objectifs du module

### **Centralisation**
- 🔧 **Constantes unifiées** : Valeurs partagées par tous les services
- 📊 **Codes de statut** : Statuts standardisés pour les résultats
- 🎛️ **Configuration** : Paramètres système centralisés
- 📝 **Documentation** : Constantes documentées et typées

### **Maintenance facilitée**
- 🔄 **Point unique** : Modification centralisée des paramètres
- 📏 **Standards** : Valeurs cohérentes dans tout le système
- 🛡️ **Validation** : Contrôles de cohérence centralisés
- 📋 **Traçabilité** : Historique des modifications

## 🧩 Composant principal

### **BaseOptimizationConfig** - Configuration de Base

Classe de base contenant toutes les constantes fondamentales pour l'optimisation de routes.

#### **Constantes de distance et proximité**
```python
from src.services.common.base_constants import BaseOptimizationConfig

# Configuration des distances
MAX_DISTANCE_SEARCH_M = 100000      # 100 km - Distance max de recherche de péages
MAX_NEARBY_TOLLS_TO_TEST = 10       # Nombre max de péages proches à tester

# Exemple d'utilisation
if distance_to_toll < BaseOptimizationConfig.MAX_DISTANCE_SEARCH_M:
    nearby_tolls = find_tolls_within_radius(
        point=location,
        max_results=BaseOptimizationConfig.MAX_NEARBY_TOLLS_TO_TEST
    )
```

#### **Constantes de performance**
```python
# Seuils de performance et progression
COMBINATION_PROGRESS_INTERVAL = 10   # Affichage progrès toutes les N combinaisons

# Dans les algorithmes d'optimisation
for i, combination in enumerate(toll_combinations):
    if i % BaseOptimizationConfig.COMBINATION_PROGRESS_INTERVAL == 0:
        print(f"Progression: {i}/{len(toll_combinations)} combinaisons testées")
```

#### **Chemins de fichiers**
```python
# Chemins vers les données
BARRIERS_CSV_PATH = "data/barriers.csv"    # Données de péages

# Utilisation
barriers_data = load_csv(BaseOptimizationConfig.BARRIERS_CSV_PATH)
```

#### **Valeurs par défaut**
```python
# Paramètres par défaut pour les calculs
DEFAULT_MAX_COMB_SIZE = 2    # Taille max des combinaisons de péages
DEFAULT_VEH_CLASS = "c1"     # Classe de véhicule par défaut

# Utilisation dans les fonctions
def optimize_route(coordinates, max_comb_size=None, veh_class=None):
    max_comb_size = max_comb_size or BaseOptimizationConfig.DEFAULT_MAX_COMB_SIZE
    veh_class = veh_class or BaseOptimizationConfig.DEFAULT_VEH_CLASS
```

## 📊 Codes de statut standardisés

### **StatusCodes** - Codes de Statut

Énumération complète des codes de statut pour les résultats d'optimisation.

#### **Codes de succès**
```python
from src.services.common.base_constants import BaseOptimizationConfig

StatusCodes = BaseOptimizationConfig.StatusCodes

# Succès généraux
SUCCESS = "SUCCESS"                           # Optimisation réussie
NO_TOLL_SUCCESS = "NO_TOLL_SUCCESS"          # Route sans péage trouvée
ONE_OPEN_TOLL_SUCCESS = "ONE_OPEN_TOLL_SUCCESS"  # Route avec 1 péage ouvert
MULTI_TOLL_SUCCESS = "MULTI_TOLL_SUCCESS"    # Route avec plusieurs péages

# Stratégies générales
GENERAL_STRATEGY = "GENERAL_STRATEGY"        # Stratégie générale appliquée
GENERAL_STRATEGY_WITH_MIN_TOLLS = "GENERAL_STRATEGY_WITH_MIN_TOLLS"
MINIMUM_TOLLS_SOLUTION = "MINIMUM_TOLLS_SOLUTION"  # Solution à péages minimaux
```

#### **Codes basés sur les contraintes**
```python
# Respect des contraintes (approche simplifiée)
CONSTRAINT_RESPECTED = "CONSTRAINT_RESPECTED"        # Contrainte respectée
CONSTRAINT_EXCEEDED_BY_ONE = "CONSTRAINT_EXCEEDED_BY_ONE"  # Dépassement d'1 unité
```

#### **Codes d'avertissement**
```python
# Avertissements
SOME_TOLLS_PRESENT = "SOME_TOLLS_PRESENT"    # Quelques péages présents
```

#### **Codes d'erreur**
```python
# Erreurs de route
NO_TOLL_ROUTE_NOT_POSSIBLE = "NO_TOLL_ROUTE_NOT_POSSIBLE"      # Route sans péage impossible
NO_OPEN_TOLL_FOUND = "NO_OPEN_TOLL_FOUND"                      # Aucun péage ouvert trouvé
NO_VALID_OPEN_TOLL_ROUTE = "NO_VALID_OPEN_TOLL_ROUTE"          # Route péage ouvert invalide
NO_VALID_ROUTE_WITH_MAX_TOLLS = "NO_VALID_ROUTE_WITH_MAX_TOLLS"  # Aucune route avec contrainte
```

### **Utilisation des codes de statut**
```python
def analyze_optimization_result(result):
    """Analyse le résultat d'une optimisation selon son statut."""
    
    status = result.get("status")
    
    if status == StatusCodes.SUCCESS:
        print("✅ Optimisation réussie")
        return True
        
    elif status == StatusCodes.NO_TOLL_SUCCESS:
        print("✅ Route sans péage trouvée")
        return True
        
    elif status == StatusCodes.CONSTRAINT_RESPECTED:
        print("✅ Contrainte respectée")
        return True
        
    elif status == StatusCodes.CONSTRAINT_EXCEEDED_BY_ONE:
        print("⚠️ Contrainte dépassée d'une unité")
        return "partial"
        
    elif status == StatusCodes.NO_VALID_ROUTE_WITH_MAX_TOLLS:
        print("❌ Aucune route trouvée avec cette contrainte")
        return False
        
    else:
        print(f"⚠️ Statut inconnu: {status}")
        return None
```

## 🔧 Utilisation pratique

### **Héritage pour modules spécialisés**
```python
# Dans src/services/optimization/constants.py
from src.services.common.base_constants import BaseOptimizationConfig

class TollOptimizationConfig(BaseOptimizationConfig):
    """Configuration spécialisée pour l'optimisation de péages."""
    
    # Hérite de toutes les constantes de base
    # + ajoute des constantes spécifiques
    
    # Optimisation des coûts
    EARLY_STOP_ZERO_COST = True
    UNLIMITED_BASE_COST = float('inf')
    
    # Détection de péages
    TOLL_DETECTION_BUFFER_M = 80.0
```

### **Validation avec les constantes**
```python
def validate_optimization_parameters(max_distance_m, max_tolls_to_test):
    """Valide les paramètres d'optimisation."""
    
    if max_distance_m > BaseOptimizationConfig.MAX_DISTANCE_SEARCH_M:
        raise ValueError(
            f"Distance max ({max_distance_m}m) dépasse la limite "
            f"({BaseOptimizationConfig.MAX_DISTANCE_SEARCH_M}m)"
        )
    
    if max_tolls_to_test > BaseOptimizationConfig.MAX_NEARBY_TOLLS_TO_TEST:
        raise ValueError(
            f"Nombre de péages ({max_tolls_to_test}) dépasse la limite "
            f"({BaseOptimizationConfig.MAX_NEARBY_TOLLS_TO_TEST})"
        )
    
    return True
```

### **Configuration dynamique**
```python
# Modification des constantes selon l'environnement
import os

class DynamicConfig(BaseOptimizationConfig):
    """Configuration dynamique selon l'environnement."""
    
    # Surcharge selon les variables d'environnement
    MAX_DISTANCE_SEARCH_M = int(os.getenv(
        'MAX_DISTANCE_SEARCH_M', 
        BaseOptimizationConfig.MAX_DISTANCE_SEARCH_M
    ))
    
    MAX_NEARBY_TOLLS_TO_TEST = int(os.getenv(
        'MAX_NEARBY_TOLLS_TO_TEST',
        BaseOptimizationConfig.MAX_NEARBY_TOLLS_TO_TEST
    ))
```

## 📋 Standards de développement

### **Ajout de nouvelles constantes**
```python
# Règles pour ajouter des constantes :
# 1. Documenter la purpose et l'unité
# 2. Utiliser des noms explicites
# 3. Grouper par domaine fonctionnel
# 4. Ajouter des exemples d'utilisation

class BaseOptimizationConfig:
    # === Nouvelle catégorie ===
    NEW_PARAMETER_SECONDS = 30  # Timeout pour nouvelle fonctionnalité (secondes)
    NEW_THRESHOLD_PERCENT = 0.1  # Seuil de tolérance (10%)
```

### **Codes de statut**
```python
# Règles pour les codes de statut :
# 1. Noms explicites et cohérents
# 2. Groupés par type (SUCCESS, ERROR, WARNING)
# 3. Pas de codes numériques, utiliser des strings
# 4. Documenter les conditions d'usage

class StatusCodes:
    # Nouveau code de succès
    NEW_SUCCESS_CASE = "NEW_SUCCESS_CASE"  # Description du cas
    
    # Nouveau code d'erreur
    NEW_ERROR_CASE = "NEW_ERROR_CASE"      # Description de l'erreur
```

## 🔍 Surveillance et monitoring

### **Constantes de monitoring**
```python
# Ajout de constantes pour le monitoring
class BaseOptimizationConfig:
    # Intervalles de monitoring
    PERFORMANCE_LOG_INTERVAL = 100  # Log perf toutes les 100 opérations
    HEALTH_CHECK_INTERVAL = 300     # Health check toutes les 5 minutes
    
    # Seuils d'alerte
    MAX_RESPONSE_TIME_MS = 5000     # Temps de réponse maximum (5s)
    ERROR_RATE_THRESHOLD = 0.05     # Taux d'erreur maximum (5%)
```
