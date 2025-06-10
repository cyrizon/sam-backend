# Stratégies d'Optimisation Budgétaire

Ce document explique le fonctionnement des différentes stratégies d'optimisation budgétaire pour le calcul d'itinéraires.

## 🎯 Vue d'ensemble

Le système utilise 4 stratégies principales + 1 stratégie de fallback pour optimiser les routes selon différentes contraintes budgétaires :

- **ZeroBudgetStrategy** : Routes gratuites (0€)
- **AbsoluteBudgetStrategy** : Budget fixe en euros
- **PercentageBudgetStrategy** : Budget en pourcentage du coût de base
- **FallbackStrategy** : Solutions de repli intelligentes

---

## 📍 1. ZeroBudgetStrategy (Budget Zéro)

### 🎯 Objectif
Trouver des itinéraires **complètement gratuits** en évitant tous les péages.

### 🔄 Fonctionnement
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Coordonnées   │───▶│  Route évitant   │───▶│   Vérification  │
│   (A → B)       │    │   les péages     │    │   coût = 0€     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┐
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SUCCESS       │ ou │   ATTENTION     │
                       │   Route gratuite│    │ Péages présents │
                       └─────────────────┘    └─────────────────┘
```

### ⚡ Algorithme
1. **Demander route sans péage** à l'API ORS
2. **Vérifier** s'il reste des péages sur le trajet
3. **Retourner** le résultat avec statut approprié

### 📊 Résultats possibles
- ✅ **Route 100% gratuite** trouvée
- ⚠️ **Route avec quelques péages** malgré l'évitement
- ❌ **Impossible** de trouver une route

---

## 💰 2. AbsoluteBudgetStrategy (Budget Fixe)

### 🎯 Objectif
Trouver des itinéraires respectant un **budget maximum en euros** (ex: 15€ max).

### 🔄 Fonctionnement
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Budget: 15€ max │───▶│   Route de base  │───▶│  Coût > 15€ ?   │
│ Coordonnées A→B │    │   Coût: 23€      │    │     OUI         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┘
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  OPTIMISATION   │───▶│   Test péages   │
                       │  Évitement des  │    │   individuels   │
                       │     péages      │    │                 │
                       └─────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┘
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Test combinai-  │───▶│ Meilleure route │
                       │ sons de péages  │    │ ≤ 15€ trouvée   │
                       └─────────────────┘    └─────────────────┘
```

### ⚡ Algorithme
1. **Calculer route de base** et son coût
2. **Si coût ≤ budget** → Retourner la route de base
3. **Sinon optimiser** :
   - Identifier péages les plus coûteux
   - Tester évitement des péages **individuels**
   - Tester **combinaisons** de péages
   - Arrêt anticipé si solution trouvée

### 📊 Critères d'optimisation
- **Fastest** : Route la plus rapide dans le budget
- **Cheapest** : Route la moins chère (priorité au budget)
- **Min Tolls** : Route avec le moins de péages

---

## 📈 3. PercentageBudgetStrategy (Budget Pourcentage)

### 🎯 Objectif
Réduire le coût de péage d'un **pourcentage du coût initial** (ex: 70% du coût de base).

### 🔄 Fonctionnement
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Pourcentage: 70%│───▶│   Route de base  │───▶│ Calcul limite   │
│ Coordonnées A→B │    │   Coût: 20€      │    │ 20€ × 70% = 14€│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┘
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  OPTIMISATION   │───▶│ Recherche routes│
                       │  Objectif: ≤14€ │    │   alternatives  │
                       └─────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┘
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Évitement péages│───▶│ Route ≤ 14€     │
                       │ + combinaisons  │    │ ou meilleure    │
                       └─────────────────┘    └─────────────────┘
```

### ⚡ Algorithme
1. **Calculer route de base** (coût de référence)
2. **Calculer limite** : `coût_base × pourcentage`
3. **Si déjà respecté** → Retourner route de base
4. **Optimiser** selon même logique qu'AbsoluteBudgetStrategy
5. **Enrichissement** avec péages à proximité

### 🎯 Spécificités
- **Référence dynamique** : Le budget dépend du coût initial
- **Recherche élargie** : Inclut péages proches du trajet
- **Pré-filtrage** : Ignore économies < 5% du budget

---

## 🆘 4. FallbackStrategy (Stratégie de Repli)

### 🎯 Objectif
Fournir des **alternatives intelligentes** quand aucune solution ne respecte le budget.

### 🔄 Fonctionnement par type de budget
```
                    ┌─────────────────────────┐
                    │   ÉCHEC STRATÉGIE       │
                    │      PRINCIPALE         │
                    └─────────────────────────┘
                                │
                    ┌───────────┴────────────┐
                    ▼                        ▼
            ┌─────────────────┐    ┌─────────────────┐
            │  BUDGET ZÉRO    │    │  BUDGET ABSOLU  │
            │  Recherche      │    │  Recherche      │
            │  route gratuite │    │  plus proche    │
            │  ou moins chère │    │  du budget      │
            └─────────────────┘    └─────────────────┘
                    │                        │
                    ▼                        ▼
            ┌─────────────────┐    ┌─────────────────┐
            │ BUDGET POURCENT │    │ FALLBACK GÉNÉRAL│
            │ Élargissement   │    │ Fastest among   │
            │ progressif du % │    │ Cheapest        │
            └─────────────────┘    └─────────────────┘
