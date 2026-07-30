# Data Analysis & Filter Justification

This section provides the technical justification for our filter choices based on real sensor data analysis from the provided `sensor_log.csv` file.

## Overview

Using ~60 seconds of real logged data from a rotary encoder + IMU accel channel at nominally 200 Hz, we performed FFT-based analysis to characterize the signal's frequency content and optimize our filter parameters.

## Data Preprocessing

Before analysis, raw sensor data is cleaned using `cleaner.py`:

1. **`uniform_sensor_data()`** performs the core preprocessing:
   - **Handle Missing/Infinite Values**: Replaces ±∞ with NaN, then applies linear interpolation, backward fill, and forward fill
   - **Resample to Uniform Timestamps**: Calculates the original sampling rate from timestamp differences, creates a uniform timestamp array spanning the full time range, and uses `np.interp` to interpolate both `encoder_count` and `accel_x_mss` to these uniform timestamps
   - **Final NaN Check**: Additional interpolation (linear, bfill, ffill) to ensure no NaN values remain
   - **Length Matching**: Ensures output length matches the original data length

2. **Outlier Removal** (`remove_outliers()`): Uses rolling median with window size of 100 samples and Z-score threshold of 4.0 to detect and replace anomalous spikes with the rolling median value.

3. **FFT Analysis** (`fft.py`): Computes the FFT magnitude spectrum and identifies the top 5 dominant frequency components.

## Analysis Results

**Statistical Analysis of IMU Data (accel_x_mss):**

| Metric | Original | Cleaned (Outliers Removed) | Interpretation |
|--------|----------|----------------------------|----------------|
| Mean | 0.046602 | 0.046003 | DC offset preserved |
| Std Dev | 0.986848 | 0.446237 | **54.7% noise reduction** |
| Min | -1.999020 | -1.855290 | Outliers clipped |
| Max | 1.778781 | 1.807450 | Range preserved |
| R² vs Original | - | 0.248318 | Low correlation confirms significant noise content |

**Encoder Data (encoder_count):**

| Metric | Original | Cleaned | Interpretation |
|--------|----------|--------|----------------|
| Mean | 618056.475526 | 618056.475526 | Identical |
| Std Dev | 353924.967740 | 353924.967740 | Identical |
| Min | 0.000000 | 0.000000 | Identical |
| Max | 1233229.000000 | 1233229.000000 | Identical |
| R² vs Original | - | 1.000000 | Perfect match — encoder data is clean |

### Dominant Frequencies from FFT Analysis

The FFT magnitude spectrum analysis of the IMU acceleration data revealed clear frequency components:

![FFT Spectrum Analysis](imu_analysis/pics/fft_spectrum.png)

| Frequency (Hz) | Normalized Magnitude | Interpretation |
|----------------|---------------------|----------------|
| **1.17 Hz** | Highest peak | **Primary rotary motion** component (the fundamental rotation frequency) |
| **5.14 Hz** | Moderate peak | **First harmonic** of the primary motion (approximately 4.4× the fundamental) |
| **5.95 Hz** | Moderate peak | Close to the first harmonic, likely a related motion component |
| **8.54 Hz** | Moderate peak | **Second harmonic** of the primary motion (approximately 7.3× the fundamental) |
| **11.90 Hz** | Lower peak | Begins the **noise floor** region |
| >12 Hz | Very low magnitude | Confirmed **noise floor** |

## Design Decisions from Analysis

### Cutoff Frequency Selection: 7.0 Hz

Based on the FFT results, we selected **7.0 Hz** as the optimal cutoff frequency for our IMU low-pass filters. This choice:
- **Preserves the signal**: Primary (1.17 Hz) and both first harmonics (5.14 Hz, 5.95 Hz) pass through with minimal attenuation
- **Attenuates the noise**: The second harmonic (8.54 Hz) and all higher frequencies are significantly reduced
- **Provides optimal separation**: ~1.5 Hz margin between the last signal component (5.95 Hz) and first noise component (8.54 Hz), avoiding ringing while maintaining signal integrity

The **54.7% reduction in standard deviation** after outlier removal confirms substantial high-frequency noise content in the original IMU data, validating our filtering approach.

### Timeout Configuration: 150ms

The `sensor_log.csv` data contains a ~150ms dropout gap. This value is used as the timeout for all filters to ensure proper behavior during real-world signal interruptions.

### Filter Application

- **IMU (acceleration)**: Requires LP filtering (7.0 Hz cutoff) + moving average filters
- **Encoder (count)**: Only moving average filters applied — encoder data is clean and requires no LP filtering

## Filter Behavior Across Dropout Gap

Our filter implementations handle the ~150ms dropout gap as follows:

### Moving Average Filters
Both `FixedMovingAverage` and `TimeDurationMovingAverage` implement timeout-based reset:
- When the time gap between samples exceeds 150ms, the filter **resets its internal buffer and sum**
- With no explicit timeout: The filter continues processing and treats the gap as an extended dt (samples outside the window are naturally expired)

### Low-Pass Filters
The IIR filters compute alpha dynamically from the actual dt. When a large dt (150ms) occurs:
- `alpha = dt / (rc + dt)` where `rc = 1/(2π·7.0)` ≈ 22.76ms
- With dt = 150ms: `alpha ≈ 150/(22.76+150) ≈ 0.87`, meaning the filter heavily weights the new input (87%) and only 13% of the previous state
- This effectively "catches up" to the new value quickly rather than smoothing it excessively
- This prevents the filter from maintaining stale state across the gap

![Dropout Gap Analysis](imu_analysis/pics/dropout_gap_analysis.png)

The dropout gap analysis plot shows how filters handle the ~150ms gap, with the LP filter dynamically adjusting alpha based on the extended dt.

Additionally, the before/after filtering comparison for IMU is shown below:

![Before/After Filtering](imu_analysis/pics/imu_all_filters_comparison.png)

This comparison shows the LP filter (7 Hz cutoff) effectively preserves the primary signal while attenuating high-frequency noise. The moving average filters also demonstrate good noise reduction with different latency characteristics.

## Evidence Files

All analysis results are available in the `imu_analysis/` directory:

- `fft.py` — FFT analysis and sine wave fitting code
- `cleaner.py` — Data cleaning: handles missing values, uniform resampling, outlier removal

- `plotter.py` — Visualization functions
- `plot_from_pickle.py` — Main analysis and plotting script
- `process_with_custom_filters.py` — Data processing with custom filters (simulates real-time with actual dt sleep)

### Generated Plots in `pics/`:
- `fft_spectrum.png` — Dominant frequency identification
- `fft_spectrum_2.png` — FFT after filtering
- `imu_all_filters_comparison.png` — IMU: Original vs LP, MA, and TD MA filters
- `encoder_ma_filters_comparison.png` — Encoder: Original vs MA and TD MA filters
- `dropout_gap_analysis.png` — Filter behavior across the ~150ms dropout gap
- `filter_errors_imu.png` — Absolute error comparison for IMU filters
