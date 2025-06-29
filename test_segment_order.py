"""
Test spécifique pour vérifier l'ordre des segments corrigé.
"""

import sys
sys.path.append('.')

import requests
import json

def test_segment_order():
    """Test l'ordre des segments après correction."""
    
    # Route Sélestat → Besançon (même que dans les logs)
    test_data = {
        "coordinates": [
            [7.448405, 48.261682],  # Sélestat 
            [3.11506, 45.784359]    # Vers Martres-d'Artière (approximatif)
        ],
        "target_tolls": 2,
        "vehicle_class": "c1"
    }
    
    print("🧪 Test de l'ordre des segments après correction")
    print(f"   Route : Sélestat → Zone Martres-d'Artière")
    print(f"   Objectif : 2 péages")
    
    try:
        response = requests.post(
            "http://localhost:5000/api/smart-route/tolls",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📋 Résultat API :")
            print(f"   Success : {result.get('success', False)}")
            print(f"   Strategy : {result.get('strategy_used', 'N/A')}")
            print(f"   Toll count : {result.get('toll_count', 'N/A')}")
            print(f"   Respects constraint : {result.get('respects_constraint', 'N/A')}")
            
            # Analyser les segments si disponibles
            segments = result.get('segments', [])
            if segments:
                print(f"\n🔍 Analyse des segments ({len(segments)} segments) :")
                for i, segment in enumerate(segments, 1):
                    has_toll = segment.get('has_toll', False)
                    start = segment.get('start_point', 'N/A')
                    end = segment.get('end_point', 'N/A')
                    reason = segment.get('segment_reason', 'N/A')
                    
                    toll_status = "AVEC péages 💰" if has_toll else "SANS péages 🚫"
                    print(f"     Segment {i}: {toll_status}")
                    print(f"        Raison : {reason}")
                    
                    if isinstance(start, list) and len(start) >= 2:
                        print(f"        Start : [{start[0]:.6f}, {start[1]:.6f}]")
                    if isinstance(end, list) and len(end) >= 2:
                        print(f"        End   : [{end[0]:.6f}, {end[1]:.6f}]")
                
                # Vérifier l'ordre attendu
                print(f"\n✅ Vérification de l'ordre :")
                if len(segments) >= 2:
                    seg1_has_toll = segments[0].get('has_toll', False)
                    seg2_has_toll = segments[1].get('has_toll', False)
                    
                    # Ordre attendu pour SORTIE : [AVEC péages] → [SANS péages]
                    if seg1_has_toll and not seg2_has_toll:
                        print("   🎉 ORDRE CORRECT : [AVEC péages] → [SANS péages]")
                        print("   ✅ Logique SORTIE respectée")
                    elif not seg1_has_toll and seg2_has_toll:
                        print("   🔄 ORDRE ENTRÉE : [SANS péages] → [AVEC péages]")
                        print("   ℹ️ Logique ENTRÉE détectée")
                    else:
                        print("   ⚠️ Ordre inattendu")
                        print(f"      Segment 1: {'AVEC' if seg1_has_toll else 'SANS'} péages")
                        print(f"      Segment 2: {'AVEC' if seg2_has_toll else 'SANS'} péages")
            else:
                print("   ⚠️ Aucun segment trouvé dans la réponse")
                
        else:
            print(f"❌ Erreur API : {response.status_code}")
            print(f"   Réponse : {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion : {e}")

if __name__ == "__main__":
    test_segment_order()
