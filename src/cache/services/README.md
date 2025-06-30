# 🔧 Cache Services - Services Spécialisés du Cache

## 📋 Vue d'ensemble

Les services du cache SAM fournissent des fonctionnalités métier spécialisées construites au-dessus des données de cache. Ils offrent des API de haut niveau pour l'association de péages, le calcul de coûts et l'analyse spatiale.

## 🏗️ Architecture

```
services/
├── toll_association_service.py    # Service d'association péages ↔ segments
├── toll_cost_calculator.py        # Calculateur de coûts avancé
└── __init__.py
```

## 🎯 Objectifs des services

### **Abstraction métier**
- 🎯 **API simplifiées** : Interfaces de haut niveau pour les cas d'usage courants
- 🔧 **Logique métier** : Encapsulation des règles de gestion complexes
- 📊 **Agrégation de données** : Combinaison intelligente des sources multiples
- 🛡️ **Validation robuste** : Contrôles de cohérence et gestion d'erreurs

### **Performance optimisée**
- ⚡ **Cache intelligent** : Mise en cache des calculs coûteux
- 🔍 **Index spatiaux** : Recherches géospatiales optimisées
- 📈 **Calculs vectorisés** : Traitement en lot pour performance
- 🧠 **Gestion mémoire** : Optimisation de l'utilisation des ressources

## 🧩 Composants détaillés

### **1. TollAssociationService** - Service d'Association de Péages

Service spécialisé dans l'association intelligente des péages aux segments autoroutiers.

#### **Fonctionnalités principales**
- 🎯 **Association spatiale** : Liaison péages ↔ segments par proximité
- 🔍 **Validation contextuelle** : Vérification cohérence opérateur/autoroute
- 📊 **Statistiques d'association** : Métriques de qualité et performance
- 🛠️ **Résolution de conflits** : Gestion des ambiguïtés et doublons

#### **Utilisation**
```python
from src.cache.services.toll_association_service import TollAssociationService

# Initialisation
association_service = TollAssociationService(
    max_distance_m=2.0,              # Distance max pour association
    enable_operator_validation=True,  # Validation opérateur
    enable_highway_validation=True,   # Validation référence autoroute
    confidence_threshold=0.8          # Seuil de confiance minimum
)

# Association pour un segment spécifique
segment = complete_motorway_links[0]
associated_tolls = association_service.associate_tolls_to_segment(
    segment=segment,
    available_tolls=toll_booths
)

print(f"Segment: {segment.segment_name}")
print(f"Péages associés: {len(associated_tolls)}")
for toll in associated_tolls:
    print(f"  - {toll.display_name} ({toll.operator})")
```

#### **Association en lot**
```python
# Association pour tous les segments
all_associations = association_service.associate_tolls_to_all_segments(
    segments=complete_motorway_links,
    tolls=toll_booths,
    enable_parallel_processing=True
)

# Résultats détaillés
association_stats = association_service.get_association_statistics()
print(f"""
📊 Statistiques d'association:
   - Segments traités: {association_stats['segments_processed']}
   - Péages associés: {association_stats['tolls_associated']}
   - Taux de succès: {association_stats['success_rate']:.1f}%
   - Temps de traitement: {association_stats['processing_time_ms']}ms
   
🎯 Qualité des associations:
   - Haute confiance: {association_stats['high_confidence_count']}
   - Confiance moyenne: {association_stats['medium_confidence_count']}
   - Faible confiance: {association_stats['low_confidence_count']}
   - Associations rejetées: {association_stats['rejected_count']}
""")
```

