# ⚠️ Gestion d'Erreurs - Système de Péages

Ce module implémente un **système de gestion d'erreurs centralisé** pour l'optimisation des péages, avec classification intelligente et logging contextualisé.

## 🎯 Vue d'ensemble

Le `TollErrorHandler` centralise la gestion des erreurs spécifiques au domaine des péages en étendant le `BaseErrorHandler` commun avec des spécialisations métier.

### 🔄 Architecture de gestion d'erreurs
```
┌─────────────────────────────────────────────────┐
│              BASE ERROR HANDLER                 │  ← Gestion générique
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │ Logging Base    │  │ Formatage Commun    │   │
│  │ Performance     │  │ Messages Standards  │   │
│  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
                        │
                        ▼ Extends
┌─────────────────────────────────────────────────┐
│             TOLL ERROR HANDLER                  │  ← Spécialisations péages
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │ Erreurs ORS     │  │ Erreurs Contraintes │   │
│  │ Erreurs Calcul  │  │ Erreurs Validation  │   │
│  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## ⚠️ TollErrorHandler

### 🎯 Objectif
Gestionnaire centralisé spécialisé dans les erreurs d'optimisation des péages avec classification intelligente et contextualisation métier.

### 📋 Responsabilités
- **Classification d'erreurs** : Catégorisation selon le domaine métier
- **Conversion d'exceptions** : Transformation erreurs techniques en erreurs métier
- **Logging contextualisé** : Enrichissement avec contexte péages
- **Messages utilisateur** : Génération de messages clairs et exploitables
- **Tracking performance** : Suivi des erreurs pour optimisation

### 🔄 Méthodes principales
```python
class TollErrorHandler(BaseErrorHandler):
    @staticmethod
    def handle_ors_error(exception, operation_name)
    @staticmethod  
    def handle_constraint_violation(max_tolls, actual_tolls, context)
    @staticmethod
    def handle_route_calculation_error(coordinates, error_details)
    @staticmethod
    def handle_timeout_error(timeout_ms, operation_type)
    @staticmethod
    def handle_validation_error(validation_type, details)
```

---

## 🚨 Types d'Erreurs Gérées

### 🌐 Erreurs de Service ORS
**Catégorie** : Erreurs de communication avec le service de calcul d'itinéraire
```python
@staticmethod
def handle_ors_error(exception, operation_name="ORS_API_CALL"):
    """
    Gère les erreurs d'appel ORS et les convertit en exceptions métier.
    """
    error_mapping = {
        'timeout': ORSConnectionError("Timeout lors de l'appel ORS"),
        'connection': ORSConnectionError("Impossible de contacter le service ORS"),
        'rate_limit': ORSConnectionError("Limite de taux ORS dépassée"),
        'invalid_coordinates': RouteCalculationError("Coordonnées invalides"),
        'no_route_found': NoTollRouteError("Aucun itinéraire trouvé")
    }
    
    # Classification automatique selon le type d'erreur
    error_type = classify_ors_error(exception)
    specific_error = error_mapping.get(error_type, TollOptimizationError(str(exception)))
    
    # Logging avec contexte
    performance_tracker.log_error(operation_name, specific_error, {
        'original_exception': str(exception),
        'error_classification': error_type,
        'service': 'ORS'
    })
    
    return specific_error
```

### 🚫 Erreurs de Contraintes
**Catégorie** : Violations des contraintes de péages définies par l'utilisateur
```python
@staticmethod
def handle_constraint_violation(max_tolls, actual_tolls, context="general"):
    """
    Gère les violations de contraintes de péages.
    """
    violation_details = {
        'requested_max_tolls': max_tolls,
        'actual_toll_count': actual_tolls,
        'violation_amount': actual_tolls - max_tolls,
        'context': context
    }
    
    # Messages contextualisés
    if context == "no_toll_request":
        message = f"Impossible d'éviter tous les péages. {actual_tolls} péage(s) présent(s)."
        status = "SOME_TOLLS_PRESENT"
    elif context == "backup_exceeded":
        message = f"Contrainte backup dépassée: {actual_tolls} > {max_tolls + 1} péages."
        status = "BACKUP_CONSTRAINT_VIOLATION"
    else:
        message = f"Contrainte violée: {actual_tolls} > {max_tolls} péages maximum."
        status = "CONSTRAINT_VIOLATION"
    
    # Logging spécialisé
    OperationTracker.log_constraint_violation(
        operation="toll_constraint_check",
        details=violation_details
    )
    
    return {
        'error': True,
        'message': message,
        'status': status,
        'details': violation_details
    }
