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

    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage during calculations."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss
        
        # Memory usage during calculations
        memory_samples = []
        
        for i in range(100):
            # Perform calculations
            self.engine.calc_ev(0.6, 2.0)
            self.engine.calc_poisson(1.5, 1.2, 6)
            
            # Sample memory every 10 iterations
            if i % 10 == 0:
                memory_samples.append(process.memory_info().rss)
        
        gc.collect()
        final_memory = process.memory_info().rss
        
        return {
            "baseline_memory_mb": baseline_memory / 1024 / 1024,
            "final_memory_mb": final_memory / 1024 / 1024,
            "peak_memory_mb": max(memory_samples) / 1024 / 1024,
            "memory_growth_mb": (final_memory - baseline_memory) / 1024 / 1024,
            "memory_leak_detected": (final_memory - baseline_memory) > 10 * 1024 * 1024  # 10MB threshold
        }
    
    def benchmark_concurrent_load(self, concurrent_requests: int = 50) -> Dict[str, Any]:
        """Benchmark concurrent load performance."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker():
            latencies = []
            for _ in range(10):  # 10 calculations per thread
                start = time.perf_counter()
                self.engine.calc_ev(0.6, 2.0)
                latencies.append((time.perf_counter() - start) * 1000)
            results_queue.put(latencies)
        
        # Start concurrent threads
        threads = []
        start_time = time.perf_counter()
        
        for _ in range(concurrent_requests):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.perf_counter() - start_time
        
        # Collect all latencies
        all_latencies = []
        while not results_queue.empty():
            all_latencies.extend(results_queue.get())
        
        return {
            "concurrent_requests": concurrent_requests,
            "total_calculations": len(all_latencies),
            "total_time_seconds": total_time,
            "throughput_per_second": len(all_latencies) / total_time,
            "mean_latency_ms": statistics.mean(all_latencies),
            "p95_latency_ms": statistics.quantiles(all_latencies, n=20)[18],
            "p99_latency_ms": statistics.quantiles(all_latencies, n=100)[98],
            "max_latency_ms": max(all_latencies)
        }

def run_ci_benchmarks() -> int:
    """Run comprehensive benchmarks for CI/CD pipeline. Returns exit code."""
    benchmark = EngineBenchmark()
    
    print("=== BetFlow Engine v0.9.0 CI Benchmark Suite ===")
    print()
    
    # SLO compliance check
    slo_results = benchmark.check_slo_compliance()
    print("1. SLO Compliance Check:")
    print(f"   Overall SLO Compliant: {slo_results['slo_compliant']}")
    
    ev = slo_results['ev_benchmark']
    print(f"   EV Calculation - P95: {ev['p95_ms']:.3f}ms, P99: {ev['p99_ms']:.3f}ms")
    
    poisson = slo_results['poisson_benchmark']
    print(f"   Poisson Calculation - P95: {poisson['p95_ms']:.3f}ms, P99: {poisson['p99_ms']:.3f}ms")
    print()
    
    # Memory usage benchmark
    try:
        memory_results = benchmark.benchmark_memory_usage()
        print("2. Memory Usage Analysis:")
        print(f"   Baseline Memory: {memory_results['baseline_memory_mb']:.1f}MB")
        print(f"   Peak Memory: {memory_results['peak_memory_mb']:.1f}MB")
        print(f"   Memory Growth: {memory_results['memory_growth_mb']:.1f}MB")
        print(f"   Memory Leak Detected: {memory_results['memory_leak_detected']}")
        print()
    except Exception as e:
        print(f"2. Memory Usage Analysis: FAILED - {e}")
        print()
    
    # Concurrent load benchmark
    try:
        load_results = benchmark.benchmark_concurrent_load(25)
        print("3. Concurrent Load Test (25 threads):")
        print(f"   Throughput: {load_results['throughput_per_second']:.1f} calc/sec")
        print(f"   Mean Latency: {load_results['mean_latency_ms']:.3f}ms")
        print(f"   P95 Latency: {load_results['p95_latency_ms']:.3f}ms")
        print(f"   P99 Latency: {load_results['p99_latency_ms']:.3f}ms")
        print()
    except Exception as e:
        print(f"3. Concurrent Load Test: FAILED - {e}")
        print()
    
    # Batch performance benchmark
    try:
        batch_results = benchmark.benchmark_batch_ev([1000, 10000])
        print("4. Batch Performance Test:")
        for batch_name, results in batch_results.items():
            print(f"   {batch_name}: {results['throughput_per_sec']:.0f} calc/sec, P95: {results['p95_ms']:.1f}ms")
        print()
    except Exception as e:
        print(f"4. Batch Performance Test: FAILED - {e}")
        print()
    
    # Health check
    health = slo_results['health_check']
    print("5. Engine Health Status:")
    print(f"   Status: {health['status']}")
    print(f"   Use Mojo: {health['use_mojo']}")
    print(f"   Mojo Available: {health['mojo_available']}")
    print(f"   Version: {health['version']}")
    print()
    
    # Final assessment
    print("=== CI Benchmark Results ===")
    
    # Check for failures
    failures = []
    if not slo_results['slo_compliant']:
        failures.append("SLO compliance failed")
    
    try:
        if memory_results['memory_leak_detected']:
            failures.append("Memory leak detected")
    except:
        failures.append("Memory analysis failed")
    
    if health['status'] != 'healthy':
        failures.append("Engine health check failed")
    
    if failures:
        print(f"❌ FAILED: {', '.join(failures)}")
        return 1
    else:
        print("✅ PASSED: All benchmarks meet requirements")
        return 0

if __name__ == "__main__":
    exit(run_ci_benchmarks())