"""
Benchmark suite for BetFlow Engine performance testing.
Used in CI/CD pipeline to ensure SLO compliance.
"""

import time
import statistics
from typing import List, Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import BetFlowEngine

class EngineBenchmark:
    """Benchmark suite for engine performance testing."""

    def __init__(self):
        self.engine = BetFlowEngine()

    def benchmark_ev_calculation(self, n_iterations: int = 1000) -> Dict[str, float]:
        """Benchmark EV calculation performance."""
        latencies = []

        for _ in range(n_iterations):
            start = time.perf_counter()
            ev = self.engine.calc_ev(0.6, 2.0)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to milliseconds

        return {
            "mean_ms": statistics.mean(latencies),
            "p50_ms": statistics.median(latencies),
            "p95_ms": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            "p99_ms": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "n_iterations": n_iterations
        }

    def benchmark_poisson_calculation(self, n_iterations: int = 100) -> Dict[str, float]:
        """Benchmark Poisson calculation performance."""
        latencies = []

        for _ in range(n_iterations):
            start = time.perf_counter()
            probs = self.engine.calc_poisson(1.5, 1.2, max_goals=6)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        return {
            "mean_ms": statistics.mean(latencies),
            "p50_ms": statistics.median(latencies),
            "p95_ms": statistics.quantiles(latencies, n=20)[18],
            "p99_ms": statistics.quantiles(latencies, n=100)[98],
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "n_iterations": n_iterations
        }

    def benchmark_batch_ev(self, batch_sizes: List[int] = [1000, 10000, 100000]) -> Dict[str, Dict[str, float]]:
        """Benchmark batch EV calculations."""
        results = {}

        for batch_size in batch_sizes:
            latencies = []

            for _ in range(5):  # Run 5 times for each batch size
                start = time.perf_counter()
                for i in range(batch_size):
                    ev = self.engine.calc_ev(0.6, 2.0)
                end = time.perf_counter()
                latencies.append((end - start) * 1000)

            results[f"batch_{batch_size}"] = {
                "mean_ms": statistics.mean(latencies),
                "p95_ms": statistics.quantiles(latencies, n=20)[18],
                "throughput_per_sec": batch_size / (statistics.mean(latencies) / 1000)
            }

        return results

    def check_slo_compliance(self) -> Dict[str, Any]:
        """Check if current performance meets SLO requirements."""
        ev_bench = self.benchmark_ev_calculation()
        poisson_bench = self.benchmark_poisson_calculation()

        slo_checks = {
            "ev_p95_slo": ev_bench["p95_ms"] < 1.0,  # < 1ms
            "ev_p99_slo": ev_bench["p99_ms"] < 5.0,  # < 5ms
            "poisson_p95_slo": poisson_bench["p95_ms"] < 1.0,  # < 1ms
            "poisson_p99_slo": poisson_bench["p99_ms"] < 5.0,  # < 5ms
        }

        return {
            "slo_compliant": all(slo_checks.values()),
            "slo_checks": slo_checks,
            "ev_benchmark": ev_bench,
            "poisson_benchmark": poisson_bench,
            "health_check": self.engine.health_check()
        }

def run_ci_benchmarks() -> int:
    """Run benchmarks for CI/CD pipeline. Returns exit code."""
    benchmark = EngineBenchmark()
    results = benchmark.check_slo_compliance()

    print("=== BetFlow Engine SLO Compliance Check ===")
    print(f"SLO Compliant: {results['slo_compliant']}")
    print()

    print("EV Calculation Performance:")
    ev = results['ev_benchmark']
    print(f"  P95: {ev['p95_ms']:.3f}ms (SLO: <1.0ms)")
    print(f"  P99: {ev['p99_ms']:.3f}ms (SLO: <5.0ms)")
    print()

    print("Poisson Calculation Performance:")
    poisson = results['poisson_benchmark']
    print(f"  P95: {poisson['p95_ms']:.3f}ms (SLO: <1.0ms)")
    print(f"  P99: {poisson['p99_ms']:.3f}ms (SLO: <5.0ms)")
    print()

    print("Health Check:")
    health = results['health_check']
    print(f"  Status: {health['status']}")
    print(f"  Use Mojo: {health['use_mojo']}")
    print(f"  Mojo Available: {health['mojo_available']}")

    # Return 0 if SLO compliant, 1 if not
    return 0 if results['slo_compliant'] else 1

if __name__ == "__main__":
    exit(run_ci_benchmarks())