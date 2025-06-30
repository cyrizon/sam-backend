# Stratégies d'Optimisation des Péages

Ce document explique le fonctionnement des différentes stratégies d'optimisation pour le calcul d'itinéraires avec contraintes sur le nombre de péages.

## 🎯 Vue d'ensemble

Le système utilise 4 stratégies principales + 1 stratégie de fallback pour optimiser les routes selon différentes contraintes de péages :

- **NoTollStrategy** : Routes sans aucun péage (0 péage)
- **OneOpenTollStrategy** : Routes avec exactement 1 péage ouvert
- **ManyTollsStrategy** : Routes avec plusieurs péages autorisés (≥2)
- **FallbackStrategy** : Solutions de repli quand aucune solution n'est trouvée

---

## 🚫 1. NoTollStrategy (Aucun Péage)

### 🎯 Objectif
Trouver des itinéraires **complètement sans péage** en utilisant l'évitement des péages.

### 🔄 Fonctionnement
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Coordonnées   │───▶│  Route évitant   │───▶│   Vérification  │
│   (A → B)       │    │   les péages     │    │   péages = 0    │
│   max_tolls=0   │    │ (avoid_features) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┐
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SUCCESS       │ ou │   ATTENTION     │
                       │ Route sans péage│    │ Péages présents │
                       └─────────────────┘    └─────────────────┘
```

### ⚡ Algorithme
1. **Demander route sans péage** via `avoid_features: ["tollways"]`
2. **Localiser péages** sur la route calculée
3. **Vérifier** s'il reste des péages malgré l'évitement
4. **Retourner** avec statut approprié

### 📊 Résultats possibles
- ✅ **Route 100% sans péage** (coût = 0€)
- ⚠️ **Route avec quelques péages** malgré l'évitement
- ❌ **Impossible** de calculer une route

---

## 🎯 2. OneOpenTollStrategy (Un Péage Ouvert)

### 🎯 Objectif
Trouver des itinéraires passant par **exactement un péage à système ouvert** pour optimiser le coût.

### 🔄 Fonctionnement
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Coordonnées   │───▶│   Route de base  │───▶│ Localisation    │
│   (A → B)       │    │     Analyse      │    │ péages ouverts  │
│   max_tolls=1   │    │                  │    │   à proximité   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┐
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Test routes   │───▶│ Route optimale  │
                       │  via 1 péage    │    │  avec 1 péage   │
                       │     ouvert      │    │     ouvert      │
                       └─────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┐
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Si échec →     │───▶│ Stratégie Many  │
                       │ Fallback vers   │    │ Tolls (max=2)   │
                       │stratégie générale│    │   de secours    │
                       └─────────────────┘    └─────────────────┘
```

### ⚡ Algorithme
1. **Calculer route de base** pour analyse
2. **Localiser péages à proximité** (sur route + nearby)
3. **Filtrer péages ouverts** seulement (système ouvert)
4. **Pour chaque péage ouvert** :
   - Calculer route Départ → Péage → Arrivée
   - Éviter tous les autres péages indésirables
   - Fusionner les deux segments
5. **Si aucun résultat** → Fallback vers ManyTollsStrategy(max=2)

### 🎯 Spécificités
- **Péages ouverts prioritaires** : Tarif fixe payé à l'entrée
- **Route en 2 segments** : Départ→Péage + Péage→Arrivée
- **Évitement intelligent** : Autres péages exclus lors du calcul
- **Fallback automatique** : Stratégie générale si échec
- **Limitation géographique** : Recherche dans un rayon de 100km

---

## 🔢 3. ManyTollsStrategy (Plusieurs Péages)

