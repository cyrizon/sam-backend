#!/usr/bin/env python3
"""
Script de nettoyage final - suppression des suffixes v2 dans les noms de fichiers et classes
"""

import os
import re
import shutil
from pathlib import Path


def backup_files():
    """Créer une sauvegarde avant nettoyage"""
    print("💾 Création de la sauvegarde...")
    
    backup_dir = Path("backup_final_cleanup")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    # Sauvegarder tout le dossier cache
    shutil.copytree("src/cache", backup_dir / "cache")
    
    # Sauvegarder les fichiers externes qui utilisent le cache
    external_files = [
        "src/__init__.py",
        "src/services/optimization/route_optimization/utils/cache_accessor.py"
    ]
    
    for file_path in external_files:
        if Path(file_path).exists():
            dest = backup_dir / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest)
    
    print(f"✅ Sauvegarde créée dans {backup_dir}")


def rename_files():
    """Renommer les fichiers avec v2"""
    print("📝 Renommage des fichiers...")
    
    renames = {
        "src/cache/managers/osm_data_manager_v2.py": "src/cache/managers/osm_data_manager.py",
        "src/cache/managers/v2_cache_manager_with_pricing.py": "src/cache/managers/cache_manager_with_pricing.py", 
        "src/cache/managers/v2_cache_manager_with_linking.py": "src/cache/managers/cache_manager_with_linking.py",
        "src/cache/serialization/cache_metadata_v2.py": "src/cache/serialization/cache_metadata.py",
        "src/cache/serialization/cache_serializer_v2.py": "src/cache/serialization/cache_serializer.py"
    }
    
    for old_path, new_path in renames.items():
        if Path(old_path).exists():
            print(f"   📁 {old_path} → {new_path}")
            shutil.move(old_path, new_path)
        else:
            print(f"   ⚠️ {old_path} n'existe pas")


def update_class_names_in_file(file_path, class_renames):
    """Mettre à jour les noms de classes dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_name, new_name in class_renames.items():
            # Remplacer les définitions de classe
            content = re.sub(rf'\bclass\s+{old_name}\b', f'class {new_name}', content)
            # Remplacer les utilisations
            content = re.sub(rf'\b{old_name}\b', new_name, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ Erreur dans {file_path}: {e}")
        return False


def update_imports_in_file(file_path, import_renames):
    """Mettre à jour les imports dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_import, new_import in import_renames.items():
            content = content.replace(old_import, new_import)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ Erreur dans {file_path}: {e}")
        return False


def update_all_references():
    """Mettre à jour toutes les références"""
    print("🔄 Mise à jour des références...")
    
    # Renommages de classes
    class_renames = {
        "OSMDataManager": "OSMDataManager",
        "CacheManagerWithPricing": "CacheManagerWithPricing",
        "CacheManagerWithLinking": "CacheManagerWithLinking", 
        "CacheMetadata": "CacheMetadata",
        "CacheSerializer": "CacheSerializer",
        "OSMData": "OSMData"
    }
    
    # Renommages d'imports
    import_renames = {
        # Imports de fichiers renommés
        "from ..serialization.cache_serializer import": "from ..serialization.cache_serializer import",
        "from ..serialization.cache_metadata import": "from ..serialization.cache_metadata import",
        "from .cache_manager_with_pricing import": "from .cache_manager_with_pricing import",
        "from .osm_data_manager import": "from .osm_data_manager import",
        "from ..managers.osm_data_manager import": "from ..managers.osm_data_manager import",
        "from .cache_metadata import": "from .cache_metadata import",
        "from .cache_serializer import": "from .cache_serializer import",
        "from src.cache.managers.cache_manager_with_linking import": "from src.cache.managers.cache_manager_with_linking import",
        
        # Imports de classes renommées (après renommage des fichiers)
        "CacheSerializer": "CacheSerializer",
        "CacheMetadata": "CacheMetadata",
        "OSMDataManager": "OSMDataManager",
        "CacheManagerWithPricing": "CacheManagerWithPricing",
        "CacheManagerWithLinking": "CacheManagerWithLinking",
        "OSMData": "OSMData"
    }
    
    # Parcourir tous les fichiers Python
    updated_files = []
    
    for file_path in Path(".").rglob("*.py"):
        if "__pycache__" in str(file_path) or "backup_" in str(file_path):
            continue
        
        # Mettre à jour les imports
        import_updated = update_imports_in_file(file_path, import_renames)
        
        # Mettre à jour les classes
        class_updated = update_class_names_in_file(file_path, class_renames)
        
        if import_updated or class_updated:
            updated_files.append(str(file_path))
    
    print(f"   ✅ {len(updated_files)} fichiers mis à jour")
    for file in updated_files[:10]:  # Afficher les 10 premiers
        print(f"      - {file}")
    if len(updated_files) > 10:
        print(f"      ... et {len(updated_files) - 10} autres")


