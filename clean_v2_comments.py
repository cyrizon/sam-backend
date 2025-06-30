#!/usr/bin/env python3
"""
Script de nettoyage final - suppression des dernières références v2 dans les commentaires et noms de fichiers
"""

import os
import re
from pathlib import Path


def clean_v2_references_in_comments():
    """Nettoyer les références v2 dans les commentaires et docstrings"""
    print("🧹 Nettoyage des références v2 dans les commentaires...")
    
    replacements = {
        "Cache V2 Package": "Cache Package",
        "Cache V2 Linking Package": "Cache Linking Package",
        "V2 Services package": "Services package",
        "Cache V2 Serialization Package": "Cache Serialization Package",
        "OSM cache V2": "OSM cache",
        "cache V2": "cache",
        "Cache Metadata V2": "Cache Metadata",
        "Cache Serializer V2": "Cache Serializer",
        "OSM data V2": "OSM data",
        "cache serializer V2": "cache serializer",
        "multi-source OSM cache V2": "multi-source OSM cache",
        "OSM cache V2 with multi-source": "OSM cache with multi-source",
        "Metadata for cached OSM data V2": "Metadata for cached OSM data",
        "Main serializer for OSM cache V2": "Main serializer for OSM cache",
        "Initialize the cache serializer V2": "Initialize the cache serializer",
        "Cache OSM V2": "Cache OSM"
    }
    
    file_replacements = {
        "osm_cache_v2_test": "osm_cache_test",
        "osm_cache_v2": "osm_cache",
        "metadata_v2.json": "metadata.json",
        "cache_data_v2.bin": "cache_data.bin"
    }
    
    updated_files = []
    
    for file_path in Path("src/cache").rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remplacer les références dans les commentaires
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            # Remplacer les noms de fichiers/dossiers
            for old, new in file_replacements.items():
                content = content.replace(old, new)
            
            # Remplacer les méthodes avec v2
            content = re.sub(r'_build_chain_from_segment_v2', '_build_chain_from_segment', content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files.append(str(file_path))
                
        except Exception as e:
            print(f"   ❌ Erreur dans {file_path}: {e}")
    
    print(f"   ✅ {len(updated_files)} fichiers mis à jour")
    for file in updated_files:
        print(f"      - {file}")


def update_version_info():
    """Mettre à jour les informations de version"""
    print("📦 Mise à jour des informations de version...")
    
    # Mettre à jour __init__.py principal
    cache_init = Path("src/cache/__init__.py")
    if cache_init.exists():
        with open(cache_init, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Mettre à jour la version
        content = re.sub(r'__version__ = "2\.0\.0"', '__version__ = "1.0.0"', content)
        
        with open(cache_init, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ Version mise à jour à 1.0.0")


def final_verification():
    """Vérification finale des références v2"""
    print("🔍 Vérification finale...")
    
    v2_found = []
    
    for file_path in Path("src/cache").rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les références v2 restantes (en excluant les commentaires de version git, etc.)
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(r'[Vv]2(?!\.0)', line) and not line.strip().startswith('#') and 'version' not in line.lower():
                    v2_found.append((str(file_path), i, line.strip()))
                    
        except Exception as e:
            continue
    
    if v2_found:
        print(f"   ⚠️ {len(v2_found)} références v2 restantes trouvées:")
        for file, line_num, line in v2_found[:10]:
            print(f"      - {file}:{line_num}: {line}")
        if len(v2_found) > 10:
            print(f"      ... et {len(v2_found) - 10} autres")
    else:
        print("   ✅ Aucune référence v2 problématique trouvée")


def main():
    """Fonction principale"""
    print("🧹 Nettoyage final des références v2 dans les commentaires")
    print("=" * 60)
    
    try:
        # 1. Nettoyer les commentaires
        clean_v2_references_in_comments()
        
        # 2. Mettre à jour la version
        update_version_info()
        
        # 3. Vérification finale
        final_verification()
        
        print("\n✅ Nettoyage final terminé!")
        print("   - Commentaires nettoyés")
        print("   - Noms de fichiers de cache mis à jour") 
        print("   - Version corrigée")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")


if __name__ == "__main__":
    main()
