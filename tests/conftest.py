import sys
from pathlib import Path

# Ajoute le dossier parent (la racine du projet) au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))