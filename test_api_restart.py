"""
Test simple via l'API après redémarrage du serveur.
"""

import requests
import json

def test_api_after_restart():
    """Test l'API après redémarrage pour prendre en compte les modifications."""
    
    url = "http://localhost:5000/api/smart-route/tolls"
    
    payload = {
        "coordinates": [
            [7.448405, 48.261682],  # Sélestat
            [3.11506, 45.784359]    # Besançon
        ],
        "target_tolls": 2,
        "vehicle_class": "c1"
    }
    
    print("🧪 Test API après redémarrage")
    print(f"   Route : Sélestat → Besançon")
    print(f"   Objectif : 2 péages")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 Réponse API :")
            print(f"   Success : {data.get('success', False)}")
            print(f"   Strategy : {data.get('strategy_used', 'Unknown')}")
            print(f"   Toll count : {data.get('toll_count', 0)}")
            print(f"   Respects constraint : {data.get('respects_constraint', False)}")
            
            # Regarder les segments si disponibles
            segments = data.get('segments', [])
            if segments:
                print(f"\n🔍 Analyse des segments ({len(segments)} segments) :")
                for i, segment in enumerate(segments):
                    if isinstance(segment, dict):
                        has_toll = segment.get('has_toll', False)
                        reason = segment.get('segment_reason', segment.get('description', 'Inconnu'))
                        
                        toll_status = '🚫 SANS péage' if not has_toll else '💰 AVEC péages'
                        print(f"   Segment {i+1}: {toll_status}")
                        print(f"      💡 {reason}")
                    else:
                        print(f"   Segment {i+1}: {segment}")
                        
                # Vérification de l'ordre
                if len(segments) >= 2 and all(isinstance(s, dict) for s in segments):
                    first_toll = segments[0].get('has_toll', False)
                    second_toll = segments[1].get('has_toll', False)
                    
                    print(f"\n✅ Vérification de l'ordre :")
                    if not first_toll and second_toll:
                        print(f"   ✅ CORRECT : Segment 1 SANS péage, Segment 2 AVEC péages")
                        return True
                    else:
                        print(f"   ❌ INCORRECT : Segment 1 {first_toll}, Segment 2 {second_toll}")
                        return False
            else:
                print(f"   ⚠️ Pas de segments dans la réponse")
                return False
                
        else:
            print(f"   ❌ Erreur HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return False

if __name__ == "__main__":
    success = test_api_after_restart()
    print(f"\n🏁 Test {'réussi' if success else 'échoué'}")