### 🎯 Objectif
Trouver des itinéraires avec **un nombre limité de péages** (2, 3, 4... jusqu'à max_tolls).

### 🔄 Fonctionnement
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Coordonnées   │───▶│   Route de base  │───▶│ Localisation    │
│   (A → B)       │    │ + Analyse coûts  │    │ tous les péages │
│ max_tolls = N   │    │                  │    │  (route+nearby) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┐
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  OPTIMISATION   │───▶│ Test évitement  │
                       │   COMBINATOIRE  │    │ péages les plus │
                       │                 │    │    coûteux      │
                       └─────────────────┘    └─────────────────┘
                                                         │
                              ┌─────────────────────────┐
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Combinaisons de │───▶│ Routes avec ≤N  │
                       │ péages à éviter │    │     péages      │
                       │ (k=1,2,3...)    │    │                 │
                       └─────────────────┘    └─────────────────┘
```

### ⚡ Algorithme
1. **Calculer route de base** et localiser tous les péages
2. **Trier péages par coût** (du plus cher au moins cher)
3. **Tester évitement combinatoire** :
   - Combinaisons de 1 péage à éviter
   - Combinaisons de 2 péages à éviter
   - ... jusqu'à max_comb_size
4. **Pour chaque combinaison** :
   - Créer polygone d'évitement multipolygon
   - Calculer route alternative
   - Vérifier contrainte : péages ≤ max_tolls
   - Garder les meilleures solutions

### 🎯 Optimisations implémentées
- **Tri par coût décroissant** : Éviter d'abord les plus chers
- **Évitement des doublons** : Signature unique par combinaison
- **Arrêt anticipé** : Si coût = 0€ trouvé
- **Heuristique d'économie** : Skip si économie potentielle ≤ 0
- **Limitation combinatoire** : max_comb_size pour éviter explosion

### 📊 Critères d'optimisation
- **Fastest** : Route la plus rapide avec ≤ max_tolls péages
- **Cheapest** : Route la moins chère avec ≤ max_tolls péages  
- **Min Tolls** : Route avec le minimum de péages possible

---

## 🆘 4. FallbackStrategy (Stratégie de Repli)

### 🎯 Objectif
Fournir une **solution de base** quand aucune stratégie spécialisée ne trouve de solution.

### 🔄 Fonctionnement
```
                    ┌─────────────────────────┐
                    │   ÉCHEC STRATÉGIE       │
                    │      SPÉCIALISÉE        │
                    └─────────────────────────┘
                                │
                    ┌───────────┴────────────┐
                    ▼                        ▼
            ┌─────────────────┐    ┌─────────────────┐
            │  ROUTE DE BASE  │───▶│   CALCUL COÛT   │
            │   Standard      │    │   ET PÉAGES     │
            └─────────────────┘    └─────────────────┘
                                            │
                                            ▼
                                 ┌─────────────────┐
                                 │   RÉSULTAT      │
                                 │   UNIFORME      │
                                 │ (same fastest,  │
                                 │ cheapest,       │
                                 │ min_tolls)      │
                                 └─────────────────┘
```

### ⚡ Algorithme
1. **Calculer route de base** (aucun évitement)
2. **Localiser et coûter péages** sur cette route
3. **Formater résultat uniforme** : fastest = cheapest = min_tolls
4. **Retourner avec statut** spécifique au contexte d'échec

### 🎯 Cas d'usage
- **NoToll** : Impossible d'éviter tous les péages
- **OneToll** : Aucun péage ouvert viable trouvé
- **ManyTolls** : Aucune combinaison respectant max_tolls
- **Général** : Erreur système ou timeout

### ⚡ Stratégies spécialisées par contexte

#### 🆓 NoToll Fallback  
1. **Route de base** comme unique solution
2. **Information utilisateur** sur péages présents malgré évitement
3. **Statut explicite** : SOME_TOLLS_PRESENT

#### 🎯 OneToll Fallback
1. **Fallback vers ManyTollsStrategy(max=2)** si échec spécialisé
2. **Priorité aux solutions ≤ 1 péage** dans les résultats généraux
3. **Statut adaptatif** : GENERAL_STRATEGY ou GENERAL_STRATEGY_WITH_MIN_TOLLS

#### 🔢 ManyTolls Fallback
1. **Application fallback automatique** si aucune solution ≤ max_tolls
2. **Route de base** utilisée comme solution de repli
3. **Validation contraintes** maintenue même en fallback

---

## 🏗️ Architecture et Orchestration

### 📋 TollRouteOptimizer (Orchestrateur)
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
│  │ Sélection auto  │  │   Fallback auto     │   │
│  │ de stratégie    │  │   si échec          │   │
│  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 🎯 Logique de sélection
```python
if max_tolls == 0:
    → NoTollStrategy
elif max_tolls == 1:
    → OneOpenTollStrategy  
elif max_tolls >= 2:
    → ManyTollsStrategy
else:
    → FallbackStrategy
```

---

## 🔧 Composants Transversaux

### 📊 RouteResultManager
- **Gestion intelligente** des 3 critères (fastest, cheapest, min_tolls)
- **Comparaison multi-critères** : coût, durée, nombre de péages
- **Fallback automatique** avec route de base si nécessaire

### 🛠️ RouteCalculator
- **Calculs de routes** avec suivi de performance
- **Localisation et coût** des péages automatique
- **Évitement** de polygones multiples optimisé

### ✅ RouteValidator
- **Validation contraintes** : max_tolls respecté
- **Vérification évitement** : péages indésirables absents
- **Validation péage cible** : présence du péage voulu

### ⚠️ TollErrorHandler
- **Gestion centralisée** des erreurs spécifiques aux péages
- **Logging** des opérations avec contexte
- **Messages** d'erreur spécialisés

---

## 🔍 Algorithmes Spécialisés

### 🎯 Péages à Système Ouvert
```python
def is_toll_open_system(toll_id):
    """Identifie les péages à tarif fixe payé à l'entrée"""
    return (toll_id.startswith("A") and 
            not toll_id.startswith("APRR_F"))
```

### 🗺️ Fusion de Routes
```python
def merge_routes(route1, route2):
    """Fusionne deux segments de route en un itinéraire continu"""
    # Combine les coordonnées en évitant les doublons
    # Recalcule la durée et distance totales
```

### 🔺 Polygones d'Évitement
```python
def avoidance_multipolygon(tolls_to_avoid):
    """Crée un polygone composite pour éviter plusieurs péages"""
    # Union des zones d'évitement individuelles
    # Optimisation géométrique
```

---

## 📈 Métriques et Performance

### 🎯 Optimisations implémentées
- **Arrêt anticipé** : Si coût = 0€ ou solution optimale trouvée
- **Cache de signatures** : Évite de retester les mêmes combinaisons
- **Heuristiques d'économie** : Skip combinaisons non prometteuses
- **Limitation géographique** : Recherche dans rayon défini
- **Suivi détaillé** : Performance tracking par opération

### 📊 Indicateurs suivis
- Nombre de combinaisons testées
- Temps par opération (localisation, calcul, validation)
- Succès/échecs par stratégie
- Distribution des solutions par critère

### ⚙️ Configuration dynamique
```python
class TollOptimizationConfig:
    MAX_DISTANCE_SEARCH_M = 100000  # 100km de recherche
    MAX_NEARBY_TOLLS_TO_TEST = 10   # Limite péages à tester
    COMBINATION_PROGRESS_INTERVAL = 50  # Affichage progrès
    EARLY_STOP_ZERO_COST = True    # Arrêt si coût nul
```

---

## 🚀 Utilisation

```python
# Exemple d'utilisation
optimizer = TollRouteOptimizer(ors_service)

# Aucun péage
result = optimizer.compute_route_with_toll_limit(
    coordinates=[[lng1, lat1], [lng2, lat2]],
    max_tolls=0
)

# Maximum 1 péage
result = optimizer.compute_route_with_toll_limit(
    coordinates=[[lng1, lat1], [lng2, lat2]], 
    max_tolls=1
)

# Maximum 3 péages avec limite combinatoire
result = optimizer.compute_route_with_toll_limit(
    coordinates=[[lng1, lat1], [lng2, lat2]],
    max_tolls=3,
    max_comb_size=8  # Teste jusqu'à 8 péages en combinaison
)
```

### 📋 Format de réponse
```json
{
  "fastest": {
    "route": "...",
    "cost": 12.50,
    "duration": 3600,
    "toll_count": 2
  },
  "cheapest": {
    "route": "...", 
    "cost": 8.20,
    "duration": 4200,
    "toll_count": 1
  },
  "min_tolls": {
    "route": "...",
    "cost": 15.00, 
    "duration": 3800,
    "toll_count": 1
  },
  "status": "MULTI_TOLL_SUCCESS"
}
```

### 📊 Codes de statut
- `NO_TOLL_SUCCESS` : Route sans péage trouvée
- `SOME_TOLLS_PRESENT` : Route avec quelques péages malgré évitement
- `ONE_OPEN_TOLL_SUCCESS` : Solution avec exactement 1 péage ouvert
- `MULTI_TOLL_SUCCESS` : Solution respectant la contrainte max_tolls
- `MINIMUM_TOLLS_SOLUTION` : Solution avec minimum de péages possible
- `GENERAL_STRATEGY` : Fallback vers stratégie générale réussi
- `NO_VALID_ROUTE_WITH_MAX_TOLLS` : Aucune solution respectant max_tolls

---

## ⚠️ Gestion d'Erreurs Spécialisées

### 🛡️ TollErrorHandler
```python
# Validation des contraintes
if max_tolls < 0:
    return handle_invalid_max_tolls_error(max_tolls)

# Gestion des erreurs de calcul de route
try:
    route = calculate_route_through_toll(coordinates, toll)
except ORSConnectionError as e:
    return handle_ors_error(e, operation_context)

# Logging contextualisé
log_operation_success("compute_toll_route", toll_count=result_toll_count)
log_operation_failure("test_combination", combination_size=k)
```

### 🔍 Types d'erreurs gérées
- **Validation** : max_tolls négatif, coordonnées invalides
- **Réseau** : Timeouts ORS, erreurs de connexion
- **Calcul** : Routes impossibles, péages introuvables
- **Logique** : Contraintes non respectées, péages à éviter toujours présents

Chaque stratégie est **optimisée** pour son cas d'usage spécifique et garantit les **meilleures performances** possibles selon les contraintes de péages définies.
