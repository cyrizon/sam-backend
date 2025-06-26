# Refactorisation de la Stratégie Intelligente V2

## Vue d'ensemble

La stratégie intelligente V2 a été refactorisée pour respecter la contrainte de 350 lignes par fichier en décomposant les responsabilités en modules séparés.

## Structure Refactorisée

### Fichier Principal : `intelligent_segmentation_strategy_v2.py` (186 lignes)
- **Responsabilité** : Orchestration de l'algorithme principal en 9 étapes
- **Fonctions principales** :
  - `find_route_with_exact_tolls()` : Point d'entrée principal
  - `_ensure_osm_data_loaded()` : Chargement des données OSM
  - `_get_base_route()` : Calcul de la route de base
  - `_identify_tolls_on_base_route()` : Identification des péages
  - `_select_target_tolls()` : Sélection des péages prioritaires

### Modules Auxiliaires

#### 1. `segmentation_point_finder.py` (145 lignes)
- **Responsabilité** : Trouver les points de segmentation (motorway_links)
- **Fonctions principales** :
  - `find_segmentation_points()` : Trouve tous les points de découpage
  - `_find_next_toll_to_avoid()` : Identifie le prochain péage à éviter
  - `_find_last_exit_before_toll()` : Trouve la sortie avant un péage
  - `_find_motorway_link_for_junction()` : Associe une sortie à son lien
  - `_calculate_distance()` : Calcul de distance haversine

#### 2. `segment_calculator.py` (83 lignes)
- **Responsabilité** : Calculer les segments de route avec/sans péages
- **Fonctions principales** :
  - `create_segments_coordinates()` : Créer les coordonnées des segments
  - `calculate_all_segments()` : Calculer toutes les routes ORS

#### 3. `route_assembler.py` (107 lignes)
- **Responsabilité** : Assembler les segments et formater les résultats
- **Fonctions principales** :
  - `assemble_final_route_multi()` : Assemblage final multi-segments
  - `_build_route_geojson()` : Construction du GeoJSON
  - `_build_result_response()` : Formatage de la réponse finale

## Algorithme en 9 Étapes

1. **Route de base** : Calcul de la route incluant tous les péages
2. **Identification des péages** : Recherche des péages sur la route de base
3. **Sélection des péages** : Priorisation des systèmes ouverts
4. **Points de segmentation** : Recherche des sorties avant les péages à éviter
5. **Motorway_links** : Association des sorties aux liens routiers
6. **Création des segments** : Division du trajet en segments
7. **Calcul des segments** : Routes ORS avec/sans péages par segment
8. **Assemblage** : Fusion des segments sans points dupliqués
9. **Résultat final** : Formatage et retour de la route optimisée

## Avantages de la Refactorisation

### Lisibilité
- Chaque module a une responsabilité unique et claire
- Le fichier principal se concentre sur l'orchestration
- Les fonctions complexes sont isolées dans des modules dédiés

### Maintenabilité
- Respect de la contrainte de 350 lignes par fichier
- Séparation des préoccupations
- Tests unitaires par module possible

### Réutilisabilité
- Les modules peuvent être réutilisés par d'autres stratégies
- Logique métier isolée et testable indépendamment

## Tests

Les tests existants continuent de passer :
- `test_strategy_v2.py` : Tests unitaires de la stratégie
- `test_api_smart_route.py` : Tests d'intégration API

## Compatibilité

La refactorisation est entièrement rétrocompatible :
- Interface publique inchangée
- Comportement algorithmique identique
- Résultats API identiques

## Usage

```python
from src.services.toll.new_segmentation.intelligent_segmentation_strategy_v2 import IntelligentSegmentationStrategyV2

strategy = IntelligentSegmentationStrategyV2(ors_service, 'data/osm_export_toll.geojson')
result = strategy.find_route_with_exact_tolls(coordinates, target_tolls=2)
```

## Architecture

```
intelligent_segmentation_strategy_v2.py (orchestrateur)
├── segmentation_point_finder.py (recherche des points)
├── segment_calculator.py (calcul des segments)
├── route_assembler.py (assemblage final)
├── osm_data_parser.py (données OSM)
├── toll_matcher.py (matching péages)
└── intelligent_segmentation_helpers.py (cas spéciaux)
```
