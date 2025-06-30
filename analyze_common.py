#!/usr/bin/env python3
"""
Analyse d'utilisation du dossier common
"""

import os
import re
from pathlib import Path

def find_external_usage():
    """Trouve les utilisations externes du module common"""
    
    # Classes exportées par common
    common_exports = [
        'BaseOptimizationConfig',
        'BaseErrorHandler', 
        'BaseResponseBuilder',
        'ResultFormatter',
        'TollMessages',
        'BudgetMessages',
        'CommonMessages',
        'CommonRouteValidator',
        'OperationTracker'
    ]
    
    # Chercher les utilisations dans tous les fichiers sauf common
    external_usage = {}
    
    for export in common_exports:
        external_usage[export] = []
    
    # Parcourir tous les fichiers Python
    for root, dirs, files in os.walk('src'):
        # Skip le dossier common lui-même
        if 'common' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Chercher chaque classe dans le contenu
                    for export in common_exports:
                        if export in content:
                            # Vérifier si c'est un vrai usage (pas juste un commentaire)
                            patterns = [
                                f'from.*{export}',
                                f'import.*{export}',
                                f'{export}\\.',
                                f'{export}\\(',
                                f': {export}',
                                f'= {export}'
                            ]
                            
                            for pattern in patterns:
                                if re.search(pattern, content):
                                    external_usage[export].append(file_path)
                                    break
                                    
                except Exception as e:
                    print(f"Erreur lecture {file_path}: {e}")
    
    return external_usage

def analyze_internal_dependencies():
    """Analyse les dépendances internes du module common"""
    
    internal_deps = {}
    common_files = []
    
    # Lister tous les fichiers du dossier common
    for file in os.listdir('src/services/common'):
        if file.endswith('.py') and file != '__init__.py':
            common_files.append(file[:-3])  # Remove .py
    
    # Analyser chaque fichier
    for file_stem in common_files:
        file_path = f'src/services/common/{file_stem}.py'
        internal_deps[file_stem] = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les imports depuis common
            for other_file in common_files:
                if other_file != file_stem:
                    patterns = [
                        f'from.*{other_file}',
                        f'from.*services.common.{other_file}',
                        f'import.*{other_file}'
                    ]
                    
                    for pattern in patterns:
                        if re.search(pattern, content):
                            internal_deps[file_stem].append(other_file)
                            break
                            
        except Exception as e:
            print(f"Erreur analyse {file_path}: {e}")
    
    return internal_deps

def main():
    print("🔍 Analyse du module common")
    print("=" * 40)
    
    # 1. Usage externe
    print("\n1. Usage externe des classes common:")
    external_usage = find_external_usage()
    
    used_externally = []
    unused_externally = []
    
    for class_name, usages in external_usage.items():
        if usages:
            used_externally.append(class_name)
            print(f"✅ {class_name}")
            for usage in set(usages):  # Remove duplicates
                print(f"   📄 {usage}")
        else:
            unused_externally.append(class_name)
    
    print(f"\n❌ Classes non utilisées externalement:")
    for class_name in unused_externally:
        print(f"   - {class_name}")
    
    # 2. Dépendances internes
    print(f"\n2. Dépendances internes:")
    internal_deps = analyze_internal_dependencies()
    
    used_internally = set()
    for file_stem, deps in internal_deps.items():
        if deps:
            print(f"📁 {file_stem}.py dépend de:")
            for dep in deps:
                print(f"   → {dep}.py")
                used_internally.add(dep)
    
    # 3. Résumé
    print(f"\n📊 Résumé:")
    print(f"   Classes utilisées externellement: {len(used_externally)}")
    print(f"   Classes non utilisées externellement: {len(unused_externally)}")
    
    all_files = set(internal_deps.keys())
    used_files = set()
    
    # Fichiers utilisés externalement
    for class_name in used_externally:
        # Mapping approximatif classe -> fichier
        file_mapping = {
            'BaseOptimizationConfig': 'base_constants',
            'BaseErrorHandler': 'base_error_handler',
            'BaseResponseBuilder': 'base_response_builder',
            'ResultFormatter': 'result_formatter',
            'TollMessages': 'toll_messages',
            'BudgetMessages': 'budget_messages',
            'CommonMessages': 'common_messages',
            'CommonRouteValidator': 'common_validator',
            'OperationTracker': 'operation_tracker'
        }
        
        if class_name in file_mapping:
            used_files.add(file_mapping[class_name])
    
    # Ajouter les fichiers utilisés internement
    used_files.update(used_internally)
    
    potentially_unused_files = all_files - used_files
    
    print(f"   Fichiers potentiellement inutilisés: {len(potentially_unused_files)}")
    
    if potentially_unused_files:
        print(f"\n🗑️ Fichiers candidats à la suppression:")
        for file_stem in potentially_unused_files:
            print(f"   - {file_stem}.py")

if __name__ == "__main__":
    main()
