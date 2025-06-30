# Cache Sérialisé OSM - Documentation

## Vue d'ensemble

Le système de cache sérialisé OSM permet d'accélérer considérablement le démarrage de l'application en sauvegardant les données OSM pré-traitées sur disque avec compression.

## Architecture

```
src/cache/
├── serialization/          # Modules de sérialisation
│   ├── __init__.py
│   ├── cache_serializer.py      # Sérialiseur principal
│   ├── cache_metadata.py        # Gestion des métadonnées
│   └── compression_utils.py     # Utilitaires de compression
├── cached_osm_manager.py        # Gestionnaire de cache intégré
└── __init__.py                  # Interface globale mise à jour

osm_cache/                       # Dossier de cache (racine projet)
├── metadata.json               # Métadonnées du cache
├── cache_data.bin             # Données compressées
└── .gitignore                 # Ignore les fichiers de cache
```

## Fonctionnement au Démarrage

### Logique de Cache Intelligente

1. **Vérification du cache** : L'application regarde d'abord si un cache valide existe dans `osm_cache/`
2. **Chargement rapide** : Si le cache existe et est valide (hash du fichier source inchangé), chargement en ~0.5s
3. **Construction du cache** : Si le cache n'existe pas ou est invalide, parsing du GeoJSON et création du cache
4. **Sauvegarde automatique** : Le nouveau cache est automatiquement sauvegardé pour les prochains démarrages

### Intégration des Caches

- **Cache OSM** : Chargé automatiquement avec `load_osm_data_with_cache()`
- **Cache Toll** : Initialisé automatiquement lors du chargement OSM (plus besoin d'initialisation manuelle)
- **Péages pré-matchés** : Sauvegardés et restaurés dans le cache (272/1478 péages matchés)

### 1. Sérialisation avec Compression

- **Compression LZMA** : Meilleur taux de compression pour gros fichiers (défaut)
- **Compression GZIP** : Plus rapide pour fichiers moyens
- **Sans compression** : Pour petits fichiers ou debugging

### 2. Validation d'Intégrité

- **Hash SHA-256** du fichier source pour détecter les modifications
- **Métadonnées** avec timestamps et statistiques
- **Validation automatique** avant chargement du cache

### 3. Performance

- **Chargement rapide** : Évite le parsing complet du GeoJSON
- **Compression efficace** : Réduit l'espace disque utilisé
- **Auto-détection** : Choix automatique de la méthode optimale

## Utilisation

### Chargement Simple

```python
from src.cache import osm_data_cache

# Chargement avec cache automatique
success = osm_data_cache.load_osm_data_with_cache("data/osm_export_toll.geojson")

if success:
    # Données disponibles dans osm_data_cache.osm_parser
    toll_stations = osm_data_cache.osm_parser.toll_stations
    junctions = osm_data_cache.osm_parser.motorway_junctions
```

### Chargement Avancé

```python
from src.cache.cached_osm_manager import CachedOSMDataManager
from src.cache.serialization.compression_utils import CompressionType

# Gestionnaire personnalisé
cache_manager = CachedOSMDataManager("custom_cache_dir")

# Chargement avec options
success = cache_manager.load_osm_data_with_cache(
    osm_file_path="data/osm_export_toll.geojson",
    force_reload=False,  # Force le rechargement depuis le source
    compression_type=CompressionType.LZMA  # Type de compression
)
```

### Gestion du Cache

```python
# Vérifier si le cache existe
if cache_manager.cache_serializer.is_cache_available("data/osm_export_toll.geojson"):
    print("Cache disponible")

# Obtenir les informations du cache
cache_info = cache_manager.get_cache_info()
if cache_info:
    cache_info.print_summary()

# Nettoyer le cache
cache_manager.clear_cache()
```

## Tests et Benchmarks

### Script de Test

```bash
# Test complet avec benchmark
python test_cache_serialization.py

# Nettoyer le cache avant les tests
python test_cache_serialization.py --clean

# Benchmark seulement
python test_cache_serialization.py --benchmark-only
```

### Exemple de Sortie

```
🚀 TEST 1: Premier chargement (création du cache)
✅ Premier chargement réussi en 8.45s
   📊 Données chargées:
      - Péages: 1478
      - Junctions: 8679
      - Links: 13914

🚀 TEST 2: Chargement depuis le cache
✅ Chargement depuis cache réussi en 1.23s
🚀 Accélération: 6.9x plus rapide
⏱️ Temps économisé: 7.22s
```

## Métadonnées du Cache

Le fichier `metadata.json` contient :

```json
{
  "version": "1.0",
  "creation_time": "2025-06-27T20:30:00",
  "source_file": "data/osm_export_toll.geojson",
  "source_hash": "abc123...",
  "source_size": 52428800,
  "toll_stations_count": 1478,
  "motorway_junctions_count": 8679,
  "motorway_links_count": 13914,
  "matched_tolls_count": 272,
  "compression_enabled": true,
  "cache_size": 8388608
}
```

## Migration

Le système est conçu pour être **rétrocompatible** :

1. **Première utilisation** : Charge depuis le GeoJSON et crée le cache
2. **Utilisations suivantes** : Charge depuis le cache si valide
3. **Modifications du source** : Détecte automatiquement et recharge

### Intégration dans l'Application

Le cache sérialisé est automatiquement intégré au démarrage de l'application via `src/__init__.py` :

```python
# Application startup (src/__init__.py)
def create_app():
    # ...configuration...
    
    print("🚦 Initialisation du cache global OSM avec sérialisation...")
    from src.cache import osm_data_cache
    
    # Chargement automatique avec cache - regarde d'abord si le cache existe
    osm_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "osm_export_toll.geojson")
    success = osm_data_cache.load_osm_data_with_cache(osm_file_path)
    
    if success:
        print("✅ Cache OSM chargé avec succès")
    else:
        print("❌ Erreur lors du chargement du cache OSM")
```

**Note importante :** Le `toll_data_cache` est maintenant initialisé automatiquement lors du chargement du cache OSM, plus besoin de l'initialiser manuellement.

## Performance Attendue

- **Premier démarrage** : ~430s (parsing complet + construction cache)
- **Démarrages suivants** : ~0.45s (chargement cache)
- **Accélération** : 960x plus rapide
- **Compression** : 50MB → ~8MB (80% de réduction)
- **Péages pré-matchés** : 272/1478 péages automatiquement liés

## Troubleshooting

### Cache Invalide

Si le cache devient invalide :
```python
# Force le rechargement
cache_manager.load_osm_data_with_cache(osm_file, force_reload=True)
```

### Problèmes de Compression

```python
# Utiliser compression plus simple
cache_manager.load_osm_data_with_cache(
    osm_file, 
    compression_type=CompressionType.GZIP
)
```

### Debug

```python
# Désactiver la compression pour debug
cache_manager.load_osm_data_with_cache(
    osm_file, 
    compression_type=CompressionType.NONE
)
```