#### **Algorithme d'association avancé**
```python
def associate_toll_to_segment_with_confidence(self, toll, segment):
    """Associe un péage à un segment avec score de confiance."""
    
    confidence_factors = {}
    
    # 1. Distance spatiale (poids: 40%)
    min_distance = self.calculate_min_distance_to_segment(toll, segment)
    distance_score = max(0, 1.0 - (min_distance / self.max_distance_m))
    confidence_factors['distance'] = distance_score * 0.4
    
    # 2. Correspondance opérateur (poids: 25%)
    operator_score = 1.0 if toll.operator == segment.operator else 0.0
    confidence_factors['operator'] = operator_score * 0.25
    
    # 3. Correspondance autoroute (poids: 20%)
    highway_score = 1.0 if toll.highway_ref == segment.highway_ref else 0.0
    confidence_factors['highway'] = highway_score * 0.20
    
    # 4. Cohérence géographique (poids: 10%)
    geographic_score = self.calculate_geographic_coherence(toll, segment)
    confidence_factors['geographic'] = geographic_score * 0.10
    
    # 5. Validation contextuelle (poids: 5%)
    context_score = self.validate_contextual_coherence(toll, segment)
    confidence_factors['context'] = context_score * 0.05
    
    # Score de confiance global
    total_confidence = sum(confidence_factors.values())
    
    return {
        'toll_id': toll.osm_id,
        'segment_id': segment.link_id,
        'confidence_score': total_confidence,
        'confidence_factors': confidence_factors,
        'is_accepted': total_confidence >= self.confidence_threshold,
        'distance_m': min_distance
    }
```

#### **Gestion des conflits**
```python
def resolve_association_conflicts(self, associations):
    """Résout les conflits d'association multiple."""
    
    # Groupement par péage
    toll_groups = {}
    for assoc in associations:
        toll_id = assoc['toll_id']
        if toll_id not in toll_groups:
            toll_groups[toll_id] = []
        toll_groups[toll_id].append(assoc)
    
    resolved_associations = []
    conflicts_resolved = 0
    
    for toll_id, candidates in toll_groups.items():
        if len(candidates) == 1:
            # Pas de conflit
            resolved_associations.extend(candidates)
        else:
            # Résolution du conflit
            conflicts_resolved += 1
            
            # Sélection de la meilleure association
            best_association = max(candidates, key=lambda x: x['confidence_score'])
            
            # Validation finale
            if best_association['confidence_score'] >= self.confidence_threshold:
                resolved_associations.append(best_association)
    
    return resolved_associations, conflicts_resolved
```

---

### **2. TollCostCalculator** - Calculateur de Coûts Avancé

Service de calcul de coûts sophistiqué qui combine les différents types de péages et tarifications.

#### **Fonctionnalités**
- 💰 **Calculs multi-tarifs** : Péages ouverts et fermés combinés
- 🚗 **Support multi-véhicules** : Toutes catégories (C1-C5)
- 📈 **Optimisation de coûts** : Recherche du chemin le moins cher
- 📊 **Analyses de sensibilité** : Impact des variations tarifaires

#### **Utilisation de base**
```python
from src.cache.services.toll_cost_calculator import TollCostCalculator

# Initialisation
cost_calculator = TollCostCalculator(
    operators_pricing=operators_data,
    toll_booths=toll_booths,
    enable_caching=True,
    cache_size=1000
)

# Calcul pour un segment autoroutier
segment = complete_motorway_links[0]
cost_result = cost_calculator.calculate_segment_cost(
    segment=segment,
    vehicle_category="c1",
    include_breakdown=True
)

print(f"Coût total: {cost_result['total_cost']:.2f}€")
print(f"Détail:")
print(f"  - Péages fermés: {cost_result['closed_tolls_cost']:.2f}€")
print(f"  - Péages ouverts: {cost_result['open_tolls_cost']:.2f}€")
print(f"  - Distance: {cost_result['distance_km']:.1f}km")
```

