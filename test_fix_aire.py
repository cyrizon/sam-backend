"""
Test pour vérifier la correction des aires d'autoroute.
"""

import requests
import json

def test_api_with_details():
    """Test détaillé de l'API."""
    url = "http://localhost:5000/api/smart-route/tolls"
    
    payload = {
        'start_coords': [7.448405, 48.261682],  # Sélestat
        'end_coords': [3.11506, 45.784359],     # Clermont-Ferrand
        'target_tolls': 2,
        'vehicle_class': 'c1'
    }
    
    print("🧪 Test API avec correction aires d'autoroute")
    print(f"📍 Sélestat → Clermont-Ferrand")
    print(f"🎯 Target: 2 péages")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        result = response.json()
        
        print(f"\n📋 Résultat API:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Toll count: {result.get('toll_count', 0)}")
        print(f"   Distance: {result.get('distance', 0):.1f}km")
        print(f"   Cost: {result.get('cost', 0):.1f}€")
        
        # Segments
        segments = result.get('segments', [])
        print(f"\n📊 Segments ({len(segments)}):")
        for i, seg in enumerate(segments):
            toll_status = "AVEC péages" if seg.get('has_toll') else "SANS péages"
            print(f"   Segment {i+1}: {toll_status}")
            print(f"     Distance: {seg.get('distance', 0):.1f}km")
            print(f"     Durée: {seg.get('duration', 0):.1f}min")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return False

if __name__ == "__main__":
    success = test_api_with_details()
    print(f"\n🎯 Résultat final: {'✅ SUCCESS' if success else '❌ FAILED'}")
