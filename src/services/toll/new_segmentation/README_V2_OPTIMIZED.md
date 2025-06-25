# Stratégie de Segmentation Intelligente V2 Optimisée

## Vue d'ensemble

La **Stratégie V2 Optimisée** représente une évolution majeure de l'algorithme de segmentation intelligente, s'inspirant des meilleures performances de la V3/V4 tout en optimisant les aspects critiques identifiés.

## Optimisations Clés

### 1. Travail sur les Segments Tollways (comme V3/V4)

**AVANT (V2 classique)** :
- Travail sur la route complète
- Recherche géographique des péages sur toute la route
- Segmentation basée sur les points de sortie individuels

**APRÈS (V2 Optimisée)** :
- Extraction des segments tollways d'ORS (`extras.tollways`)
- Travail segment par segment (plus précis)
- Utilisation de la structure naturelle des segments payants/gratuits

```python
# Extraction des segments tollways
tollways_data = self._extract_tollways_segments(base_route)
segments = tollways_data['segments']  # [{'is_toll': True/False, 'start_waypoint': int, 'end_waypoint': int}]
```

### 2. Pré-matching des Péages OSM/CSV au Chargement

**PROBLÈME IDENTIFIÉ** :
- Re-matching des péages OSM/CSV à chaque requête (coûteux)
- Attribut `csv_role` ('O'/'F') non disponible immédiatement
- Recherches répétitives dans les données CSV

**SOLUTION OPTIMISÉE** :
- Matching OSM/CSV une seule fois au chargement (`osm_data_parser.py`)
- Chaque `TollStation` a son `csv_match` pré-calculé
- `csv_role` immédiatement disponible pour la logique de sélection

```python
# Dans osm_data_parser.py
def _prematch_tolls_with_csv(self):
    """Pré-matche les péages OSM avec les données CSV au chargement."""
    matcher = TollMatcher()
    matched_tolls = matcher.match_osm_tolls_with_csv(osm_tolls_dict)
    self._associate_csv_matches(matched_tolls)

# Chaque TollStation a maintenant :
toll_station.csv_match = {
    'role': 'O' ou 'F',  # CLÉ pour l'optimisation
    'name': 'Nom CSV',
    'id': 'ID CSV'
}
```

### 3. Utilisation des Motorway_Junctions + Motorway_Links Liés

**AVANT** :
- Recherche géographique des sorties à chaque calcul
- Pas d'exploitation des liens OSM pré-existants

**APRÈS** :
- Utilisation des `motorway_junctions` avec leurs `linked_motorway_links`
- Pas de recherche géographique inutile (déjà fait au chargement)
- Accès direct aux sorties liées via la structure OSM

### 4. Logique des Segments Gratuits Optimisée

**RÈGLE CLÉE** : Ne pas utiliser les segments gratuits entre deux péages fermés (`csv_role='F'`)

```python
def _apply_free_segments_logic(self, segments, selected_tolls):
    """Ne pas utiliser segments gratuits entre péages fermés."""
    closed_tolls = [t for t in selected_tolls if t.csv_role == 'F']
    
    if len(closed_tolls) >= 2:
        # Supprimer les segments gratuits intermédiaires
        segments = [s for s in segments if not self._is_free_segment_between_closed_tolls(s, closed_tolls)]
    
    return segments
```

### 5. Sélection des Péages Optimisée

**PRIORISATION** : Système ouvert (`csv_role='O'`) > Système fermé (`csv_role='F'`)

```python
def _select_target_tolls_optimized(self, tolls_on_segments, target_count):
    """Sélection priorisant le système ouvert (disponible immédiatement)."""
    open_system_tolls = [t for t in tolls_on_segments if t.csv_role == 'O']
    closed_system_tolls = [t for t in tolls_on_segments if t.csv_role != 'O']
    
    # Prioriser les péages ouverts
    selected = open_system_tolls[:target_count]
    remaining = target_count - len(selected)
    selected.extend(closed_system_tolls[:remaining])
    
    return selected
```

## Architecture Optimisée

### Flux d'Exécution

```
1. Route de base + extraction segments tollways
   ├── Utilisation d'ORS extras.tollways
   └── Structure naturelle payant/gratuit

2. Identification péages pré-matchés sur segments
   ├── Utilisation des csv_match pré-calculés
   ├── csv_role immédiatement disponible
   └── Pas de re-matching

3. Sélection péages cibles (système ouvert prioritaire)
   ├── Tri par csv_role ('O' > 'F')
   └── Sélection optimisée

4. Segmentation intelligente basée tollways
   ├── Analyse segments vs péages sélectionnés
   ├── Utilisation motorway_junctions liés
   └── Logique segments gratuits optimisée

5. Calcul routes + assemblage final
   └── Utilisation des modules existants optimisés
```

### Modules Impliqués

```
intelligent_segmentation_v2_optimized.py  # Module principal
├── osm_data_parser.py                   # Pré-matching au chargement
├── toll_matcher.py                      # Matching OSM/CSV (une seule fois)
├── hybrid_strategy/
│   ├── tollways_analyzer.py            # Analyse segments tollways
│   └── segment_avoidance_manager.py    # Gestion évitement segments
└── linking/junction_linker.py           # Liens motorway_junctions
```

## Gains de Performance Attendus

### 1. Réduction des Calculs Répétitifs
- **Matching OSM/CSV** : 1 fois au chargement vs N fois par requête
- **Recherches géographiques** : Utilisation des liens OSM pré-calculés
- **Analyse des péages** : `csv_role` immédiatement disponible

### 2. Optimisation de la Segmentation
- **Segments tollways** : Structure naturelle plus précise que route complète
- **Logique gratuits** : Évite les calculs inutiles entre péages fermés
- **Sélection péages** : Priorisation intelligente système ouvert

### 3. Réduction de la Complexité
- **Cache pré-calculé** : Moins de logique complexe à l'exécution
- **Segments naturels** : Alignement avec la structure ORS
- **Liens OSM** : Exploitation maximale des données disponibles

## Tests et Validation

### Tests Unitaires
```bash
python test_intelligent_segmentation_v2_optimized.py
```

### Tests d'Intégration
1. **Test extraction tollways** : Validation segments ORS
2. **Test pré-matching** : Vérification csv_role disponible
3. **Test sélection optimisée** : Priorisation système ouvert
4. **Test logique gratuits** : Règle péages fermés

### Cas de Test Recommandés
1. **Route multi-segments** : Mélange payant/gratuit
2. **Péages système ouvert** : Priorisation correcte
3. **Péages non-matchés** : Fallback système fermé
4. **Segments entre péages fermés** : Évitement segments gratuits

## Migration et Déploiement

### Rétrocompatibilité
- Interface identique à la V2 classique
- Fallback automatique si pré-matching échoue
- Logs détaillés pour debugging

### Configuration Requise
- Cache OSM initialisé avec pré-matching
- Données CSV accessibles au chargement
- Structure tollways dans les réponses ORS

### Monitoring
- Métriques de performance (temps de calcul)
- Taux de réussite du pré-matching
- Qualité des segments générés

## Conclusion

La **V2 Optimisée** combine les meilleures approches de la V3/V4 (segments tollways) avec des optimisations critiques (pré-matching, liens OSM) pour offrir :

- **Performance** : Réduction drastique des calculs répétitifs
- **Précision** : Travail sur segments naturels + csv_role fiable
- **Robustesse** : Fallbacks et gestion d'erreurs améliorés
- **Maintenabilité** : Code mieux structuré et testé

Cette approche représente l'état de l'art pour la segmentation intelligente des itinéraires à péages.
