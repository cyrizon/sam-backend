#!/usr/bin/env python3
"""
Migration cache V2 -> cache principal
"""

import os
import shutil
from pathlib import Path

def backup_current_cache():
    """Sauvegarde l'ancien cache V1"""
    backup_dir = Path("backup_cache_v1")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    # Exclure v2 de la sauvegarde
    src_cache = Path("src/cache")
    
    # Copier tout sauf v2
    backup_dir.mkdir(exist_ok=True)
    for item in src_cache.iterdir():
        if item.name != 'v2' and item.name != '__pycache__':
            if item.is_dir():
                shutil.copytree(item, backup_dir / item.name)
            else:
                shutil.copy2(item, backup_dir / item.name)
    
    print(f"✅ Sauvegarde V1 créée: {backup_dir}")

def copy_v1_dependencies_to_v2():
    """Copie les 2 modules V1 nécessaires dans V2"""
    
    dependencies = [
        ("src/cache/serialization/compression_utils.py", "src/cache/v2/serialization/compression_utils.py"),
        ("src/cache/utils/geographic_utils.py", "src/cache/v2/utils/geographic_utils.py")
    ]
    
    for src, dst in dependencies:
        dst_dir = Path(dst).parent
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ Copié: {src} -> {dst}")
        else:
            print(f"❌ Source manquante: {src}")

def update_v2_imports():
    """Met à jour les imports dans V2 pour utiliser les copies locales"""
    
    files_to_update = [
        "src/cache/v2/serialization/cache_serializer_v2.py",
        "src/cache/v2/linking/toll_detector.py", 
        "src/cache/v2/linking/link_builder.py"
    ]
    
    for file_path in files_to_update:
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer les imports vers V1
        updated = content.replace(
            "from ...serialization.compression_utils import",
            "from .compression_utils import"
        ).replace(
            "from ...utils.geographic_utils import", 
            "from ..utils.geographic_utils import"
        )
        
        if updated != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated)
            print(f"🔄 Mis à jour: {file_path}")

def remove_v1_files():
    """Supprime les anciens fichiers V1 (garde seulement v2)"""
    
    cache_dir = Path("src/cache")
    
    for item in cache_dir.iterdir():
        if item.name not in ['v2', '__pycache__']:
            if item.is_dir():
                shutil.rmtree(item)
                print(f"🗑️ Dossier supprimé: {item}")
            else:
                os.remove(item)
                print(f"🗑️ Fichier supprimé: {item}")

def promote_v2_to_main():
    """Déplace v2 au niveau principal cache"""
    
    v2_dir = Path("src/cache/v2")
    cache_dir = Path("src/cache")
    
    # Déplacer tous les contenus de v2 vers cache
    for item in v2_dir.iterdir():
        dst = cache_dir / item.name
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        
        shutil.move(str(item), str(dst))
        print(f"📦 Déplacé: v2/{item.name} -> cache/{item.name}")
    
    # Supprimer le dossier v2 vide
    v2_dir.rmdir()
    print(f"🗑️ Dossier v2 supprimé")

def update_external_imports():
    """Met à jour tous les imports externes de v2 vers cache"""
    
    import re
    
    # Trouver tous les fichiers qui importent v2
    files_to_update = [
        "src/__init__.py",
        "src/services/optimization/route_optimization/utils/cache_accessor.py",
        "src/services/optimization/route_optimization/toll_analysis/spatial/spatial_index.py",
        "src/services/optimization/route_optimization/toll_analysis/spatial/motorway_links_index.py", 
        "src/services/optimization/route_optimization/toll_analysis/spatial/unified_spatial_manager.py",
        "src/services/optimization/route_optimization/toll_analysis/selection_analyzer.py",
        "src/services/optimization/route_optimization/toll_analysis/replacement/entry_finder.py",
        "src/services/optimization/route_optimization/toll_analysis/replacement/route_proximity_analyzer.py",
        "src/services/optimization/route_optimization/toll_analysis/replacement/toll_replacement_engine.py"
    ]
    
    for file_path in files_to_update:
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer src.cache.v2 par src.cache
        updated = re.sub(r'from src\.cache\.v2\.', 'from src.cache.', content)
        
        if updated != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated)
            print(f"🔄 Imports mis à jour: {file_path}")

def test_imports():
    """Teste que les imports fonctionnent encore"""
    try:
        from src.cache.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking
        from src.cache.models.toll_booth_station import TollBoothStation
        print("✅ Tests d'imports réussis")
        return True
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def main():
    print("🚀 Migration cache V2 -> cache principal")
    print("=" * 50)
    
    # 1. Sauvegarde
    print("\n1. Sauvegarde du cache V1...")
    backup_current_cache()
    
    # 2. Copier dépendances V1 dans V2
    print("\n2. Copie des dépendances V1 dans V2...")
    copy_v1_dependencies_to_v2()
    
    # 3. Mettre à jour les imports internes V2
    print("\n3. Mise à jour des imports internes V2...")
    update_v2_imports()
    
    # 4. Test avant promotion
    print("\n4. Test des imports avant promotion...")
    if not test_imports():
        print("❌ Échec des tests - Arrêt de la migration")
        return False
    
    # 5. Supprimer V1
    print("\n5. Suppression des fichiers V1...")
    remove_v1_files()
    
    # 6. Promouvoir V2
    print("\n6. Promotion V2 -> cache principal...")
    promote_v2_to_main()
    
    # 7. Mettre à jour imports externes
    print("\n7. Mise à jour des imports externes...")
    update_external_imports()
    
    # 8. Test final
    print("\n8. Test final...")
    if test_imports():
        print("✅ Migration cache réussie!")
        print("📁 Sauvegarde V1 disponible dans: backup_cache_v1/")
    else:
        print("❌ Migration échouée")
        return False
    
    return True

if __name__ == "__main__":
    main()
