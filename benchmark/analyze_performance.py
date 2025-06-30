#!/usr/bin/env python3
"""
Analyse des performances SAM
============================

Script d'exemple pour analyser les logs et sessions de performance du backend SAM.
Utilise les données générées par le PerformanceTracker.
"""

import json
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def analyze_daily_performance(log_dir: str = "benchmark/logs"):
    """
    Analyse les performances quotidiennes du système SAM.
    
    Args:
        log_dir: Répertoire contenant les logs de performance
    """
    log_path = Path(log_dir)
    
    # Trouver tous les fichiers de session JSON
    session_files = list(log_path.glob("session_route_*.json"))
    
    if not session_files:
        print("❌ Aucune session trouvée")
        return
    
    print(f"📊 Analyse de {len(session_files)} sessions d'optimisation")
    print("=" * 60)
    
    # Statistiques globales
    total_sessions = len(session_files)
    total_duration = 0
    total_api_calls = 0
    error_count = 0
    
    # Statistiques par opération
    operation_stats = {}
    api_call_stats = {}
    
    # Analyser chaque session
    for session_file in session_files:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session = json.load(f)
            
            # Statistiques globales
            total_duration += session.get('total_duration_ms', 0)
            session_api_calls = sum(session.get('api_calls', {}).values())
            total_api_calls += session_api_calls
            error_count += len(session.get('errors', []))
            
            # Analyser les métriques
            for metric in session.get('metrics', []):
                op = metric['operation']
                duration = metric['duration_ms']
                
                if op not in operation_stats:
                    operation_stats[op] = {
                        'count': 0,
                        'total_duration': 0,
                        'max_duration': 0,
                        'min_duration': float('inf')
                    }
                
                operation_stats[op]['count'] += 1
                operation_stats[op]['total_duration'] += duration
                operation_stats[op]['max_duration'] = max(operation_stats[op]['max_duration'], duration)
                operation_stats[op]['min_duration'] = min(operation_stats[op]['min_duration'], duration)
            
            # Analyser les appels API
            for api, count in session.get('api_calls', {}).items():
                api_call_stats[api] = api_call_stats.get(api, 0) + count
                
        except Exception as e:
            print(f"⚠️ Erreur lors de l'analyse de {session_file.name}: {e}")
            continue
    
    # Afficher les résultats
    print(f"🚀 Sessions totales: {total_sessions}")
    print(f"⏱️ Temps total: {total_duration/1000:.1f}s")
    print(f"📞 Appels API totaux: {total_api_calls}")
    print(f"❌ Erreurs totales: {error_count}")
    print(f"📈 Temps moyen par session: {total_duration/total_sessions/1000:.1f}s")
    print(f"📊 API calls par session: {total_api_calls/total_sessions:.1f}")
    
    print("\n🔍 TOP 10 - Opérations les plus chronophages:")
    print("-" * 50)
    
    # Trier par durée totale
    sorted_ops = sorted(
        operation_stats.items(), 
        key=lambda x: x[1]['total_duration'], 
        reverse=True
    )
    
    for i, (op, stats) in enumerate(sorted_ops[:10], 1):
        avg_duration = stats['total_duration'] / stats['count']
        percentage = (stats['total_duration'] / total_duration * 100)
        
        print(f"{i:2d}. {op}")
        print(f"    🔄 {stats['count']}x exécutions")
        print(f"    ⏱️ {stats['total_duration']:.0f}ms total ({percentage:.1f}%)")
        print(f"    📊 {avg_duration:.1f}ms moyenne")
        print(f"    📈 {stats['min_duration']:.1f}ms → {stats['max_duration']:.1f}ms")
        print()
    
    print("📞 Répartition des appels API:")
    print("-" * 30)
    
    for api, count in sorted(api_call_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_api_calls * 100) if total_api_calls > 0 else 0
        print(f"  {api}: {count} ({percentage:.1f}%)")
    
    # Recommandations
    print(f"\n💡 Recommandations:")
    print("-" * 20)
    
    avg_session_time = total_duration / total_sessions if total_sessions > 0 else 0
    
    if avg_session_time > 5000:  # 5 secondes
        print("  ⚠️ Temps d'optimisation élevé - considérer l'optimisation des algorithmes")
    
    if total_api_calls / total_sessions > 10:
        print("  📞 Nombre d'appels API élevé - considérer la mise en cache")
    
    if error_count > 0:
        print(f"  ❌ {error_count} erreurs détectées - vérifier les logs détaillés")
    
    # Identifier les opérations les plus lentes
    slowest_op = max(operation_stats.items(), key=lambda x: x[1]['max_duration'])
    if slowest_op[1]['max_duration'] > 10000:  # 10 secondes
        print(f"  🐌 Opération très lente détectée: {slowest_op[0]} ({slowest_op[1]['max_duration']:.0f}ms)")


def analyze_specific_session(session_file: str):
    """
    Analyse détaillée d'une session spécifique.
    
    Args:
        session_file: Chemin vers le fichier JSON de session
    """
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {session_file}: {e}")
        return
    
    print(f"🔍 Analyse détaillée - {session['session_id']}")
    print("=" * 60)
    
    # Informations générales
    print(f"📍 Route: {session['origin']} → {session['destination']}")
    print(f"📏 Distance: {session['route_distance_km']:.1f} km")
    print(f"⏱️ Durée totale: {session['total_duration_ms']:.0f}ms")
    print(f"🔄 Opérations: {len(session['metrics'])}")
    print(f"📞 Appels API: {sum(session['api_calls'].values())}")
    print(f"❌ Erreurs: {len(session.get('errors', []))}")
    
    # Timeline des opérations
    print(f"\n📅 Timeline des opérations:")
    print("-" * 40)
    
    start_time = datetime.fromisoformat(session['start_time'])
    
    for i, metric in enumerate(session['metrics'], 1):
        op_time = datetime.fromisoformat(metric['timestamp'])
        elapsed = (op_time - start_time).total_seconds()
        
        print(f"{i:2d}. +{elapsed:6.2f}s | {metric['operation']:25} | {metric['duration_ms']:8.1f}ms")
    
    # Appels API
    if session['api_calls']:
        print(f"\n📞 Détail des appels API:")
        print("-" * 25)
        for api, count in session['api_calls'].items():
            print(f"  {api}: {count}x")
    
    # Erreurs
    if session.get('errors'):
        print(f"\n❌ Erreurs rencontrées:")
        print("-" * 20)
        for error in session['errors']:
            print(f"  • {error}")
    
    # Résultat d'optimisation
    if session.get('optimization_result'):
        result = session['optimization_result']
        print(f"\n🎯 Résultat d'optimisation:")
        print("-" * 25)
        print(f"  Statut: {result.get('status', 'N/A')}")
        
        if 'fastest' in result:
            fastest = result['fastest']
            print(f"  Route rapide: {fastest.get('duration', 0)/3600:.1f}h, {fastest.get('cost', 0):.2f}€")
        
        if 'cheapest' in result:
            cheapest = result['cheapest']
            print(f"  Route économique: {cheapest.get('duration', 0)/3600:.1f}h, {cheapest.get('cost', 0):.2f}€")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Analyser une session spécifique
        session_file = sys.argv[1]
        analyze_specific_session(session_file)
    else:
        # Analyse globale
        analyze_daily_performance()
