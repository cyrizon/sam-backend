"""
test_linking.py
--------------

Script de test pour valider le linking des motorway_junctions et motorway_links.
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.cache.parsers.osm_parser import OSMParser


def test_linking():
    """Test le linking des éléments OSM."""
    print("🚀 Test du linking des éléments OSM...")

    # Chemin vers le fichier GeoJSON (racine du projet + data)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    print(project_root)
    geojson_path = os.path.join(project_root, "data", "osm_export_toll.geojson")

    print(f"📁 Chargement du fichier : {geojson_path}")

    if not os.path.exists(geojson_path):
        print(f"❌ Fichier GeoJSON non trouvé : {geojson_path}")
        return

    # Créer le parser et charger les données
    parser = OSMParser(geojson_path)

    print("⏳ Chargement et parsing en cours...")
    success = parser.load_and_parse()

    if success:
        print("✅ Test de linking terminé avec succès!")
    else:
        print("❌ Échec du test de linking")


if __name__ == "__main__":
    test_linking()
