# 🧠 Smart Toll Cache - Cache Intelligent des Péages

Ce module implémente un **système de cache intelligent** spécialement conçu pour optimiser les calculs de coûts de péages tout en respectant la logique complexe des systèmes de péage français.

## 🎯 Vue d'ensemble

Le SmartTollCache comprend et respecte la **logique des péages fermés** où le coût dépend de la séquence complète des péages traversés, contrairement aux péages ouverts à tarif fixe.

### 🔄 Principe de fonctionnement
- **Cache de séquences** : Stockage des séquences complètes de péages avec coûts réels
- **Logique différenciée** : Traitement spécialisé péages ouverts vs fermés
- **Optimisation intelligente** : Évite les recalculs inutiles
- **TTL adaptatif** : Durée de vie configurable des données en cache
- **Thread-safe** : Accès concurrent sécurisé

---

## 🧠 SmartTollCache

### 🎯 Objectif
Optimiser les performances de calcul des coûts de péages en cachant intelligemment les séquences de péages avec leurs coûts réels.

### 📋 Responsabilités
- **Cache de séquences** : Stockage des combinaisons de péages calculées
- **Différenciation système** : Traitement spécialisé ouverts/fermés
- **Gestion TTL** : Expiration automatique des données obsolètes
- **Optimisation performance** : Réduction significative des recalculs
- **Thread safety** : Accès concurrent sécurisé

### 🔄 Fonctionnalités principales
```python
class SmartTollCache:
    def __init__(max_size=500, ttl_seconds=3600)
    def get_sequence_cost(toll_sequence, vehicle_type="light")
    def cache_sequence_cost(toll_sequence, cost, vehicle_type="light")
    def invalidate_expired_entries()
    def clear_cache()
    def get_cache_stats()
```

---

## 🎯 Logique des Systèmes de Péage

### 🔓 Péages Ouverts (Système Ouvert)
**Caractéristiques** : Tarif fixe payé à l'entrée, indépendant de la sortie
```python
# Exemples : A1, A4, A13, A14, A15, A16
open_system_tolls = ["A1_SENLIS", "A4_MEAUX", "A13_NORMANDIE"]

# Coût fixe par péage
cost_per_toll = {
    "A1_SENLIS": 2.80,      # Prix fixe
    "A4_MEAUX": 3.20,       # Prix fixe  
    "A13_NORMANDIE": 4.50   # Prix fixe
}

# Coût total = somme des coûts individuels
total_cost = sum(toll_costs)  # Simple addition
```

### 🔒 Péages Fermés (Système Fermé)
**Caractéristiques** : Tarif selon distance parcourue entre entrée et sortie
```python
# Exemples : A6, A7, A8, A9, A10, A11
closed_system_tolls = ["A6_FLEURY", "A6_AUXERRE", "A6_CHALON"]

# Coût selon séquence complète
sequence_cost = calculate_closed_system_cost([
    ("A6_FLEURY", "entry"),
    ("A6_AUXERRE", "intermediate"), 
    ("A6_CHALON", "exit")
])

# Le coût total n'est PAS la somme des coûts individuels
# Il dépend de la distance totale parcourue sur le réseau
```

---

## 🔧 Algorithmes de Cache

### 🔑 Génération de clés de cache
```python
def generate_cache_key(toll_sequence, vehicle_type):
    """
    Génère une clé unique pour une séquence de péages.
    Inclut l'ordre des péages car il affecte le coût total.
    """
    # Normalisation de la séquence
    normalized_sequence = [
        f"{toll['id']}:{toll['type']}" for toll in toll_sequence
    ]
    
    # Création d'une signature unique
    sequence_string = f"{vehicle_type}:{':'.join(normalized_sequence)}"
    cache_key = hashlib.md5(sequence_string.encode()).hexdigest()
    
    return cache_key
```

### 💾 Stratégie de mise en cache
```python
def cache_sequence_cost(self, toll_sequence, cost, vehicle_type="light"):
    """
    Met en cache le coût d'une séquence de péages avec métadonnées.
    """
    cache_key = self.generate_cache_key(toll_sequence, vehicle_type)
    
    cache_entry = {
        'cost': cost,
        'vehicle_type': vehicle_type,
        'timestamp': time.time(),
        'sequence_length': len(toll_sequence),
        'systems': self.analyze_toll_systems(toll_sequence)
    }
    
    with self._lock:
        # Éviction LRU si cache plein
        if len(self._cache) >= self._max_size:
            self._evict_lru_entry()
            
        self._cache[cache_key] = cache_entry
        self._access_times[cache_key] = time.time()
```

### 🔍 Récupération intelligente
```python
def get_sequence_cost(self, toll_sequence, vehicle_type="light"):
    """
    Récupère le coût d'une séquence depuis le cache avec validation.
    """
    cache_key = self.generate_cache_key(toll_sequence, vehicle_type)
    
    with self._lock:
        if cache_key not in self._cache:
            return None
            
        entry = self._cache[cache_key]
        
        # Vérification TTL
        if self._is_expired(entry):
            del self._cache[cache_key]
            del self._access_times[cache_key]
            return None
            
        # Mise à jour access time pour LRU
        self._access_times[cache_key] = time.time()
        
        return entry['cost']
```

---

## 📊 Gestion de la Performance

