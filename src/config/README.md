# ⚙️ Configuration - Gestion des Environnements

## 📋 Vue d'ensemble

Le système de configuration SAM gère les paramètres d'environnement pour le développement, les tests et la production. Il utilise une approche orientée classe avec des configurations spécialisées pour chaque environnement.

## 🏗️ Architecture

```
config/
├── config.py              # Gestionnaire principal de configuration
├── dev_config.py          # Configuration développement
├── production_config.py   # Configuration production
└── __init__.py
```

## 🎯 Objectifs du système

### **Séparation des environnements**
- 🔧 **Développement** : Configuration optimisée pour le debug et les tests
- 🚀 **Production** : Configuration sécurisée et performante
- 🧪 **Tests** : Configuration isolée pour les tests unitaires
- 🔄 **Basculement** : Changement d'environnement via variables

### **Flexibilité**
- 📊 **Variables d'environnement** : Support des .env et variables système
- 🔧 **Configuration dynamique** : Paramètres modifiables à l'exécution
- 🛡️ **Validation** : Contrôles de cohérence des paramètres
- 📝 **Documentation** : Paramètres documentés et typés

## 🧩 Composants détaillés

### **1. Config** - Gestionnaire Principal

Point d'entrée unique pour accéder aux configurations d'environnement.

#### **Structure**
```python
from src.config.config import Config

# Initialisation
config = Config()

# Accès aux configurations
dev_config = config.dev_config
prod_config = config.production_config

# Sélection automatique basée sur FLASK_ENV
import os
env = os.getenv("FLASK_ENV", "dev")
active_config = config.dev_config if env == "dev" else config.production_config
```

#### **Utilisation dans l'application**
```python
# Dans app.py ou __init__.py
from src.config.config import Config
import os

def create_app():
    app = Flask(__name__)
    
    # Chargement de la configuration selon l'environnement
    env = os.getenv("FLASK_ENV", "dev")
    config = Config()
    
    if env == "dev":
        app.config.from_object(config.dev_config)
        print("🔧 Mode développement activé")
    elif env == "production":
        app.config.from_object(config.production_config)
        print("🚀 Mode production activé")
    else:
        # Fallback sur développement
        app.config.from_object(config.dev_config)
        print(f"⚠️ Environnement '{env}' inconnu, fallback sur développement")
    
    return app
```

---

### **2. DevConfig** - Configuration Développement

Configuration optimisée pour le développement local avec debug activé.

#### **Paramètres actuels**
```python
class DevConfig:
    def __init__(self):
        self.ENV = "dev"
        self.DEBUG = True          # Debug Flask activé
        self.PORT = 5000          # Port de développement standard
        self.HOST = "0.0.0.0"     # Écoute sur toutes les interfaces
```

#### **Configuration étendue recommandée**
```python
import os
from dotenv import load_dotenv

load_dotenv()  # Charge le fichier .env

class DevConfig:
    def __init__(self):
        # Configuration de base
        self.ENV = "dev"
        self.DEBUG = True
        self.PORT = int(os.getenv("DEV_PORT", 5000))
        self.HOST = os.getenv("DEV_HOST", "0.0.0.0")
        
        # Configuration Flask
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
        self.TESTING = False
        
        # Configuration OpenRouteService
        self.ORS_BASE_URL = os.getenv("ORS_BASE_URL", "http://localhost:8082/ors")
        self.ORS_API_KEY = os.getenv("ORS_API_KEY", "")
        self.ORS_TIMEOUT = int(os.getenv("ORS_TIMEOUT", 30))
        
        # Configuration Cache
        self.CACHE_DIR = os.getenv("CACHE_DIR", "osm_cache_dev")
        self.DATA_DIR = os.getenv("DATA_DIR", "./data")
        self.ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        
        # Configuration CORS
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        
        # Configuration Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/sam-backend-dev.log")
        self.ENABLE_FILE_LOGGING = True
        
        # Configuration Rate Limiting
        self.RATE_LIMIT_ENABLED = False  # Désactivé en dev
        self.RATE_LIMIT_DEFAULT = "1000 per hour"
        
        # Configuration Performance
        self.ENABLE_PROFILING = True
        self.ENABLE_METRICS = True
        self.CACHE_PRELOAD = True
        
        # Configuration Database (si nécessaire)
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sam_dev.db")
        
        # Validation de la configuration
        self._validate_config()
    
    def _validate_config(self):
        """Valide la configuration de développement."""
        if not self.SECRET_KEY or self.SECRET_KEY == "dev-secret-key-change-me":
            print("⚠️ ATTENTION: Clé secrète par défaut utilisée en développement")
        
        if not self.ORS_BASE_URL:
            raise ValueError("❌ ORS_BASE_URL est requis")
        
        if not os.path.exists(self.DATA_DIR):
            print(f"⚠️ Répertoire de données manquant: {self.DATA_DIR}")
```

