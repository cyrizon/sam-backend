"""
Module d'optimisation des sorties d'autoroute.

Fournit des outils pour remplacer intelligemment les péages d'entrée
par des sorties d'autoroute optimales afin d'éviter les bugs de navigation.
"""

from .exit_optimization_manager import ExitOptimizationManager
from .motorway_exit_finder import MotorwayExitFinder
from .exit_toll_detector import ExitTollDetector

__all__ = [
    'ExitOptimizationManager',
    'MotorwayExitFinder', 
    'ExitTollDetector'
]
