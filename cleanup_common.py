#!/usr/bin/env python3
"""
Nettoyage sécurisé du module common
"""

import os
import shutil
from pathlib import Path

# Fichiers à supprimer (tout sauf base_constants.py et __init__.py)
FILES_TO_REMOVE = [
    "src/services/common/base_error_handler.py",
    "src/services/common/base_response_builder.py",
    "src/services/common/budget_messages.py", 
    "src/services/common/common_messages.py",
    "src/services/common/common_validator.py",
    "src/services/common/operation_tracker.py",
    "src/services/common/result_formatter.py",
    "src/services/common/toll_messages.py"
]

def backup_files():
    """Créer une sauvegarde des fichiers à supprimer"""
    backup_dir = Path("backup_common_unused")
    backup_dir.mkdir(exist_ok=True)
    
    backed_up = []
    for file_path in FILES_TO_REMOVE:
        if os.path.exists(file_path):
            filename = Path(file_path).name
            backup_path = backup_dir / filename
            shutil.copy2(file_path, backup_path)
            backed_up.append(file_path)
            print(f"✅ Sauvegardé: {file_path} -> {backup_path}")
    
    return backed_up

def update_init_file():
    """Mettre à jour le fichier __init__.py pour ne garder que BaseOptimizationConfig"""
    init_path = "src/services/common/__init__.py"
    
    new_content = '''"""
Common services module
---------------------

Module contenant les constantes de base pour l'optimisation.
"""

from .base_constants import BaseOptimizationConfig

__all__ = [
    'BaseOptimizationConfig'
]
'''
    
    # Backup de l'ancien __init__.py
    if os.path.exists(init_path):
        shutil.copy2(init_path, "backup_common_unused/__init__.py")
        print(f"✅ Sauvegardé: {init_path} -> backup_common_unused/__init__.py")
    
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"🔄 Mis à jour: {init_path}")

def remove_files(files_to_remove):
    """Supprimer les fichiers"""
    removed = []
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            removed.append(file_path)
            print(f"🗑️ Supprimé: {file_path}")
    
    return removed

def test_imports():
    """Tester que les imports principaux fonctionnent encore"""
    try:
        # Test de l'import principal
        from src.services.common.base_constants import BaseOptimizationConfig
        from src.services.optimization.constants import TollOptimizationConfig
        
        print("✅ Tests d'imports réussis")
        return True
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Nettoyage sécurisé du module common")
    print("=" * 50)
    
    # 1. Créer sauvegarde
    print("\n1. Création de la sauvegarde...")
    backed_up = backup_files()
    
    if not backed_up:
        print("❌ Aucun fichier à sauvegarder/supprimer")
        exit(0)
    
    # 2. Test avant suppression
    print("\n2. Test des imports avant suppression...")
    if not test_imports():
        print("❌ Imports échoués avant suppression - Arrêt")
        exit(1)
    
    # 3. Mettre à jour __init__.py
    print("\n3. Mise à jour du __init__.py...")
    update_init_file()
    
    # 4. Supprimer les fichiers
    print("\n4. Suppression des fichiers...")
    removed = remove_files(backed_up)
    
    # 5. Test après suppression
    print("\n5. Test des imports après suppression...")
    if test_imports():
        print("✅ Nettoyage du module common réussi!")
        print(f"📁 Sauvegarde disponible dans: backup_common_unused/")
        print(f"🗑️ Fichiers supprimés: {len(removed)}")
        print(f"✅ Seul base_constants.py reste dans common/")
    else:
        print("❌ Imports échoués après suppression")
        print("🔄 Restauration recommandée depuis backup_common_unused/")
