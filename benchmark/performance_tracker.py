"""
Performance tracking system for toll route optimization.
Measures execution times, API calls, and logs performance metrics.
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
import os


@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    operation: str
    duration_ms: float
    timestamp: str
    thread_id: int
    details: Dict[str, Any] = None


@dataclass
class RouteOptimizationSession:
    """Complete session metrics for a route optimization"""
    session_id: str
    start_time: str
    end_time: str
    total_duration_ms: float
    origin: str
    destination: str
    route_distance_km: float
    metrics: List[PerformanceMetric]
    api_calls: Dict[str, int]
    toll_networks: List[str]
    optimization_result: Dict[str, Any]
    errors: List[str] = None


class PerformanceTracker:
    """
    Performance tracking system with file logging and real-time monitoring.
    Thread-safe for concurrent operations.
    """
    
    def __init__(self, log_dir: str = "benchmark/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe storage
        self._lock = threading.Lock()
        self._current_session: Optional[RouteOptimizationSession] = None
        self._metrics: List[PerformanceMetric] = []
        self._api_calls: Dict[str, int] = {}
        self._errors: List[str] = []
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup performance logging configuration"""
        log_file = self.log_dir / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.logger = logging.getLogger('performance_tracker')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler for real-time monitoring
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def start_optimization_session(self, origin: str, destination: str, 
                                 route_distance_km: float = 0) -> str:
        """Start a new route optimization session"""
        with self._lock:
            session_id = f"route_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            self._current_session = RouteOptimizationSession(
                session_id=session_id,
                start_time=datetime.now().isoformat(),
                end_time="",
                total_duration_ms=0,
                origin=origin,
                destination=destination,
                route_distance_km=route_distance_km,
                metrics=[],
                api_calls={},
                toll_networks=[],
                optimization_result={}
            )
            
            # Reset session-specific tracking
            self._metrics = []
            self._api_calls = {}
            self._errors = []
            
            self.logger.info(f"Started optimization session {session_id}: {origin} -> {destination}")
            return session_id
    
    def end_optimization_session(self, result: Dict[str, Any] = None):
        """End the current optimization session and save results"""
        with self._lock:
            if not self._current_session:
                self.logger.warning("No active session to end")
                return
            
            # Calculate total duration
            start_time = datetime.fromisoformat(self._current_session.start_time)
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds() * 1000
            
            # Update session
            self._current_session.end_time = end_time.isoformat()
            self._current_session.total_duration_ms = total_duration
            self._current_session.metrics = self._metrics.copy()
            self._current_session.api_calls = self._api_calls.copy()
            self._current_session.optimization_result = result or {}
            self._current_session.errors = self._errors.copy()
            
            # Save to file
            self._save_session()
            
            # Log summary
            self._log_session_summary()
            
            session_id = self._current_session.session_id
            self._current_session = None
            return session_id
    
    @contextmanager
    def measure_operation(self, operation: str, details: Dict[str, Any] = None):
        """Context manager to measure operation duration with progress info"""
        start_time = time.perf_counter()
        start_timestamp = datetime.now().isoformat()
        
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            metric = PerformanceMetric(
                operation=operation,
                duration_ms=duration_ms,
                timestamp=start_timestamp,
                thread_id=threading.get_ident(),
                details=details or {}
            )
            
            with self._lock:
                self._metrics.append(metric)
            
            # Log avec compteurs API si disponibles
            total_api_calls = sum(self._api_calls.values())
            
            # Log slow operations immediately avec compteurs
            if duration_ms > 5000:  # 5 seconds
                self.logger.warning(f"Slow operation: {operation} took {duration_ms:.2f}ms | Total API calls: {total_api_calls}")
            elif duration_ms > 1000:  # 1 second
                self.logger.info(f"Operation: {operation} took {duration_ms:.2f}ms | Total API calls: {total_api_calls}")

    def count_api_call(self, api_name: str):
        """Increment API call counter with immediate logging"""
        with self._lock:
            self._api_calls[api_name] = self._api_calls.get(api_name, 0) + 1
            total_calls = sum(self._api_calls.values())
        
        # Log tous les 5 appels pour suivre la progression
        if total_calls % 5 == 0:
            self.logger.info(f"🔄 API Progress: {total_calls} total calls | Latest: {api_name} (#{self._api_calls[api_name]})")

    def log_error(self, error_msg: str):
        """Log an error during optimization"""
        with self._lock:
            self._errors.append(f"{datetime.now().isoformat()}: {error_msg}")
        self.logger.error(error_msg)
    
    def set_toll_networks(self, networks: List[str]):
        """Set the toll networks used in current session"""
        if self._current_session:
            self._current_session.toll_networks = networks
    
    def _save_session(self):
        """Save session data to JSON file"""
        if not self._current_session:
            return
        
        filename = f"session_{self._current_session.session_id}.json"
        filepath = self.log_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._current_session), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save session data: {e}")
    
    def _log_session_summary(self):
        """Log a comprehensive summary of the optimization session"""
        if not self._current_session:
            return
        
        session = self._current_session
        total_api_calls = sum(session.api_calls.values())
        
        summary = f"""
🎯 RÉSUMÉ COMPLET - Session {session.session_id}
================================================================
📍 Itinéraire: {session.origin} -> {session.destination}
📏 Distance: {session.route_distance_km:.1f} km
⏱️  Durée totale: {session.total_duration_ms:.2f}ms ({session.total_duration_ms/1000:.1f}s)
🔧 Opérations mesurées: {len(session.metrics)}
🌐 Appels API totaux: {total_api_calls}
🛣️  Réseaux de péage: {', '.join(session.toll_networks) if session.toll_networks else 'Aucun'}
❌ Erreurs: {len(session.errors)}

📊 DÉTAIL DES APPELS API:
"""
    
        if session.api_calls:
            for api, count in sorted(session.api_calls.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_api_calls * 100) if total_api_calls > 0 else 0
                summary += f"   🔗 {api}: {count} appels ({percentage:.1f}%)\n"
        else:
            summary += "   Aucun appel API enregistré\n"
        
        summary += "\n⚡ PERFORMANCE PAR OPÉRATION:\n"
        
        # Group metrics by operation
        operation_stats = {}
        for metric in session.metrics:
            op = metric.operation
            if op not in operation_stats:
                operation_stats[op] = {'count': 0, 'total_ms': 0, 'max_ms': 0, 'min_ms': float('inf')}
            
            operation_stats[op]['count'] += 1
            operation_stats[op]['total_ms'] += metric.duration_ms
            operation_stats[op]['max_ms'] = max(operation_stats[op]['max_ms'], metric.duration_ms)
            operation_stats[op]['min_ms'] = min(operation_stats[op]['min_ms'], metric.duration_ms)
        
        # Sort by total time consumed
        sorted_ops = sorted(operation_stats.items(), key=lambda x: x[1]['total_ms'], reverse=True)
        
        for op, stats in sorted_ops:
            avg_ms = stats['total_ms'] / stats['count']
            percentage = (stats['total_ms'] / session.total_duration_ms * 100) if session.total_duration_ms > 0 else 0
            
            summary += f"   📈 {op}:\n"
            summary += f"      • Exécutions: {stats['count']}x\n"
            summary += f"      • Temps total: {stats['total_ms']:.2f}ms ({percentage:.1f}% du total)\n"
            summary += f"      • Moyenne: {avg_ms:.2f}ms\n"
            summary += f"      • Min/Max: {stats['min_ms']:.2f}ms / {stats['max_ms']:.2f}ms\n\n"
        
        # Performance insights
        summary += "🔍 ANALYSE DE PERFORMANCE:\n"
        
        # Find bottlenecks
        if operation_stats:
            slowest_op = max(operation_stats.items(), key=lambda x: x[1]['max_ms'])
            most_time_consuming = max(operation_stats.items(), key=lambda x: x[1]['total_ms'])
            most_frequent = max(operation_stats.items(), key=lambda x: x[1]['count'])
            
            summary += f"   🐌 Opération la plus lente: {slowest_op[0]} ({slowest_op[1]['max_ms']:.2f}ms)\n"
            summary += f"   ⏰ Plus consommatrice de temps: {most_time_consuming[0]} ({most_time_consuming[1]['total_ms']:.2f}ms total)\n"
            summary += f"   🔄 Plus fréquente: {most_frequent[0]} ({most_frequent[1]['count']} exécutions)\n"
            
            # API call efficiency
            if total_api_calls > 0:
                api_time_per_call = session.total_duration_ms / total_api_calls
                summary += f"   📡 Temps moyen par appel API: {api_time_per_call:.2f}ms\n"
                
                if api_time_per_call > 3000:
                    summary += "   ⚠️  Les appels API sont lents (>3s en moyenne)\n"
                
                if total_api_calls > 100:
                    summary += "   ⚠️  Nombre élevé d'appels API - considérer la mise en cache\n"
        
        if session.errors:
            summary += f"\n❌ ERREURS ({len(session.errors)}):\n"
            for i, error in enumerate(session.errors[-5:], 1):  # Show last 5 errors
                summary += f"   {i}. {error}\n"
            if len(session.errors) > 5:
                summary += f"   ... et {len(session.errors) - 5} autres erreurs\n"
        
        summary += "\n" + "="*80 + "\n"
        
        self.logger.info(summary)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current session statistics with real-time display"""
        with self._lock:
            if not self._current_session:
                return {}
            
            stats = {
                'session_id': self._current_session.session_id,
                'operations_count': len(self._metrics),
                'api_calls': self._api_calls.copy(),
                'errors_count': len(self._errors),
                'elapsed_time_ms': (datetime.now() - datetime.fromisoformat(self._current_session.start_time)).total_seconds() * 1000
            }
            
            # Affichage temps réel des stats importantes
            total_api_calls = sum(self._api_calls.values())
            print(f"\n📊 STATS TEMPS RÉEL:")
            print(f"   Opérations: {len(self._metrics)}")
            print(f"   Appels API: {total_api_calls}")
            for api, count in self._api_calls.items():
                print(f"     - {api}: {count}")
            print(f"   Erreurs: {len(self._errors)}")
            print(f"   Temps écoulé: {stats['elapsed_time_ms']/1000:.1f}s\n")
            
            return stats
    
    def analyze_performance_bottlenecks(self, session_file: str = None) -> Dict[str, Any]:
        """Analyze performance bottlenecks from session data"""
        if session_file:
            with open(self.log_dir / session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        elif self._current_session:
            session_data = asdict(self._current_session)
        else:
            return {}
        
        metrics = session_data.get('metrics', [])
        
        # Analyze bottlenecks
        bottlenecks = {
            'slowest_operations': [],
            'most_frequent_operations': [],
            'api_call_overhead': {},
            'recommendations': []
        }
        
        # Find slowest operations
        sorted_metrics = sorted(metrics, key=lambda x: x['duration_ms'], reverse=True)
        bottlenecks['slowest_operations'] = sorted_metrics[:10]
        
        # Most frequent operations
        op_counts = {}
        for metric in metrics:
            op = metric['operation']
            op_counts[op] = op_counts.get(op, 0) + 1
        
        bottlenecks['most_frequent_operations'] = sorted(
            op_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]
        
        # Generate recommendations
        total_time = session_data.get('total_duration_ms', 0)
        api_calls = sum(session_data.get('api_calls', {}).values())
        
        if api_calls > 50:
            bottlenecks['recommendations'].append("Consider reducing API calls through caching")
        
        if total_time > 30000:  # 30 seconds
            bottlenecks['recommendations'].append("Route optimization is taking too long - consider timeout limits")
        
        return bottlenecks


# Global instance
performance_tracker = PerformanceTracker()
