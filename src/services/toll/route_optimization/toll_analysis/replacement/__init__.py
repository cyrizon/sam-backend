"""
Toll Replacement Module
======================

Gestion du remplacement des péages fermés par des entrées d'autoroute optimales.
"""

from .entry_finder import EntryFinder
from .route_proximity_analyzer import RouteProximityAnalyzer
from .toll_replacement_engine import TollReplacementEngine

__all__ = [
    'EntryFinder',
    'RouteProximityAnalyzer', 
    'TollReplacementEngine'
]
