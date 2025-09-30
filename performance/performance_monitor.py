"""
Performance Monitoring Module for CNFund System
Tracks and reports performance metrics for optimization
"""

import time
import functools
from datetime import datetime
from typing import Dict, Any, Callable
import streamlit as st

class PerformanceMonitor:
    """Monitor and track application performance metrics"""

    def __init__(self):
        self.metrics = {}
        self.session_start = time.time()

    def track_time(self, operation_name: str):
        """Decorator to track execution time of functions"""
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self._record_metric(operation_name, duration, 'success')
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self._record_metric(operation_name, duration, 'error')
                    raise e
            return wrapper
        return decorator

    def _record_metric(self, operation: str, duration: float, status: str):
        """Record a performance metric"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'success_count': 0,
                'error_count': 0,
                'history': []
            }

        metric = self.metrics[operation]
        metric['count'] += 1
        metric['total_time'] += duration
        metric['avg_time'] = metric['total_time'] / metric['count']
        metric['min_time'] = min(metric['min_time'], duration)
        metric['max_time'] = max(metric['max_time'], duration)

        if status == 'success':
            metric['success_count'] += 1
        else:
            metric['error_count'] += 1

        # Keep last 100 measurements
        metric['history'].append({
            'timestamp': datetime.now(),
            'duration': duration,
            'status': status
        })
        if len(metric['history']) > 100:
            metric['history'].pop(0)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics"""
        return self.metrics

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        total_operations = sum(m['count'] for m in self.metrics.values())
        total_time = sum(m['total_time'] for m in self.metrics.values())
        session_duration = time.time() - self.session_start

        return {
            'session_duration': session_duration,
            'total_operations': total_operations,
            'total_time': total_time,
            'operations': len(self.metrics),
            'avg_operation_time': total_time / total_operations if total_operations > 0 else 0
        }

    def render_dashboard(self):
        """Render performance dashboard in Streamlit"""
        st.subheader("📊 Performance Monitoring Dashboard")

        summary = self.get_summary()

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Session Duration", f"{summary['session_duration']:.1f}s")
        with col2:
            st.metric("Total Operations", summary['total_operations'])
        with col3:
            st.metric("Tracked Functions", summary['operations'])
        with col4:
            st.metric("Avg Operation Time", f"{summary['avg_operation_time']*1000:.1f}ms")

        # Detailed metrics
        if self.metrics:
            st.subheader("Operation Details")

            for operation, data in sorted(self.metrics.items(),
                                         key=lambda x: x[1]['avg_time'],
                                         reverse=True):
                with st.expander(f"🔍 {operation}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Call Count:** {data['count']}")
                        st.write(f"**Success Rate:** {data['success_count']/data['count']*100:.1f}%")

                    with col2:
                        st.write(f"**Avg Time:** {data['avg_time']*1000:.1f}ms")
                        st.write(f"**Min Time:** {data['min_time']*1000:.1f}ms")

                    with col3:
                        st.write(f"**Max Time:** {data['max_time']*1000:.1f}ms")
                        st.write(f"**Total Time:** {data['total_time']:.2f}s")

                    # Recent history
                    if data['history']:
                        recent = data['history'][-10:]
                        times = [h['duration']*1000 for h in recent]
                        st.line_chart(times)

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def track_performance(operation_name: str):
    """Decorator to track function performance"""
    monitor = get_performance_monitor()
    return monitor.track_time(operation_name)

# Context manager for manual tracking
class PerformanceTimer:
    """Context manager for tracking code block performance"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.monitor = get_performance_monitor()

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = 'success' if exc_type is None else 'error'
        self.monitor._record_metric(self.operation_name, duration, status)
        return False

# Streamlit specific performance tracking
def track_streamlit_render(func):
    """Track Streamlit component render time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with PerformanceTimer(f"render_{func.__name__}"):
            return func(*args, **kwargs)
    return wrapper

# Cache performance tracking
def track_cache_performance():
    """Monitor Streamlit cache hit/miss rates"""
    if 'cache_stats' not in st.session_state:
        st.session_state.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_time': 0
        }
    return st.session_state.cache_stats

def record_cache_hit(duration: float):
    """Record a cache hit"""
    stats = track_cache_performance()
    stats['hits'] += 1
    stats['total_time'] += duration

def record_cache_miss(duration: float):
    """Record a cache miss"""
    stats = track_cache_performance()
    stats['misses'] += 1
    stats['total_time'] += duration

def get_cache_hit_rate() -> float:
    """Get cache hit rate percentage"""
    stats = track_cache_performance()
    total = stats['hits'] + stats['misses']
    return (stats['hits'] / total * 100) if total > 0 else 0

# Page load time tracking
def track_page_load():
    """Track page load time"""
    if 'page_load_start' not in st.session_state:
        st.session_state.page_load_start = time.time()
        st.session_state.page_loads = []

    # Record load time on first render
    if len(st.session_state.page_loads) == 0:
        load_time = time.time() - st.session_state.page_load_start
        st.session_state.page_loads.append({
            'timestamp': datetime.now(),
            'duration': load_time
        })

        # Track in performance monitor
        monitor = get_performance_monitor()
        monitor._record_metric('page_load', load_time, 'success')

def get_average_page_load() -> float:
    """Get average page load time"""
    if 'page_loads' not in st.session_state or not st.session_state.page_loads:
        return 0

    loads = st.session_state.page_loads
    return sum(l['duration'] for l in loads) / len(loads)

# Performance baseline establishment
def establish_baseline():
    """Establish performance baseline for comparison"""
    baseline = {
        'timestamp': datetime.now(),
        'app_start_time': time.time(),
        'initial_load': None,
        'operations': {}
    }

    if 'performance_baseline' not in st.session_state:
        st.session_state.performance_baseline = baseline

    return st.session_state.performance_baseline

def compare_to_baseline() -> Dict[str, Any]:
    """Compare current performance to baseline"""
    if 'performance_baseline' not in st.session_state:
        return {'status': 'no_baseline', 'message': 'No baseline established'}

    baseline = st.session_state.performance_baseline
    monitor = get_performance_monitor()
    current_metrics = monitor.get_metrics()

    comparison = {
        'timestamp': datetime.now(),
        'improvements': [],
        'regressions': [],
        'new_operations': []
    }

    for op_name, current_data in current_metrics.items():
        if op_name in baseline['operations']:
            baseline_avg = baseline['operations'][op_name]['avg_time']
            current_avg = current_data['avg_time']

            if current_avg < baseline_avg:
                improvement = (baseline_avg - current_avg) / baseline_avg * 100
                comparison['improvements'].append({
                    'operation': op_name,
                    'improvement': improvement,
                    'baseline': baseline_avg,
                    'current': current_avg
                })
            elif current_avg > baseline_avg:
                regression = (current_avg - baseline_avg) / baseline_avg * 100
                comparison['regressions'].append({
                    'operation': op_name,
                    'regression': regression,
                    'baseline': baseline_avg,
                    'current': current_avg
                })
        else:
            comparison['new_operations'].append(op_name)

    return comparison