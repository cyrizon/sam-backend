"""
Link Types Enumeration
---------------------

Defines the types of motorway links.
"""

from enum import Enum


class LinkType(Enum):
    """Type de lien motorway_link."""
    ENTRY = "entry"           # Bretelle d'entrée
    EXIT = "exit"             # Bretelle de sortie  
    INDETERMINATE = "indeterminate"  # Type indéterminé (à classifier)
    CONNECTOR = "connector"   # Lien de connexion (classifié depuis indeterminate)