```

### 🛣️ Erreurs de Calcul d'Itinéraire
**Catégorie** : Problèmes lors du calcul des routes avec contraintes
```python
@staticmethod
def handle_route_calculation_error(coordinates, error_details, operation_context):
    """
    Gère les erreurs de calcul d'itinéraire spécifiques aux péages.
    """
    error_classification = {
        'invalid_coordinates': "Coordonnées de départ ou d'arrivée invalides",
        'no_route_possible': "Aucun itinéraire possible entre ces points",
        'avoidance_too_restrictive': "Contraintes d'évitement trop restrictives",
        'segmentation_failed': "Échec de la segmentation d'itinéraire",
        'toll_localization_failed': "Impossible de localiser les péages sur l'itinéraire"
    }
    
    error_type = error_details.get('type', 'unknown')
    user_message = error_classification.get(error_type, "Erreur de calcul d'itinéraire")
    
    # Contexte enrichi pour debugging
    context = {
        'coordinates': coordinates,
        'error_type': error_type,
        'operation_context': operation_context,
        'error_details': error_details,
        'timestamp': time.time()
    }
    
    # Performance tracking
    performance_tracker.log_operation_failure(
        operation="route_calculation",
        context=context
    )
    
    return RouteCalculationError(user_message, context)
```

### ⏱️ Erreurs de Timeout
**Catégorie** : Dépassements de temps de calcul configurés
```python
@staticmethod
def handle_timeout_error(timeout_ms, operation_type, context=None):
    """
    Gère les timeouts selon le type d'opération.
    """
    timeout_messages = {
        'constraint_resolution': f"Résolution des contraintes interrompue après {timeout_ms}ms",
        'segment_calculation': f"Calcul de segment interrompu après {timeout_ms}ms", 
        'route_optimization': f"Optimisation d'itinéraire interrompue après {timeout_ms}ms",
        'toll_localization': f"Localisation des péages interrompue après {timeout_ms}ms"
    }
    
    message = timeout_messages.get(operation_type, f"Opération interrompue après {timeout_ms}ms")
    
    # Suggestion d'actions correctives
    suggestions = {
        'constraint_resolution': "Essayez d'augmenter max_tolls ou réduire la complexité",
        'segment_calculation': "L'itinéraire peut être trop complexe pour la segmentation",
        'route_optimization': "Considérez un trajet plus direct ou moins de contraintes"
    }
    
    timeout_context = {
        'timeout_ms': timeout_ms,
        'operation_type': operation_type,
        'suggestion': suggestions.get(operation_type),
        'context': context
    }
    
    # Logging timeout avec analyse
    performance_tracker.log_timeout(operation_type, timeout_ms, timeout_context)
    
    return {
        'error': True,
        'type': 'timeout',
        'message': message,
        'suggestion': timeout_context['suggestion'],
        'status': 'COMPUTATION_TIMEOUT'
    }
```

---

## 📊 Classification et Logging

### 🔍 Classification automatique d'erreurs
```python
def classify_ors_error(exception):
    """
    Classifie automatiquement les erreurs ORS selon leurs caractéristiques.
    """
    error_str = str(exception).lower()
    
    # Patterns de classification
    if 'timeout' in error_str or 'timed out' in error_str:
        return 'timeout'
    elif 'connection' in error_str or 'unreachable' in error_str:
        return 'connection'
    elif 'rate limit' in error_str or '429' in error_str:
        return 'rate_limit'
    elif 'coordinates' in error_str or 'invalid location' in error_str:
        return 'invalid_coordinates'
    elif 'no route' in error_str or 'route not found' in error_str:
        return 'no_route_found'
    else:
        return 'unknown'