---

### **3. ProductionConfig** - Configuration Production

Configuration sécurisée et optimisée pour l'environnement de production.

#### **Paramètres actuels**
```python
class ProductionConfig:
    def __init__(self):
        self.ENV = "production"
        self.DEBUG = False         # Debug désactivé en production
        self.PORT = 5000          # Port standard
        self.HOST = "0.0.0.0"     # Écoute sur toutes les interfaces
```

#### **Configuration étendue recommandée**
```python
import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    def __init__(self):
        # Configuration de base
        self.ENV = "production"
        self.DEBUG = False
        self.PORT = int(os.getenv("PORT", 5000))
        self.HOST = os.getenv("HOST", "0.0.0.0")
        
        # Configuration Flask - SÉCURISÉE
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        if not self.SECRET_KEY:
            raise ValueError("❌ SECRET_KEY est obligatoire en production")
        
        self.TESTING = False
        
        # Configuration OpenRouteService
        self.ORS_BASE_URL = os.getenv("ORS_BASE_URL")
        self.ORS_API_KEY = os.getenv("ORS_API_KEY", "")
        self.ORS_TIMEOUT = int(os.getenv("ORS_TIMEOUT", 10))
        
        if not self.ORS_BASE_URL:
            raise ValueError("❌ ORS_BASE_URL est obligatoire en production")
        
        # Configuration Cache
        self.CACHE_DIR = os.getenv("CACHE_DIR", "osm_cache_prod")
        self.DATA_DIR = os.getenv("DATA_DIR", "/app/data")
        self.ENABLE_CACHE = True  # Toujours activé en production
        
        # Configuration CORS - RESTRICTIVE
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if cors_origins:
            self.CORS_ORIGINS = cors_origins.split(",")
        else:
            raise ValueError("❌ CORS_ORIGINS doit être défini en production")
        
        # Configuration Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "/var/log/sam-backend.log")
        self.ENABLE_FILE_LOGGING = True
        self.ENABLE_SYSLOG = os.getenv("ENABLE_SYSLOG", "false").lower() == "true"
        
        # Configuration Rate Limiting - ACTIVÉ
        self.RATE_LIMIT_ENABLED = True
        self.RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT", "100 per hour")
        self.RATE_LIMIT_STORAGE_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Configuration Performance
        self.ENABLE_PROFILING = False  # Désactivé en production
        self.ENABLE_METRICS = True
        self.CACHE_PRELOAD = True
        
        # Configuration Sécurité
        self.FORCE_HTTPS = os.getenv("FORCE_HTTPS", "true").lower() == "true"
        self.SESSION_COOKIE_SECURE = True
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = 'Lax'
        
        # Configuration Database
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        
        # Configuration Monitoring
        self.SENTRY_DSN = os.getenv("SENTRY_DSN", "")
        self.APM_SERVICE_NAME = "sam-backend"
        
        # Validation stricte
        self._validate_production_config()
    
    def _validate_production_config(self):
        """Validation stricte pour la production."""
        required_vars = [
            "SECRET_KEY", "ORS_BASE_URL", "CORS_ORIGINS"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(self, var.lower()) if hasattr(self, var.lower()) else not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"❌ Variables requises manquantes en production: {', '.join(missing_vars)}")
        
        # Validation de sécurité
        if self.DEBUG:
            raise ValueError("❌ DEBUG ne doit pas être activé en production")
        
        if "localhost" in str(self.CORS_ORIGINS):
            print("⚠️ ATTENTION: localhost détecté dans CORS_ORIGINS en production")
```

