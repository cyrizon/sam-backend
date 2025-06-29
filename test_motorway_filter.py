"""
Test du filtre de liens autoroutiers amélioré.
Valide que les aires sont bien exclues et les vraies entrées/sorties acceptées.
"""

import sys
sys.path.append('.')

from src.services.toll.route_optimization.toll_analysis.selection_analyzer import SelectionAnalyzer

def create_mock_link(link_id, destination, coordinates):
    """Crée un mock CompleteMotorwayLink pour les tests."""
    class MockLink:
        def __init__(self, link_id, destination, coordinates):
            self.link_id = link_id
            self.destination = destination
            self._coordinates = coordinates
        
        def get_all_coordinates(self):
            return self._coordinates
        
        def get_start_point(self):
            return self._coordinates[0] if self._coordinates else [0, 0]
    
    return MockLink(link_id, destination, coordinates)

def test_motorway_filter():
    """Test du filtre _is_valid_motorway_link avec différents cas."""
    
    analyzer = SelectionAnalyzer()
    
    # Cas 1: Aire problématique courte (80.8m) - destination null
    aire_courte = create_mock_link(
        "entry_direct_537170765",
        None,  # destination null
        [
            [4.5068569, 45.8717074],
            [4.506783, 45.8716323],
            [4.5066959, 45.871561],
            [4.5064967, 45.8714539],
            [4.5062796, 45.8712707]
        ]
    )
    
    # Cas 2: Vraie entrée longue (1236.7m) - destination null
    vraie_entree_1 = create_mock_link(
        "entry_link_2780203",
        None,  # destination null mais longue
        [
            [5.0806074, 45.0229708],
            [5.0808314, 45.0228953],
            [5.0810118, 45.0228338],
            [5.0811925, 45.0227859],
            [5.0812814, 45.022775],
            [5.0813726, 45.0227702],
            [5.0814637, 45.0227693],
            [5.0815402, 45.0227788],
            [5.0816341, 45.0228015],
            [5.0817123, 45.0228278],
            [5.0817776, 45.0228584],
            [5.0818468, 45.0228979],
            [5.0818996, 45.0229428],
            [5.0819305, 45.0229778],
            [5.0819617, 45.0230168],
            [5.0819908, 45.0230717],
            [5.0820096, 45.0231286],
            [5.0820188, 45.0231782],
            [5.082019, 45.0232395],
            [5.0820136, 45.0232926],
            [5.0820049, 45.0233329],
            [5.0819787, 45.0234129],
            [5.0818683, 45.0236613],
            [5.0813386, 45.0248045],
            [5.081023, 45.0254912],
            [5.0809201, 45.0257813],
            [5.0808251, 45.0261236],
            [5.080791, 45.0262708],
            [5.080748, 45.0265014],
            [5.0806324, 45.0272295],
            [5.0805681, 45.0274152],
            [5.0805783, 45.0272237],
            [5.0806938, 45.0265075],
            [5.0807597, 45.0261216],
            [5.0808549, 45.0257022],
            [5.0810586, 45.0250414],
            [5.0810815, 45.0249419],
            [5.0811023, 45.024831],
            [5.0811137, 45.0247481],
            [5.0811208, 45.0246715],
            [5.0811211, 45.0245888],
            [5.0811124, 45.0245021],
            [5.0810983, 45.0244348],
            [5.0810842, 45.0243789],
            [5.0810668, 45.0243286],
            [5.0810339, 45.0242518],
            [5.0809977, 45.0241869],
            [5.0809473, 45.0241096],
            [5.080881, 45.0240291],
            [5.0807905, 45.0239395],
            [5.0806919, 45.0238585],
            [5.0805932, 45.0237904],
            [5.0804935, 45.0237324],
            [5.0804217, 45.0236978],
            [5.0803357, 45.0236587],
            [5.0802405, 45.0236213],
            [5.0795586, 45.0233812]
        ]
    )
    
    # Cas 3: Vraie entrée moyenne (502.0m) - destination null
    vraie_entree_2 = create_mock_link(
        "entry_link_4014140",
        None,  # destination null mais moyenne
        [
            [5.8210708, 45.2234288],
            [5.8211662, 45.2232593],
            [5.8211856, 45.223211],
            [5.8212043, 45.2231521],
            [5.8212136, 45.223082],
            [5.821204, 45.2230025],
            [5.8211883, 45.2228814],
            [5.8209269, 45.2224487],
            [5.8207191, 45.2221267],
            [5.8205247, 45.2218591],
            [5.8203348, 45.2216236],
            [5.8187736, 45.2197755]
        ]
    )
    
    # Cas 4: Aire étiquetée (881.8m) - destination "Aire des Noues"
    aire_etiquetee = create_mock_link(
        "entry_link_1211819191",
        "Aire des Noues",  # destination avec "Aire"
        [
            [5.2996033, 47.0645413],
            [5.2998609, 47.06458],
            [5.3000097, 47.0646038],
            [5.3000972, 47.0646216],
            [5.3001697, 47.0646414],
            [5.3002298, 47.0646647],
            [5.300277, 47.0646903],
            [5.3003362, 47.0647269],
            [5.3005617, 47.0649058],
            [5.3006463, 47.0649663],
            [5.3007226, 47.0650166],
            [5.3008105, 47.0650678],
            [5.3008922, 47.0651145],
            [5.3009746, 47.0651569],
            [5.3011083, 47.0652163],
            [5.3012728, 47.0652785],
            [5.30136, 47.0653083],
            [5.3014451, 47.0653373],
            [5.3016015, 47.065381],
            [5.3023848, 47.0655546],
            [5.3028775, 47.0656542],
            [5.3038742, 47.0658476],
            [5.3045993, 47.0659893],
            [5.3053701, 47.0661418],
            [5.3061265, 47.0663074],
            [5.3067188, 47.066438],
            [5.307007, 47.0665125],
            [5.3072092, 47.0665967]
        ]
    )
    
    # Cas 5: Vraie sortie avec destination explicite (longueur suffisante)
    vraie_sortie = create_mock_link(
        "exit_link_123456",
        "Villefranche sur Saône;Pontcharra-sur-Turdine;Tarare Est",  # destination réelle
        [
            [4.7319396, 45.9734404],
            [4.7320000, 45.9735000],
            [4.7321000, 45.9736000],
            [4.7322000, 45.9737000],
            [4.7323000, 45.9738000],
            [4.7324000, 45.9739000],
            [4.7325000, 45.9740000]
        ]
    )
    
    print("🧪 Test du filtre de liens autoroutiers")
    print("=" * 60)
    
    # Tests
    test_cases = [
        (aire_courte, "Aire courte (80.8m, dest=null)", False),
        (vraie_entree_1, "Vraie entrée longue (1236.7m, dest=null)", True),
        (vraie_entree_2, "Vraie entrée moyenne (502.0m, dest=null)", True),
        (aire_etiquetee, "Aire étiquetée (881.8m, dest='Aire des Noues')", False),
        (vraie_sortie, "Vraie sortie (dest explicite)", True)
    ]
    
    all_passed = True
    
    for link, description, expected in test_cases:
        # Calculer la longueur
        length = analyzer._calculate_link_length_meters(link)
        
        # Tester le filtre
        result = analyzer._is_valid_motorway_link(link)
        
        # Vérifier le résultat
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result != expected:
            all_passed = False
        
        print(f"{status} {description}")
        print(f"     Longueur: {length:.1f}m")
        print(f"     Destination: {link.destination}")
        print(f"     Attendu: {expected}, Obtenu: {result}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("🎉 Tous les tests sont PASSÉS ! Le filtre fonctionne correctement.")
    else:
        print("⚠️ Certains tests ont ÉCHOUÉ. Vérifiez la logique du filtre.")
    
    print("\n📋 Résumé de la logique du filtre :")
    print("1. Si destination contient 'aire' → EXCLU (même si long)")
    print("2. Si destination non null et sans 'aire' → ACCEPTÉ (entrée/sortie réelle)")
    print("3. Si destination null → ACCEPTÉ seulement si longueur > 200m")

if __name__ == "__main__":
    test_motorway_filter()
