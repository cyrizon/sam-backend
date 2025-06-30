#!/usr/bin/env python3
"""
Analyse complète du cache V1 vs V2
"""

import os
import re
from pathlib import Path

def find_all_python_files(directory):
    """Trouve tous les fichiers Python dans un répertoire"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def analyze_cache_dependencies():
    """Analyse les dépendances entre V1 et V2"""
    
    print("🔍 Analyse des dépendances cache V1 ↔ V2")
    print("=" * 50)
    
    # 1. Ce que V2 utilise de V1
    print("\n1️⃣ Ce que V2 utilise de V1:")
    v2_files = find_all_python_files('src/cache/v2')
    v2_uses_v1 = {}
    
    for file_path in v2_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les imports vers V1 (avec ...)
            v1_imports = re.findall(r'from\s+\.\.\.([^\s]+)\s+import', content)
            if v1_imports:
                v2_uses_v1[file_path] = v1_imports
                
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
    
    if v2_uses_v1:
        for file_path, imports in v2_uses_v1.items():
            rel_path = file_path.replace('src\\cache\\v2\\', '').replace('src/cache/v2/', '')
            print(f"📄 {rel_path}")
            for imp in set(imports):
                print(f"   → ...{imp}")
    else:
        print("✅ V2 n'utilise rien de V1")
    
    # 2. Ce qui utilise V2 en externe
    print(f"\n2️⃣ Modules externes utilisant V2:")
    all_files = find_all_python_files('src')
    external_uses_v2 = {}
    
    for file_path in all_files:
        if 'cache/v2' in file_path:
            continue  # Skip V2 internal files
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les imports de V2
            v2_imports = re.findall(r'from\s+src\.cache\.v2\.([^\s]+)\s+import', content)
            if v2_imports:
                external_uses_v2[file_path] = v2_imports
                
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
    
    if external_uses_v2:
        for file_path, imports in external_uses_v2.items():
            rel_path = file_path.replace('src\\', '').replace('src/', '')
            print(f"📄 {rel_path}")
            for imp in set(imports):
                print(f"   ← v2.{imp}")
    
    # 3. Ce qui utilise V1 en externe
    print(f"\n3️⃣ Modules externes utilisant V1:")
    external_uses_v1 = {}
    
    for file_path in all_files:
        if 'cache/' in file_path and 'v2' not in file_path:
            continue  # Skip V1 internal files
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les imports de V1
            v1_imports = re.findall(r'from\s+src\.cache\.([^v][^\s]*)\s+import', content)
            if v1_imports:
                external_uses_v1[file_path] = v1_imports
                
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
    
    if external_uses_v1:
        for file_path, imports in external_uses_v1.items():
            rel_path = file_path.replace('src\\', '').replace('src/', '')
            print(f"📄 {rel_path}")
            for imp in set(imports):
                print(f"   ← v1.{imp}")
    else:
        print("✅ Aucun module externe n'utilise V1")
    
    return v2_uses_v1, external_uses_v2, external_uses_v1

def analyze_v1_modules():
    """Analyse les modules de V1 utilisés par V2"""
    
    print(f"\n4️⃣ Modules V1 nécessaires pour V2:")
    
    # Modules V1 utilisés par V2
    v1_modules_used = [
        'serialization.compression_utils',
        'utils.geographic_utils'
    ]
    
    for module in v1_modules_used:
        file_path = f"src/cache/{module.replace('.', '/')}.py"
        if os.path.exists(file_path):
            print(f"✅ {module} - Fichier existe: {file_path}")
        else:
            print(f"❌ {module} - Fichier manquant: {file_path}")

def count_files():
    """Compte les fichiers dans V1 et V2"""
    
    print(f"\n📊 Statistiques:")
    
    v1_files = find_all_python_files('src/cache')
    v2_files = find_all_python_files('src/cache/v2')
    
    # Exclure V2 du compte V1
    v1_only_files = [f for f in v1_files if 'v2' not in f]
    
    print(f"   Fichiers V1 (hors V2): {len(v1_only_files)}")
    print(f"   Fichiers V2: {len(v2_files)}")
    print(f"   Total cache: {len(v1_files)}")

def main():
    v2_uses_v1, external_uses_v2, external_uses_v1 = analyze_cache_dependencies()
    analyze_v1_modules()
    count_files()
    
    print(f"\n🎯 Résumé de migration:")
    print(f"   V2 dépend de {len(set([imp for imports in v2_uses_v1.values() for imp in imports]))} modules V1")
    print(f"   {len(external_uses_v2)} modules externes utilisent V2")
    print(f"   {len(external_uses_v1)} modules externes utilisent V1")
    
    if len(external_uses_v1) == 0 and len(v2_uses_v1) <= 2:
        print(f"\n✅ Migration possible:")
        print(f"   1. Déplacer compression_utils et geographic_utils dans V2")
        print(f"   2. Remplacer cache/v2 par cache/")
        print(f"   3. Supprimer l'ancien cache V1")
    else:
        print(f"\n⚠️ Migration complexe - V1 encore utilisé")

if __name__ == "__main__":
    main()