```

### 📈 Logging contextualisé
```python
@staticmethod
def log_operation_context(operation, success, details):
    """
    Logging enrichi avec contexte métier péages.
    """
    base_context = {
        'service': 'toll_optimization',
        'operation': operation,
        'success': success,
        'timestamp': time.time()
    }
    
    # Enrichissement selon le type d'opération
    if operation.startswith('constraint_'):
        base_context['domain'] = 'constraints'
        base_context['max_tolls'] = details.get('max_tolls')
        base_context['actual_tolls'] = details.get('actual_tolls')
    elif operation.startswith('route_'):
        base_context['domain'] = 'routing'
        base_context['coordinates_count'] = len(details.get('coordinates', []))
    elif operation.startswith('segment_'):
        base_context['domain'] = 'segmentation'
        base_context['segment_count'] = details.get('segment_count')
    
    # Logging selon le niveau
    if success:
        performance_tracker.log_operation_success(operation, base_context)
    else:
        performance_tracker.log_operation_failure(operation, base_context)
```

---

## 🔧 Configuration et Messages

### ⚙️ Configuration des erreurs
```python
class ErrorConfig:
    # Timeouts par opération
    CONSTRAINT_TIMEOUT_MS = 5000
    SEGMENT_TIMEOUT_MS = 2000
    ROUTE_TIMEOUT_MS = 8000
    
    # Retry policies
    ORS_MAX_RETRIES = 3
    ORS_RETRY_DELAY_MS = 1000
    
    # Logging levels
    ERROR_LOG_LEVEL = "ERROR"
    WARNING_LOG_LEVEL = "WARNING"
    INFO_LOG_LEVEL = "INFO"
    
    # Messages
    ENABLE_USER_FRIENDLY_MESSAGES = True
    INCLUDE_TECHNICAL_DETAILS = False  # En production
```

### 💬 Messages utilisateur
```python
class TollMessages:
    # Contraintes
    NO_TOLLS_POSSIBLE = "Impossible de calculer un itinéraire sans péage"
    TOO_MANY_TOLLS = "Trop de péages sur cet itinéraire ({actual} > {max})"
    BACKUP_SOLUTION = "Solution de secours utilisée ({tolls} péages)"
    
    # Service
    SERVICE_UNAVAILABLE = "Service de calcul d'itinéraire temporairement indisponible"
    CALCULATION_TIMEOUT = "Calcul d'itinéraire trop long, timeout dépassé"
    
    # Données
    INVALID_COORDINATES = "Coordonnées de départ ou d'arrivée invalides"
    NO_ROUTE_FOUND = "Aucun itinéraire trouvé entre ces points"
    
    # Suggestions
    INCREASE_MAX_TOLLS = "Essayez d'augmenter le nombre maximum de péages autorisés"
    USE_DIRECT_ROUTE = "Considérez un itinéraire plus direct"
    CHECK_COORDINATES = "Vérifiez que les coordonnées sont correctes"
```

---

## 📈 Métriques et Monitoring

### 📊 Tracking des erreurs
```python
class ErrorMetrics:
    def track_error_distribution():
        """Suit la distribution des types d'erreurs."""
        return {
            'ors_errors': count_by_type('ors'),
            'constraint_violations': count_by_type('constraint'),
            'timeouts': count_by_type('timeout'),
            'validation_errors': count_by_type('validation')
        }
    
    def calculate_error_rate():
        """Calcule le taux d'erreur global."""
        total_operations = get_total_operations()
        total_errors = get_total_errors()
        return (total_errors / total_operations) * 100 if total_operations > 0 else 0
    
    def get_most_frequent_errors():
        """Identifie les erreurs les plus fréquentes."""
        return get_error_frequency_ranking(limit=10)
```

### 🎯 Alertes et notifications
```python
class ErrorAlerting:
    def check_error_thresholds():
        """Vérifie les seuils d'alerte."""
        error_rate = ErrorMetrics.calculate_error_rate()
        
        if error_rate > 10:  # 10% d'erreur
            send_alert("HIGH_ERROR_RATE", {
                'current_rate': error_rate,
                'threshold': 10,
                'recent_errors': ErrorMetrics.get_most_frequent_errors()
            })
    
    def monitor_service_health():
        """Surveille la santé du service."""
        ors_error_rate = get_ors_error_rate()
        if ors_error_rate > 15:  # 15% d'erreur ORS
            send_alert("ORS_SERVICE_DEGRADED", {
                'ors_error_rate': ors_error_rate,
                'recommended_action': 'Check ORS service status'
            })
```

Le système de gestion d'erreurs offre une **approche robuste et intelligente** pour traiter les erreurs spécifiques au domaine des péages, avec **classification automatique**, **logging enrichi** et **monitoring proactif**.