def update_init_files():
    """Mettre à jour les fichiers __init__.py"""
    print("📦 Mise à jour des __init__.py...")
    
    # Mettre à jour src/cache/__init__.py
    cache_init = Path("src/cache/__init__.py")
    if cache_init.exists():
        with open(cache_init, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer OSMDataManager par OSMDataManager
        content = content.replace('OSMDataManager', 'OSMDataManager')
        content = content.replace("'OSMDataManager'", "'OSMDataManager'")
        
        with open(cache_init, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ src/cache/__init__.py mis à jour")
    
    # Mettre à jour src/cache/managers/__init__.py
    managers_init = Path("src/cache/managers/__init__.py")
    if managers_init.exists():
        with open(managers_init, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer les imports
        content = content.replace('from .osm_data_manager import OSMDataManager', 
                                'from .osm_data_manager import OSMDataManager')
        content = content.replace("'OSMDataManager'", "'OSMDataManager'")
        
        with open(managers_init, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ src/cache/managers/__init__.py mis à jour")
    
    # Mettre à jour src/cache/serialization/__init__.py
    serialization_init = Path("src/cache/serialization/__init__.py")
    if serialization_init.exists():
        with open(serialization_init, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer les imports
        content = content.replace('from .cache_metadata import CacheMetadata', 
                                'from .cache_metadata import CacheMetadata')
        content = content.replace('from .cache_serializer import CacheSerializer', 
                                'from .cache_serializer import CacheSerializer')
        content = content.replace("'CacheMetadata'", "'CacheMetadata'")
        content = content.replace("'CacheSerializer'", "'CacheSerializer'")
        
        with open(serialization_init, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ src/cache/serialization/__init__.py mis à jour")


def test_imports():
    """Tester les imports après nettoyage"""
    print("🧪 Test des imports...")
    
    import_tests = [
        "from src.cache.managers.cache_manager_with_linking import CacheManagerWithLinking",
        "from src.cache.managers.osm_data_manager import OSMDataManager", 
        "from src.cache.serialization.cache_metadata import CacheMetadata",
        "from src.cache.serialization.cache_serializer import CacheSerializer",
        "from src.cache import OSMDataManager"
    ]
    
    for test_import in import_tests:
        try:
            exec(test_import)
            print(f"   ✅ {test_import}")
        except Exception as e:
            print(f"   ❌ {test_import}: {e}")


def main():
    """Fonction principale"""
    print("🧹 Nettoyage final des suffixes v2")
    print("=" * 50)
    
    try:
        # 1. Sauvegarde
        backup_files()
        
        # 2. Renommer les fichiers
        rename_files()
        
        # 3. Mettre à jour les références
        update_all_references()
        
        # 4. Mettre à jour les __init__.py
        update_init_files() 
        
        # 5. Tester les imports
        test_imports()
        
        print("\n✅ Nettoyage terminé avec succès!")
        print("   - Fichiers renommés sans suffixe v2")
        print("   - Classes renommées sans suffixe V2")
        print("   - Imports mis à jour")
        print("   - Sauvegarde disponible dans backup_final_cleanup/")
        
    except Exception as e:
        print(f"\n❌ Erreur pendant le nettoyage: {e}")
        print("   - Restaurez depuis la sauvegarde si nécessaire")


if __name__ == "__main__":
    main()
