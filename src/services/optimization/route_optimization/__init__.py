"""
Route Optimization Package
=========================

Package principal pour l'optimisation d'itinéraires avec péages.
Architecture simplifiée et modulaire pour une maintenance facile.
"""

# Imports corrigés après création complète
try:
    from .main.intelligent_optimizer import IntelligentOptimizer
    __all__ = ['IntelligentOptimizer']
except ImportError:
    __all__ = []