### ⏱️ TTL (Time To Live) Adaptatif
```python
def _is_expired(self, cache_entry):
    """
    Vérification d'expiration avec TTL adaptatif selon le type de données.
    """
    current_time = time.time()
    entry_age = current_time - cache_entry['timestamp']
    
    # TTL adaptatif selon complexité de la séquence
    if cache_entry['sequence_length'] > 5:
        # Séquences complexes : TTL plus long (2h)
        ttl = self._ttl_seconds * 2
    elif 'closed_system' in cache_entry['systems']:
        # Péages fermés : TTL standard (1h)  
        ttl = self._ttl_seconds
    else:
        # Péages ouverts : TTL plus court (30min)
        ttl = self._ttl_seconds // 2
        
    return entry_age > ttl
```

### 🗑️ Éviction LRU (Least Recently Used)
```python
def _evict_lru_entry(self):
    """
    Éviction de l'entrée la moins récemment utilisée.
    """
    if not self._access_times:
        return
        
    # Trouve l'entrée avec le plus ancien access_time
    lru_key = min(self._access_times.keys(), 
                  key=lambda k: self._access_times[k])
    
    # Suppression
    del self._cache[lru_key]
    del self._access_times[lru_key]
    
    self._stats['evictions'] += 1
```

### 📈 Statistiques de performance
```python
def get_cache_stats(self):
    """
    Retourne des statistiques détaillées du cache.
    """
    total_requests = self._stats['hits'] + self._stats['misses']
    hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
    
    return {
        'size': len(self._cache),
        'max_size': self._max_size,
        'hits': self._stats['hits'],
        'misses': self._stats['misses'],
        'hit_rate': f"{hit_rate:.2%}",
        'evictions': self._stats['evictions'],
        'expired_cleanups': self._stats['expired_cleanups'],
        'avg_sequence_length': self._calculate_avg_sequence_length(),
        'cache_efficiency': self._calculate_cache_efficiency()
    }
```

---

## 🧪 Analyse des Systèmes de Péage

### 🔍 Identification automatique
```python
def analyze_toll_systems(self, toll_sequence):
    """
    Analyse une séquence pour identifier les types de systèmes présents.
    """
    systems = {
        'open_system': [],
        'closed_system': [],
        'mixed': False
    }
    
    for toll in toll_sequence:
        if is_toll_open_system(toll['id']):
            systems['open_system'].append(toll['id'])
        else:
            systems['closed_system'].append(toll['id'])
    
    # Détection système mixte
    if systems['open_system'] and systems['closed_system']:
        systems['mixed'] = True
        
    return systems
```

### 📊 Optimisations spécialisées
```python
def should_cache_sequence(self, toll_sequence, computation_time_ms):
    """
    Détermine si une séquence mérite d'être mise en cache.
    """
    # Toujours cacher les séquences coûteuses en calcul
    if computation_time_ms > 500:  # 500ms
        return True
        
    # Cacher les séquences de péages fermés (calcul complexe)
    systems = self.analyze_toll_systems(toll_sequence)
    if systems['closed_system'] or systems['mixed']:
        return True
        
    # Cacher les longues séquences (>3 péages)
    if len(toll_sequence) > 3:
        return True
        
    # Péages ouverts simples : cache optionnel
    return len(toll_sequence) > 1
```

---

## 🔧 Configuration et Utilisation

### ⚙️ Configuration recommandée
```python
# Configuration production
production_cache = SmartTollCache(
    max_size=1000,          # 1000 séquences max
    ttl_seconds=3600        # 1 heure TTL
)

# Configuration développement  
dev_cache = SmartTollCache(
    max_size=100,           # Cache plus petit
    ttl_seconds=1800        # 30 minutes TTL
)

# Configuration test
test_cache = SmartTollCache(
    max_size=50,            # Cache minimal
    ttl_seconds=300         # 5 minutes TTL
)
```

### 🚀 Utilisation dans le système
```python
# Intégration avec le calculateur de coûts
class TollCostCalculator:
    def __init__(self, cache=None):
        self.cache = cache or SmartTollCache()
        
    def calculate_sequence_cost(self, toll_sequence, vehicle_type="light"):
        # Tentative de récupération depuis cache
        cached_cost = self.cache.get_sequence_cost(toll_sequence, vehicle_type)
        if cached_cost is not None:
            return cached_cost
            
        # Calcul réel si non trouvé en cache
        start_time = time.time()
        actual_cost = self._compute_actual_cost(toll_sequence, vehicle_type)
        computation_time = (time.time() - start_time) * 1000
        
        # Mise en cache si pertinent
        if self.cache.should_cache_sequence(toll_sequence, computation_time):
            self.cache.cache_sequence_cost(toll_sequence, actual_cost, vehicle_type)
            
        return actual_cost
```

---

## 📈 Métriques et Monitoring

### 📊 Indicateurs de performance
- **Taux de hit** : Pourcentage de requêtes servies par le cache
- **Temps de réponse moyen** : Cache vs calcul réel
- **Efficacité mémoire** : Ratio utilité/espace utilisé
- **Taux d'éviction** : Fréquence de remplacement des entrées

### 🎯 Objectifs de performance
- **Hit rate** : > 70% pour les séquences complexes
- **Réduction temps** : -85% vs calcul complet
- **Utilisation mémoire** : < 100MB en production
- **TTL optimal** : Équilibre fraîcheur/performance

Le SmartTollCache offre une **optimisation intelligente** des calculs de péages en respectant la **complexité inhérente** des systèmes de péage français, avec un **impact significatif sur les performances** du système global.