---

### **4. Configuration de Test**

Configuration spécialisée pour les tests unitaires et d'intégration.

#### **Création de TestConfig**
```python
# src/config/test_config.py
import os
import tempfile

class TestConfig:
    def __init__(self):
        # Configuration de base
        self.ENV = "test"
        self.DEBUG = False
        self.TESTING = True
        self.PORT = 5001  # Port différent pour éviter les conflits
        self.HOST = "127.0.0.1"
        
        # Configuration Flask pour tests
        self.SECRET_KEY = "test-secret-key"
        self.WTF_CSRF_ENABLED = False  # Désactiver CSRF pour les tests
        
        # Configuration OpenRouteService - MOCK
        self.ORS_BASE_URL = "http://mock-ors:8082/ors"
        self.ORS_API_KEY = "test-api-key"
        self.ORS_TIMEOUT = 5
        
        # Configuration Cache - TEMPORAIRE
        self.temp_dir = tempfile.mkdtemp()
        self.CACHE_DIR = os.path.join(self.temp_dir, "test_cache")
        self.DATA_DIR = os.path.join(self.temp_dir, "test_data")
        self.ENABLE_CACHE = True
        
        # Configuration CORS - PERMISSIVE
        self.CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
        
        # Configuration Logging - MINIMAL
        self.LOG_LEVEL = "ERROR"  # Logs minimum pendant les tests
        self.LOG_FILE = None
        self.ENABLE_FILE_LOGGING = False
        
        # Configuration Rate Limiting - DÉSACTIVÉ
        self.RATE_LIMIT_ENABLED = False
        
        # Configuration Performance - DÉSACTIVÉ
        self.ENABLE_PROFILING = False
        self.ENABLE_METRICS = False
        self.CACHE_PRELOAD = False
        
        # Configuration Database - EN MÉMOIRE
        self.DATABASE_URL = "sqlite:///:memory:"
        
        # Données de test
        self.TEST_DATA_SETUP = True
        self.MOCK_EXTERNAL_SERVICES = True
    
    def cleanup(self):
        """Nettoie les ressources temporaires."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
```

## 🔧 Configuration avancée

### **Variables d'environnement**

#### **Fichier .env de développement**
```bash
# .env (développement)
FLASK_ENV=dev
SECRET_KEY=your-dev-secret-key
DEBUG=true

# OpenRouteService
ORS_BASE_URL=http://localhost:8082/ors
ORS_API_KEY=your-ors-api-key
ORS_TIMEOUT=30

# Cache et données
CACHE_DIR=osm_cache_dev
DATA_DIR=./data
ENABLE_CACHE=true

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/sam-backend-dev.log

# Performance
ENABLE_PROFILING=true
ENABLE_METRICS=true
```

#### **Variables de production**
```bash
# Variables d'environnement production
FLASK_ENV=production
SECRET_KEY=your-super-secure-production-key
DEBUG=false

# OpenRouteService
ORS_BASE_URL=https://your-ors-instance.com/ors
ORS_API_KEY=your-production-ors-key
ORS_TIMEOUT=10

# Cache
CACHE_DIR=/app/cache
DATA_DIR=/app/data

# CORS
CORS_ORIGINS=https://your-frontend.com,https://app.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/sam-backend.log
ENABLE_SYSLOG=true

# Rate Limiting
RATE_LIMIT=100 per hour
REDIS_URL=redis://redis:6379

# Sécurité
FORCE_HTTPS=true

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### **Configuration conditionnelle**
```python
# Configuration avec conditions
class SmartConfig:
    def __init__(self):
        self.env = os.getenv("FLASK_ENV", "dev")
        
        # Configuration de base commune
        self._setup_base_config()
        
        # Configuration spécifique à l'environnement
        if self.env == "dev":
            self._setup_dev_config()
        elif self.env == "production":
            self._setup_production_config()
        elif self.env == "test":
            self._setup_test_config()
        else:
            raise ValueError(f"Environnement inconnu: {self.env}")
        
        # Post-configuration
        self._post_setup()
    
    def _setup_base_config(self):
        """Configuration commune à tous les environnements."""
        self.APP_NAME = "SAM Backend"
        self.VERSION = "2.1.0"
        self.API_VERSION = "v1"
        
    def _setup_dev_config(self):
        """Configuration développement."""
        self.DEBUG = True
        self.LOG_LEVEL = "DEBUG"
        
    def _setup_production_config(self):
        """Configuration production."""
        self.DEBUG = False
        self.LOG_LEVEL = "INFO"
        
    def _post_setup(self):
        """Configuration post-initialisation."""
        self._validate_config()
        self._setup_logging()
        
    def _validate_config(self):
        """Validation de la configuration."""
        if self.env == "production" and self.DEBUG:
            raise ValueError("DEBUG ne peut pas être True en production")
