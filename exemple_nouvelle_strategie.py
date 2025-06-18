"""
Exemple d'utilisation de la nouvelle stratégie tollways
=====================================================

Ce script montre comment utiliser la nouvelle stratégie de segmentation
basée sur les données tollways d'ORS.
"""

from src.services.smart_route import SmartRouteService

def exemple_utilisation_nouvelle_strategie():
    """
    Exemple d'utilisation de la nouvelle stratégie tollways.
    """
    
    # Initialiser le service (nouvelle stratégie activée par défaut)
    smart_service = SmartRouteService()
    
    # Coordonnées d'exemple (format ORS : [longitude, latitude])
    coordinates = [
        [7.7521, 48.5734],  # Strasbourg  
        [4.8357, 45.7640]   # Lyon
    ]
    
    # 1. Route avec limite de péages
    print("🧪 Test : Route avec maximum 2 péages")
    try:
        result = smart_service.compute_route_with_toll_limit(
            coordinates=coordinates,
            max_tolls=2,
            veh_class="c1"
        )
        
        print("✅ Résultat obtenu:")
        print(f"   - Statut: {result.get('status', 'N/A')}")
        print(f"   - Stratégie utilisée: nouvelle tollways")
        
        if 'route' in result:
            route = result['route']
            if 'features' in route and route['features']:
                props = route['features'][0].get('properties', {})
                summary = props.get('summary', {})
                print(f"   - Distance: {summary.get('distance', 0)/1000:.1f} km")
                print(f"   - Durée: {summary.get('duration', 0)/60:.0f} min")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("ℹ️ Vérifiez que ORS_BASE_URL est configuré dans .env")

def exemple_comparaison_strategies():
    """
    Exemple de comparaison entre ancienne et nouvelle stratégie.
    """
    print("\n🔍 Comparaison des stratégies (simulation)")
    
    coordinates = [
        [2.3522, 48.8566],  # Paris
        [5.3698, 43.2965]   # Marseille  
    ]
    
    print("📍 Trajet: Paris -> Marseille")
    print("🎯 Contrainte: Maximum 3 péages")
    
    # Nouvelle stratégie (par défaut)
    print("\n🚀 Nouvelle stratégie tollways:")
    print("   - Extraction directe depuis ORS extras")
    print("   - Segmentation précise par indices")
    print("   - Polygones d'évitement optimisés")
    print("   - Pipeline: Route base → Analyse tollways → Évitement sélectif")
    
    # Note sur l'ancienne stratégie
    print("\n⚡ Ancienne stratégie (désactivée):")
    print("   - Calcul manuel des segments")
    print("   - Approximations géographiques")
    print("   - Plus d'appels API nécessaires")
    print("   - Pipeline: Route base → Localisation péages → Combinaisons → Calculs multiples")

def exemple_configuration():
    """
    Exemple de configuration avancée.
    """
    print("\n⚙️ Configuration de la stratégie")
    
    # Configuration par défaut (recommandée)
    print("📦 Configuration par défaut:")
    print("   use_new_tollway_strategy=True")
    print("   use_segmentation=True (pour compatibilité)")
    
    # Configuration alternative pour tests
    print("\n🧪 Pour tester l'ancienne stratégie:")
    print("   Modifier smart_route.py:")
    print("   use_new_tollway_strategy=False")
    
    # Variables d'environnement requises
    print("\n🔑 Variables d'environnement requises:")
    print("   ORS_BASE_URL=http://localhost:8080/ors")
    print("   Ou votre instance ORS personnalisée")

if __name__ == "__main__":
    print("=" * 60)
    print("EXEMPLE D'UTILISATION - NOUVELLE STRATÉGIE TOLLWAYS")
    print("=" * 60)
    
    exemple_utilisation_nouvelle_strategie()
    exemple_comparaison_strategies() 
    exemple_configuration()
    
    print("\n" + "=" * 60)
    print("💡 Pour plus d'informations, voir NOUVELLE_STRATEGIE_TOLLWAYS.md")
    print("=" * 60)