```

### ⚡ Stratégies spécialisées

#### 🆓 Zero Budget Fallback
1. **Recherche route 100% gratuite** (exhaustive)
2. **Sinon** → Route la moins chère possible
3. **Dernier recours** → Route de base

#### 💰 Absolute Budget Fallback
1. **Route la plus proche** du budget (±20%)
2. **Sinon** → Route la moins chère globale
3. **Dernier recours** → Route de base

#### 📈 Percentage Budget Fallback
1. **Élargissement progressif** : 110% → 125% → 150%
2. **Sinon** → Route la moins chère globale

#### 🔄 General Fallback
- **Fastest Among Cheapest** : Route la plus rapide parmi les moins chères

---

## 🏗️ Architecture et Orchestration

### 📋 BudgetRouteOptimizer (Orchestrateur)
```
┌─────────────────────────────────────────────────┐
│                ORCHESTRATEUR                    │
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │ Validation      │  │  Délégation pure    │   │
│  │ Paramètres      │  │  aux stratégies     │   │
│  └─────────────────┘  └─────────────────────┘   │
│           │                       │             │
│           ▼                       ▼             │
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │ Détection type  │  │   Fallback auto     │   │
│  │ de budget       │  │   si échec          │   │
│  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 🎯 Logique de sélection
```python
if budget == 0:
    → ZeroBudgetStrategy
elif pourcentage_défini:
    → PercentageBudgetStrategy  
elif budget_euros_défini:
    → AbsoluteBudgetStrategy
else:
    → FallbackStrategy (fastest_among_cheapest)
```

---

## 🔧 Composants Transversaux

### 📊 BudgetRouteResultManager
- **Gestion intelligente** des 3 critères (fastest, cheapest, min_tolls)
- **Priorité aux routes** dans le budget
- **Statistiques** de conformité budgétaire

### 🛠️ BudgetRouteCalculator
- **Calculs de routes** avec suivi de performance
- **Localisation et coût** des péages
- **Évitement** de polygones multiples

### ⚠️ BudgetErrorHandler
- **Gestion centralisée** des erreurs
- **Logging** des opérations
- **Messages** d'erreur contextuels

### ✅ BudgetRouteValidator
- **Validation contraintes budgétaires** : Respect des limites définies
- **Vérification évitement** : Péages indésirables correctement évités
- **Validation de cohérence** : Résultats logiques et cohérents

---

## 📈 Métriques et Performance

### 🎯 Optimisations implémentées
- **Arrêt anticipé** si route gratuite trouvée
- **Pré-filtrage** des économies négligeables
- **Cache** des coûts de péages
- **Limitation** des combinaisons testées
- **Suivi** détaillé des performances

### 📊 Indicateurs suivis
- Nombre de routes testées
- Taux de conformité budgétaire
- Temps d'exécution par opération
- Succès/échecs par stratégie

---

## 🔍 Algorithmes Spécialisés

### 💰 Calcul de Coût Marginal
```python
def add_marginal_cost(tolls, veh_class="c1"):
    """Calcule le coût incrémental de chaque péage selon la classe de véhicule"""
    # Péages ouverts : tarif fixe à l'entrée
    # Péages fermés : tarif selon distance parcourue
```

### 🎯 Validation de Contraintes Budgétaires
```python
def _is_within_budget(cost, budget_limit, budget_type):
    """Vérifie si un coût respecte la contrainte budgétaire"""
    if budget_type == "zero":
        return cost == 0
    elif budget_type in ["absolute", "percentage"]:
        return cost <= budget_limit
```

### 📊 Gestionnaire de Résultats Intelligent
```python
def update_with_route(route_data, base_cost):
    """Met à jour les meilleurs résultats selon les critères multiples"""
    # Priorité aux routes dans le budget
    # Comparaison multi-critères : coût, durée, péages
```

---

## ⚙️ Configuration Dynamique