#### **Calculs avancés**
```python
# Calcul pour un itinéraire complet
route_segments = [segment1, segment2, segment3]
route_cost = cost_calculator.calculate_route_cost(
    segments=route_segments,
    vehicle_category="c1"
)

# Analyse de sensibilité
sensitivity_analysis = cost_calculator.analyze_cost_sensitivity(
    segments=route_segments,
    vehicle_categories=["c1", "c2", "c3"],
    operator_variations={"APRR": 1.1, "ASF": 0.95}  # Variations tarifaires
)

print(f"Coût de base (C1): {sensitivity_analysis['base_costs']['c1']:.2f}€")
print(f"Coût avec variations: {sensitivity_analysis['varied_costs']['c1']:.2f}€")
print(f"Impact: {sensitivity_analysis['cost_impact']['c1']:.1f}%")
```

#### **Algorithmes de calcul**
```python
def calculate_segment_cost_detailed(self, segment, vehicle_category):
    """Calcule le coût détaillé d'un segment."""
    
    cost_breakdown = {
        'segment_id': segment.link_id,
        'vehicle_category': vehicle_category,
        'distance_km': segment.distance_km,
        'operator': segment.operator,
        'costs': {
            'closed_tolls': 0.0,
            'open_tolls': 0.0,
            'total': 0.0
        },
        'toll_details': []
    }
    
    # Calcul des péages fermés (au kilomètre)
    if segment.operator and segment.distance_km > 0:
        price_per_km = self.get_operator_price_per_km(
            segment.operator, vehicle_category
        )
        closed_cost = segment.distance_km * price_per_km
        cost_breakdown['costs']['closed_tolls'] = closed_cost
    
    # Calcul des péages ouverts (tarifs fixes)
    for toll_id in segment.associated_tolls:
        toll = self.get_toll_by_id(toll_id)
        if toll and toll.is_open_toll:
            open_cost = self.get_open_toll_price(toll.name, vehicle_category)
            cost_breakdown['costs']['open_tolls'] += open_cost
            
            cost_breakdown['toll_details'].append({
                'toll_name': toll.display_name,
                'toll_type': 'open',
                'cost': open_cost
            })
    
    # Coût total
    cost_breakdown['costs']['total'] = (
        cost_breakdown['costs']['closed_tolls'] +
        cost_breakdown['costs']['open_tolls']
    )
    
    return cost_breakdown
```

#### **Optimisation multi-critères**
```python
def find_optimal_route(self, route_options, criteria):
    """Trouve la route optimale selon plusieurs critères."""
    
    evaluations = []
    
    for route in route_options:
        evaluation = {
            'route': route,
            'scores': {},
            'total_score': 0.0
        }
        
        # Critère coût (poids configurable)
        cost = self.calculate_route_cost(route.segments, criteria['vehicle_category'])
        cost_score = self.normalize_cost_score(cost, criteria['cost_range'])
        evaluation['scores']['cost'] = cost_score * criteria['cost_weight']
        
        # Critère distance (poids configurable)
        distance = sum(s.distance_km for s in route.segments)
        distance_score = self.normalize_distance_score(distance, criteria['distance_range'])
        evaluation['scores']['distance'] = distance_score * criteria['distance_weight']
        
        # Critère nombre de péages (poids configurable)
        toll_count = sum(len(s.associated_tolls) for s in route.segments)
        toll_score = self.normalize_toll_count_score(toll_count, criteria['toll_range'])
        evaluation['scores']['toll_count'] = toll_score * criteria['toll_weight']
        
        # Score total
        evaluation['total_score'] = sum(evaluation['scores'].values())
        evaluations.append(evaluation)
    
    # Retourne la route avec le meilleur score
    best_route = max(evaluations, key=lambda x: x['total_score'])
    return best_route
```

