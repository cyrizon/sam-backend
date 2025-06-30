#!/usr/bin/env python3
"""
Dernier nettoyage des références v2 dans les docstrings et messages
"""

import re
from pathlib import Path


def final_v2_cleanup():
    """Nettoyage final et complet des références v2"""
    print("🧹 Nettoyage final et complet des références v2...")
    
    # Patterns de remplacement plus spécifiques
    patterns = [
        (r'V2 Cache Manager', 'Cache Manager'),
        (r'OSM Data Manager V2', 'OSM Data Manager'),
        (r'gestionnaire OSM V2', 'gestionnaire OSM'),
        (r'Gestionnaire V2', 'Gestionnaire'),
        (r'données OSM V2', 'données OSM'),
        (r'système de cache OSM V2', 'système de cache OSM'),
        (r'Cache V2', 'Cache'),
        (r'Extended V2 Cache Manager', 'Extended Cache Manager'),
        (r'V2 étendu', 'étendu'),
        (r'V2 avec', 'avec'),
        (r'V2 complet', 'complet'),
        (r'OSM V2', 'OSM'),
        (r'V2\s*-\s*', ''),  # "V2 - " devient ""
    ]
    
    updated_files = []
    
    for file_path in Path("src/cache").rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Appliquer tous les patterns
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files.append(str(file_path))
                
        except Exception as e:
            print(f"   ❌ Erreur dans {file_path}: {e}")
    
    print(f"   ✅ {len(updated_files)} fichiers nettoyés")
    
    return updated_files


def verify_no_v2_left():
    """Vérifier qu'il ne reste plus de références v2 problématiques"""
    print("🔍 Vérification finale - recherche de références v2...")
    
    v2_found = []
    
    for file_path in Path("src/cache").rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Chercher V2 mais ignorer les versions comme "1.0.0"
                if re.search(r'\bV2\b', line) and not re.search(r'\d+\.\d+\.\d+', line):
                    v2_found.append((str(file_path), i, line.strip()))
                    
        except Exception as e:
            continue
    
    if v2_found:
        print(f"   ⚠️ {len(v2_found)} références V2 restantes:")
        for file, line_num, line in v2_found:
            print(f"      - {file}:{line_num}: {line}")
    else:
        print("   ✅ Aucune référence V2 problématique trouvée!")
    
    return len(v2_found) == 0


def main():
    """Fonction principale"""
    print("🧹 Nettoyage final et complet V2")
    print("=" * 40)
    
    # Nettoyage final
    updated_files = final_v2_cleanup()
    
    # Vérification
    is_clean = verify_no_v2_left()
    
    print(f"\n{'✅' if is_clean else '⚠️'} Nettoyage terminé")
    if is_clean:
        print("   - Toutes les références V2 ont été supprimées")
        print("   - Le cache est maintenant unifié sans suffixes")
    else:
        print("   - Quelques références V2 peuvent subsister")
        print("   - Vérifiez manuellement si nécessaire")


if __name__ == "__main__":
    main()
