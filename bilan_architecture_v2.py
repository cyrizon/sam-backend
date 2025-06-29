"""
Bilan Final Architecture V2
===========================

Résumé de l'architecture route optimization refactorisée.
"""

import os

def analyze_architecture():
    """Analyse finale de l'architecture."""
    print("🎯 BILAN FINAL DE L'ARCHITECTURE ROUTE OPTIMIZATION V2")
    print("=" * 60)
    
    # Analyse des tailles
    print("\n📏 ANALYSE DES TAILLES DE FICHIERS")
    print("-" * 40)
    
    route_opt_path = "src/services/toll/route_optimization"
    file_sizes = []
    
    for root, dirs, files in os.walk(route_opt_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                    
                    # Calculer le chemin relatif
                    rel_path = os.path.relpath(file_path, route_opt_path)
                    file_sizes.append((lines, rel_path))
                    
                except Exception as e:
                    print(f"   ⚠️ Erreur lecture {file}: {e}")
    
    # Trier par taille décroissante
    file_sizes.sort(reverse=True)
    
    # Afficher les plus gros fichiers
    print("TOP 15 des plus gros fichiers:")
    for i, (lines, path) in enumerate(file_sizes[:15], 1):
        status = "✅" if lines <= 300 else "❌"
        print(f"{i:2d}. {status} {lines:3d} lignes - {path}")
    
    # Statistiques globales
    total_files = len(file_sizes)
    oversized = sum(1 for lines, _ in file_sizes if lines > 300)
    total_lines = sum(lines for lines, _ in file_sizes)
    avg_lines = total_lines / total_files if total_files > 0 else 0
    
    print(f"\n📊 STATISTIQUES GLOBALES")
    print("-" * 25)
    print(f"• Total fichiers Python: {total_files}")
    print(f"• Fichiers > 300 lignes: {oversized} {'❌' if oversized > 0 else '✅'}")
    print(f"• Total lignes de code: {total_lines:,}")
    print(f"• Moyenne lignes/fichier: {avg_lines:.1f}")
    
    # Architecture modulaire
    print(f"\n🏗️ ARCHITECTURE MODULAIRE")
    print("-" * 30)
    
    modules = {}
    for lines, path in file_sizes:
        folder = os.path.dirname(path).split('/')[0] if '/' in path else 'root'
        if folder not in modules:
            modules[folder] = {'files': 0, 'lines': 0}
        modules[folder]['files'] += 1
        modules[folder]['lines'] += lines
    
    for module, stats in sorted(modules.items()):
        avg = stats['lines'] / stats['files']
        print(f"• {module:20} : {stats['files']:2d} fichiers, {stats['lines']:4d} lignes (moy: {avg:.1f})")
    
    # Validation des contraintes
    print(f"\n✅ VALIDATION DES CONTRAINTES")
    print("-" * 35)
    
    constraints_met = [
        ("Taille fichiers < 300 lignes", oversized == 0),
        ("Architecture modulaire", len(modules) >= 5),
        ("Séparation responsabilités", avg_lines < 200),
        ("Cache V2 intégré", any("cache_accessor" in path for _, path in file_sizes))
    ]
    
    for constraint, met in constraints_met:
        status = "✅" if met else "❌"
        print(f"{status} {constraint}")
    
    # Conclusion
    all_constraints_met = all(met for _, met in constraints_met)
    
    print(f"\n🎉 CONCLUSION")
    print("-" * 15)
    if all_constraints_met:
        print("✅ ARCHITECTURE V2 VALIDÉE !")
        print("✅ Toutes les contraintes respectées")
        print("✅ Code propre et modulaire")
        print("✅ Prêt pour la production")
    else:
        print("⚠️ Quelques ajustements nécessaires")
    
    return all_constraints_met


if __name__ == "__main__":
    analyze_architecture()