```python
class BudgetOptimizationConfig:
    # Limites de recherche
    MAX_DISTANCE_SEARCH_M = 100000  # 100km pour péages à proximité
    MAX_COMB_SIZE = 8               # Limite combinaisons de péages
    
    # Optimisations
    PRE_FILTER_THRESHOLD = 0.05     # Seuil économies négligeables (5%)
    EARLY_STOP_FREE_ROUTE = True    # Arrêt si route gratuite trouvée
    
    # Performance
    MAX_FALLBACK_COMBINATIONS = 1000  # Limite pour éviter timeouts
    COMBINATION_PROGRESS_INTERVAL = 50  # Affichage progrès
```

---

## 🚀 Utilisation

```python
# Exemple d'utilisation
optimizer = BudgetRouteOptimizer(ors_service)

# Budget zéro
result = optimizer.compute_route_with_budget_limit(
    coordinates=[[lng1, lat1], [lng2, lat2]],
    max_price=0
)

# Budget 15€ max
result = optimizer.compute_route_with_budget_limit(
    coordinates=[[lng1, lat1], [lng2, lat2]], 
    max_price=15.0
)

# Budget 70% du coût de base
result = optimizer.compute_route_with_budget_limit(
    coordinates=[[lng1, lat1], [lng2, lat2]],
    max_price_percent=0.7
)

# Avec paramètres avancés
result = optimizer.compute_route_with_budget_limit(
    coordinates=[[lng1, lat1], [lng2, lat2]],
    max_price=20.0,
    veh_class="c2",  # Véhicule de classe 2
    max_comb_size=10  # Test jusqu'à 10 péages en combinaison
)
```

### 📋 Format de réponse
```json
{
  "fastest": {
    "route": {
      "type": "FeatureCollection",
      "features": [...]
    },
    "cost": 12.50,
    "duration": 3600,
    "toll_count": 2,
    "within_budget": true
  },
  "cheapest": {
    "route": {...}, 
    "cost": 8.20,
    "duration": 4200,
    "toll_count": 1,
    "within_budget": true
  },
  "min_tolls": {
    "route": {...},
    "cost": 15.00, 
    "duration": 3800,
    "toll_count": 1,
    "within_budget": false
  },
  "status": "BUDGET_SATISFIED",
  "statistics": {
    "routes_tested": 45,
    "routes_within_budget": 12,
    "budget_compliance_rate": 26.7
  }
}
```

### 📊 Codes de statut
- `BUDGET_ALREADY_SATISFIED` : Route de base respecte déjà le budget
- `BUDGET_SATISFIED` : Solution trouvée dans le budget
- `NO_ROUTE_WITHIN_BUDGET` : Aucune solution dans le budget
- `FREE_ALTERNATIVE_FOUND` : Route gratuite trouvée
- `CLOSEST_TO_BUDGET_FOUND` : Route la plus proche du budget
- `FALLBACK_BASE_ROUTE_USED` : Route de base utilisée en dernier recours

---

## ⚠️ Gestion d'Erreurs Spécialisées

### 🛡️ BudgetErrorHandler
```python
# Validation des paramètres d'entrée
validation_error = handle_budget_validation_error(max_price, max_price_percent)

# Gestion des erreurs ORS
ors_error = handle_ors_error(exception, operation_context)

# Logging contextualisé
log_operation_success("compute_budget_route", details)
log_operation_failure("optimize_route", error_message)
```

### 🔍 Types d'erreurs gérées
- **Validation** : Paramètres invalides (budget négatif, pourcentage > 100%)
- **Réseau** : Timeouts, erreurs de connexion ORS
- **Calcul** : Routes impossibles, péages introuvables
- **Performance** : Dépassement de limites de calcul

---

## 🔄 Différences avec l'Optimisation par Péages

| Aspect | **Budget** | **Péages** |
|--------|------------|------------|
| **Contrainte** | Coût maximum (€ ou %) | Nombre maximum de péages |
| **Priorité** | Économies financières | Réduction du nombre de péages |
| **Critère principal** | Respect du budget | Respect de max_tolls |
| **Recherche** | Péages les plus coûteux à éviter | Combinaisons optimales à éviter |
| **Fallback** | Routes proches du budget | Route de base simple |
| **Complexité** | Calculs de coûts continus | Contraintes discrètes |

### 🎯 Cas d'usage recommandés

#### 💰 Utiliser les stratégies Budget quand :
- L'utilisateur a un **budget fixe** à respecter
- Les **économies financières** sont prioritaires  
- Besoin de **flexibilité** sur le nombre de péages
- **Budget dynamique** selon le coût de référence

#### 🔢 Utiliser les stratégies Péages quand :
- L'utilisateur veut **limiter le nombre** de péages
- La **simplicité de conduite** est prioritaire
- Besoin de **prévisibilité** (nombre fixe de péages)
- **Contrainte ferme** sur max_tolls

Chaque stratégie est **optimisée** pour son cas d'usage spécifique et garantit les **meilleures performances** possibles selon les contraintes budgétaires définies.
