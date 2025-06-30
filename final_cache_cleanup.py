#!/usr/bin/env python3
"""
Script de nettoyage final du cache - suppression des références "v2" dans les noms de fichiers et classes
"""

import os
import re
import shutil
from pathlib import Path


def analyze_v2_references():
    """Analyser toutes les références v2 restantes"""
    print("🔍 Analyse des références v2 restantes...")
    
    cache_dir = Path("src/cache")
    v2_files = []
    v2_classes = []
    v2_imports = []
    
    for file_path in cache_dir.rglob("*.py"):
        if file_path.name.startswith("__pycache__"):
            continue
            
        # Fichiers avec "v2" dans le nom
        if "v2" in file_path.name.lower():
            v2_files.append(str(file_path))
        
        # Lire le contenu pour trouver classes et imports
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Classes avec V2
            classes = re.findall(r'class\s+(\w*[Vv]2\w*)', content)
            v2_classes.extend([(str(file_path), cls) for cls in classes])
            
            # Imports avec v2
            imports = re.findall(r'(from\s+[^\s]*v2[^\s]*\s+import\s+[^\n]+)', content)
            v2_imports.extend([(str(file_path), imp) for imp in imports])
            
        except Exception as e:
            print(f"⚠️ Erreur lecture {file_path}: {e}")
    
    return v2_files, v2_classes, v2_imports


def find_external_usages():
    """Trouver les utilisations externes des classes/fichiers v2"""
    print("🔍 Recherche des utilisations externes...")
    
    external_usages = []
    root_dir = Path(".")
    
    # Patterns à chercher
    patterns = [
        r'V2CacheManager',
        r'OSMDataManager',
        r'CacheMetadata',
        r'CacheSerializer',
        r'v2_cache_manager',
        r'osm_data_manager_v2',
        r'cache_metadata_v2',
        r'cache_serializer_v2'
    ]
    
    for file_path in root_dir.rglob("*.py"):
        if "src/cache" in str(file_path) or "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    external_usages.append((str(file_path), pattern, len(matches)))
                    
        except Exception as e:
            continue
    
    return external_usages


def create_renaming_plan():
    """Créer un plan de renommage"""
    print("📋 Création du plan de renommage...")
    
    renaming_plan = {
        # Fichiers
        "src/cache/managers/osm_data_manager_v2.py": "src/cache/managers/osm_data_manager.py",
        "src/cache/managers/v2_cache_manager_with_pricing.py": "src/cache/managers/cache_manager_with_pricing.py", 
        "src/cache/managers/v2_cache_manager_with_linking.py": "src/cache/managers/cache_manager_with_linking.py",
        "src/cache/serialization/cache_metadata_v2.py": "src/cache/serialization/cache_metadata.py",
        "src/cache/serialization/cache_serializer_v2.py": "src/cache/serialization/cache_serializer.py",
        
        # Classes
        "OSMDataManager": "OSMDataManager",
        "CacheManagerWithPricing": "CacheManagerWithPricing",
        "CacheManagerWithLinking": "CacheManagerWithLinking", 
        "CacheMetadata": "CacheMetadata",
        "CacheSerializer": "CacheSerializer"
    }
    
    return renaming_plan


def main():
    """Fonction principale"""
    print("🧹 Nettoyage final du cache V2")
    print("=" * 50)
    
    # Analyse
    v2_files, v2_classes, v2_imports = analyze_v2_references()
    external_usages = find_external_usages()
    
    print(f"\n📊 Résultats de l'analyse:")
    print(f"   - Fichiers avec 'v2': {len(v2_files)}")
    print(f"   - Classes avec 'V2': {len(v2_classes)}")
    print(f"   - Imports avec 'v2': {len(v2_imports)}")
    print(f"   - Utilisations externes: {len(external_usages)}")
    
    print(f"\n📁 Fichiers avec v2:")
    for file in v2_files:
        print(f"   - {file}")
    
    print(f"\n🏛️ Classes avec V2:")
    for file, cls in v2_classes:
        print(f"   - {cls} dans {file}")
    
    print(f"\n📦 Imports avec v2:")
    for file, imp in v2_imports[:10]:  # Limiter l'affichage
        print(f"   - {imp} dans {file}")
    if len(v2_imports) > 10:
        print(f"   ... et {len(v2_imports) - 10} autres")
    
    print(f"\n🔗 Utilisations externes:")
    for file, pattern, count in external_usages:
        print(f"   - {pattern} ({count}x) dans {file}")
    
    # Plan de renommage
    plan = create_renaming_plan()
    print(f"\n📋 Plan de renommage proposé:")
    for old, new in plan.items():
        print(f"   - {old} → {new}")


if __name__ == "__main__":
    main()
