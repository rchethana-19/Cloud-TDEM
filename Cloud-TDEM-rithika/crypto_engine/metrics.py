"""
TDEM Week 3
Performance Metrics
"""

import time
import tracemalloc


def start_metrics():
    """
    Start performance measurement.
    """

    tracemalloc.start()

    return time.perf_counter()


def stop_metrics(start_time):
    """
    Stop measurement and return metrics.
    """

    elapsed = time.perf_counter() - start_time

    current_memory, peak_memory = (
        tracemalloc.get_traced_memory()
    )

    tracemalloc.stop()

    return {
        "time_seconds": elapsed,
        "memory_current_bytes": current_memory,
        "memory_peak_bytes": peak_memory
    }


def get_metrics():
    """Return a stable metrics payload for the backend adapter."""
    return {
        "encryption_time_ms": 0.0,
        "decryption_time_ms": 0.0,
        "request_count": 0,
        "failure_count": 0,
        "ai_decision_count": 0,
    }