```

### **Configuration avec classes héritées**
```python
# Configuration avec héritage
class BaseConfig:
    """Configuration de base partagée."""
    APP_NAME = "SAM Backend"
    VERSION = "2.1.0"
    
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY", self.default_secret_key())
        self.ORS_BASE_URL = os.getenv("ORS_BASE_URL")
        self.DATA_DIR = os.getenv("DATA_DIR", "./data")
    
    def default_secret_key(self):
        """Clé secrète par défaut selon l'environnement."""
        return "change-me-in-production"

class DevConfig(BaseConfig):
    """Configuration développement."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    RATE_LIMIT_ENABLED = False
    
    def default_secret_key(self):
        return "dev-secret-key"

class ProductionConfig(BaseConfig):
    """Configuration production."""
    DEBUG = False
    LOG_LEVEL = "INFO"
    RATE_LIMIT_ENABLED = True
    
    def default_secret_key(self):
        raise ValueError("SECRET_KEY doit être définie en production")
```

## 🛠️ Utilisation pratique

### **Intégration avec Flask**
```python
# app.py
from flask import Flask
from src.config.config import Config
import os

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Détermination de la configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "dev")
    
    # Chargement de la configuration
    config = Config()
    
    if config_name == "dev":
        app.config.from_object(config.dev_config)
    elif config_name == "production":
        app.config.from_object(config.production_config)
    elif config_name == "test":
        app.config.from_object(config.test_config)
    
    # Configuration des composants
    setup_logging(app)
    setup_cors(app)
    setup_rate_limiting(app)
    
    return app

def setup_logging(app):
    """Configure le logging selon l'environnement."""
    import logging
    
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"))
    logging.basicConfig(level=level)
    
    if app.config.get("ENABLE_FILE_LOGGING"):
        file_handler = logging.FileHandler(app.config["LOG_FILE"])
        file_handler.setLevel(level)
        app.logger.addHandler(file_handler)

def setup_cors(app):
    """Configure CORS selon l'environnement."""
    from flask_cors import CORS
    
    origins = app.config.get("CORS_ORIGINS", [])
    CORS(app, origins=origins)

def setup_rate_limiting(app):
    """Configure le rate limiting si activé."""
    if app.config.get("RATE_LIMIT_ENABLED"):
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=[app.config.get("RATE_LIMIT_DEFAULT", "100 per hour")]
        )
```

### **Accès à la configuration dans l'application**
```python
# Dans vos routes ou services
from flask import current_app

def some_function():
    # Accès à la configuration
    ors_url = current_app.config["ORS_BASE_URL"]
    cache_dir = current_app.config["CACHE_DIR"]
    debug_mode = current_app.config["DEBUG"]
    
    if debug_mode:
        print(f"🔧 Mode debug - ORS: {ors_url}")
```

### **Configuration pour Docker**
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Variables d'environnement par défaut
ENV FLASK_ENV=production
ENV PORT=5000
ENV HOST=0.0.0.0

# Configuration spécifique production
ENV DEBUG=false
ENV ENABLE_CACHE=true
ENV LOG_LEVEL=INFO

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  sam-backend:
    build: .
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - ORS_BASE_URL=${ORS_BASE_URL}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - LOG_LEVEL=INFO
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/var/log
```
