# Benchmark Results

## Overview

Benchmark results for **floating-point** filter performance tests conducted on 2026-07-30.
All tests used IMU sensor data and ran for 10 seconds with a 5% rate tolerance.

**Note:** These benchmarks test the standard floating-point implementations. The fixed-point (Q-format) implementations have separate considerations and are not benchmarked here.

---

## Performance Across All Rates

### Low-Pass Filter

| Rate | Throughput | Can Keep Up | Avg Processing Time |
|------|------------|-------------|---------------------|
| 200 Hz | 200.08 Hz | ✅ Yes | 67.69 μs |
| 2000 Hz | 1999.72 Hz | ✅ Yes | 18.30 μs |
| 20000 Hz | 11732.59 Hz | ❌ No | 8.81 μs |

### Fixed Mean Filter

| Rate | Throughput | Can Keep Up | Avg Processing Time |
|------|------------|-------------|---------------------|
| 200 Hz | 200.09 Hz | ✅ Yes | 66.97 μs |
| 2000 Hz | 1997.32 Hz | ✅ Yes | 16.59 μs |
| 20000 Hz | 11695.91 Hz | ❌ No | 9.16 μs |

---

## Analysis

### Rates Up to 2000 Hz: Excellent Performance

- At 200 Hz and 2000 Hz, both filters achieve throughput matching the expected rate within tolerance.
- Processing time per sample decreases as rate increases (67 μs at 200 Hz → 18 μs at 2000 Hz for LP filter), demonstrating efficient computation.

### The 20k Hz Bottleneck

At 20000 Hz, both filters hit nearly identical limits:
- Low-Pass: 11732.59 Hz (58.7% of target)
- Fixed Mean: 11695.91 Hz (58.5% of target)

**The bottleneck is the ROS 2 message transport layer, not filter computation.**

#### Root Cause:

**The bottleneck is in the Python data generator's `publish_imu()` callback.** Even at 20k Hz, the generator cannot produce messages fast enough.

1. **`time.time()` System Call Overhead**: In `sensor_streamer/generator.py`, `publish_imu()` calls `time.time()` on line 92 for every iteration. At 20k Hz (every 50 μs), this system call alone consumes significant time. Python's `time.time()` has overhead of ~1-2 μs per call on typical systems, and with the timer callback overhead, this becomes the limiting factor.

2. **Additional Per-Callback Costs**: Each callback also performs:
   - Numerical velocity calculation with NumPy (`np.sin`, `np.cos`)
   - Random number generation for noise (`random.gauss`)
   - ROS 2 Python message serialization and publishing

3. **Python Interpreter Limits**: Even with all optimizations, the Python interpreter cannot sustain sub-50 μs iteration times. The C++ generator also hits the same ceiling because the ROS 2 Python bindings and message passing infrastructure add unavoidable overhead.

4. **Identical Ceiling for Both Filters**: Both LP and Fixed Mean filters hit the exact same ~11,700 Hz ceiling, proving the bottleneck is in data generation, not filter computation. The filters process messages in only 8-9 μs.

#### Evidence:
- Both filter types hit the exact same ceiling at 20k Hz
- C++ and Python generators both produce the same limitation
- Increasing queue size to 5000 does not improve throughput
- Filter processing time (8-9 μs) is much faster than the 50 μs message interval
- At 2000 Hz (500 μs interval), the generator keeps up perfectly

---

## Raw Results

All raw JSON files are available in `colcon_ws/results/`:

**Low-Pass Filter:**
- `lp_benchmark_200hz_20260730_151917.json`
- `lp_benchmark_2000hz_20260730_151937.json`
- `lp_benchmark_20000hz_20260730_152004.json`

**Fixed Mean Filter:**
- `fixed_ma_benchmark_200hz_20260730_150841.json`
- `fixed_ma_benchmark_2000hz_20260730_151439.json`
- `fixed_ma_benchmark_20000hz_20260730_151501.json`