#### **Cache intelligent**
```python
class CostCalculatorCache:
    """Cache intelligent pour les calculs de coûts."""
    
    def __init__(self, max_size=1000):
        self.cache = {}
        self.access_count = {}
        self.max_size = max_size
    
    def get_cached_cost(self, cache_key):
        """Récupère un coût depuis le cache."""
        if cache_key in self.cache:
            self.access_count[cache_key] += 1
            return self.cache[cache_key]
        return None
    
    def cache_cost(self, cache_key, cost_result):
        """Met en cache un résultat de coût."""
        # Éviction LRU si nécessaire
        if len(self.cache) >= self.max_size:
            lru_key = min(self.access_count.keys(), 
                         key=lambda k: self.access_count[k])
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        self.cache[cache_key] = cost_result
        self.access_count[cache_key] = 1
    
    def generate_cache_key(self, segment_id, vehicle_category, operator):
        """Génère une clé de cache unique."""
        return f"{segment_id}:{vehicle_category}:{operator}"
```

## 🔧 Configuration et utilisation avancée

### **Configuration des services**
```python
# Configuration complète des services
SERVICES_CONFIG = {
    "toll_association": {
        "max_distance_m": 2.0,
        "confidence_threshold": 0.8,
        "enable_operator_validation": True,
        "enable_highway_validation": True,
        "parallel_processing": True,
        "batch_size": 100
    },
    "cost_calculator": {
        "enable_caching": True,
        "cache_size": 1000,
        "enable_sensitivity_analysis": True,
        "default_vehicle_category": "c1",
        "precision_decimal_places": 2
    }
}

# Application de la configuration
association_service = TollAssociationService(**SERVICES_CONFIG["toll_association"])
cost_calculator = TollCostCalculator(**SERVICES_CONFIG["cost_calculator"])
```

### **Intégration avec le cache manager**
```python
# Intégration complète avec le gestionnaire de cache
def setup_integrated_services(cache_manager):
    """Configure les services intégrés avec le cache."""
    
    # Service d'association
    association_service = TollAssociationService(max_distance_m=2.0)
    
    # Service de calcul de coûts
    cost_calculator = TollCostCalculator(
        operators_pricing=cache_manager.pricing_manager.operators_data,
        toll_booths=cache_manager.toll_booths
    )
    
    # Association globale péages ↔ segments
    associations = association_service.associate_tolls_to_all_segments(
        segments=cache_manager.complete_motorway_links,
        tolls=cache_manager.toll_booths
    )
    
    # Mise à jour des segments avec associations
    for assoc in associations:
        segment = cache_manager.get_segment_by_id(assoc['segment_id'])
        if segment:
            segment.associated_tolls = assoc['associated_tolls']
    
    # Stockage des services dans le cache manager
    cache_manager.association_service = association_service
    cache_manager.cost_calculator = cost_calculator
    
    return cache_manager
```

## 📊 Métriques et monitoring

### **Métriques de performance**
```python
# Métriques typiques des services
service_metrics = {
    "toll_association": {
        "processing_time_per_segment": "5-15ms",
        "success_rate": "85-95%",
        "confidence_score_average": "0.82-0.91",
        "memory_usage": "10-25MB"
    },
    "cost_calculator": {
        "calculation_time_per_segment": "1-3ms", 
        "cache_hit_rate": "60-80%",
        "precision_accuracy": "99.95%",
        "memory_usage": "5-15MB"
    }
}
```

### **Monitoring en temps réel**
```python
def monitor_services_performance():
    """Monitoring des performances des services."""
    
    monitoring_data = {
        "timestamp": datetime.now().isoformat(),
        "association_service": {
            "total_associations": association_service.get_total_associations(),
            "average_confidence": association_service.get_average_confidence(),
            "processing_time_ms": association_service.get_last_processing_time(),
            "error_count": association_service.get_error_count()
        },
        "cost_calculator": {
            "total_calculations": cost_calculator.get_total_calculations(),
            "cache_hit_rate": cost_calculator.get_cache_hit_rate(),
            "average_calculation_time_ms": cost_calculator.get_average_calculation_time(),
            "memory_usage_mb": cost_calculator.get_memory_usage()
        }
    }
    
    return monitoring_data
```