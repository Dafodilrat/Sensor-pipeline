#!/usr/bin/env python3
"""
ROS-agnostic Python script to visualize sensor data with moving average filters.

Loads CSV data from sensor_log.csv, applies BOTH fixed window and time duration 
moving average filters from the custom py_moving_average library, and creates 
four plots in a single figure:
- Fixed Window MA: IMU acceleration (raw vs filtered)
- Fixed Window MA: Encoder counts (raw vs filtered)
- Time Duration MA: IMU acceleration (raw vs filtered)
- Time Duration MA: Encoder counts (raw vs filtered)

Both filters use the same window size and timeout. Time Duration MA has an 
additional duration parameter.

Usage:
    python visualize_sensor_data.py
    
    # With custom parameters
    python visualize_sensor_data.py --csv /path/to/sensor_log.csv \
        --window-size 20 --timeout 0.1 --time-duration 50.0

Requirements:
    - py_moving_average library must be built and available in PYTHONPATH
    - matplotlib, numpy, pandas
"""

import argparse
import sys
import os
from datetime import timedelta

# Add custom lib to path if not already there
custom_lib_path = os.path.join(os.path.dirname(__file__), 'custom_lib')
if os.path.exists(custom_lib_path):
    sys.path.insert(0, custom_lib_path)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def load_csv_data(csv_path):
    """Load sensor data from CSV file."""
    df = pd.read_csv(csv_path)
    
    # Validate required columns
    required_cols = ['timestamp_s', 'encoder_count', 'accel_x_mss']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")
    
    return df


def apply_fixed_moving_averages(data, window_size=20, timeout_seconds=0.1):
    """
    Apply fixed window moving average filters to encoder and IMU data.
    
    Args:
        data: DataFrame with 'encoder_count', 'accel_x_mss', 'timestamp_s' columns
        window_size: Size of the moving average window
        timeout_seconds: Timeout for filter reset on data dropouts
    
    Returns:
        Dict with filtered encoder and acceleration data
    """
    try:
        from py_moving_average.FixedMovingAverage.mediumbuffer import Integer as MA_Int
        from py_moving_average.FixedMovingAverage.mediumbuffer import Double as MA_Double
    except ImportError as e:
        # Try alternative import paths
        try:
            import py_moving_average
            MA_Int = py_moving_average.FixedMovingAverage.mediumbuffer.Integer
            MA_Double = py_moving_average.FixedMovingAverage.mediumbuffer.Double
        except (ImportError, AttributeError) as e2:
            raise ImportError(
                f"Failed to import py_moving_average library. "
                f"Ensure it's built and in PYTHONPATH. Error: {e2}"
            ) from e2
    
    # Initialize filters
    ma_encoder = MA_Int(window_size, timeout_seconds)
    ma_accel = MA_Double(window_size, timeout_seconds)
    
    # Apply filters to each data point
    encoder_values = data['encoder_count'].values
    accel_values = data['accel_x_mss'].values
    timestamps = data['timestamp_s'].values
    
    filtered_encoder = []
    filtered_accel = []
    
    for i, (enc_val, acc_val, ts) in enumerate(zip(encoder_values, accel_values, timestamps)):
        # Convert numpy types to native Python types for the filter
        enc_val = int(enc_val)
        acc_val = float(acc_val)
        
        # Update filters and get results
        filtered_enc = ma_encoder.update(enc_val)
        filtered_acc = ma_accel.update(acc_val)
        
        filtered_encoder.append(filtered_enc)
        filtered_accel.append(filtered_acc)
    
    return {
        'timestamp_s': timestamps,
        'encoder_raw': encoder_values,
        'encoder_filtered': np.array(filtered_encoder),
        'accel_raw': accel_values,
        'accel_filtered': np.array(filtered_accel)
    }


def apply_time_moving_averages(data, window_size=100, window_duration_ms=50.0, timeout_seconds=0.1):
    """
    Apply time duration moving average filters to encoder and IMU data.
    
    Args:
        data: DataFrame with 'encoder_count', 'accel_x_mss', 'timestamp_s' columns
        window_size: Size of the window
        window_duration_ms: Duration of the time window in milliseconds
        timeout_seconds: Timeout for filter reset on data dropouts
    
    Returns:
        Dict with time-based filtered encoder and acceleration data
    """
    try:
        from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Integer as TD_MA_Int
        from py_moving_average.TimeDurationMovingAverage.mediumbuffer import Double as TD_MA_Double
    except ImportError as e:
        # Try alternative import paths
        try:
            import py_moving_average
            TD_MA_Int = py_moving_average.TimeDurationMovingAverage.mediumbuffer.Integer
            TD_MA_Double = py_moving_average.TimeDurationMovingAverage.mediumbuffer.Double
        except (ImportError, AttributeError) as e2:
            raise ImportError(
                f"Failed to import py_moving_average library. "
                f"Ensure it's built and in PYTHONPATH. Error: {e2}"
            ) from e2
    
    # Initialize time-based filters
    window_duration = timedelta(milliseconds=window_duration_ms)
    td_ma_encoder = TD_MA_Int(window_size, window_duration, timeout_seconds)
    td_ma_accel = TD_MA_Double(window_size, window_duration, timeout_seconds)
    
    # Apply filters to each data point
    encoder_values = data['encoder_count'].values
    accel_values = data['accel_x_mss'].values
    timestamps = data['timestamp_s'].values
    
    filtered_encoder = []
    filtered_accel = []
    
    for i, (enc_val, acc_val, ts) in enumerate(zip(encoder_values, accel_values, timestamps)):
        # Convert numpy types to native Python types for the filter
        enc_val = int(enc_val)
        acc_val = float(acc_val)
        
        # Update filters and get results
        filtered_enc = td_ma_encoder.update(enc_val)
        filtered_acc = td_ma_accel.update(acc_val)
        
        filtered_encoder.append(filtered_enc)
        filtered_accel.append(filtered_acc)
    
    return {
        'timestamp_s': timestamps,
        'encoder_raw': encoder_values,
        'encoder_filtered': np.array(filtered_encoder),
        'accel_raw': accel_values,
        'accel_filtered': np.array(filtered_accel)
    }


def create_plots(fixed_results, time_results, window_size=20, timeout=0.1, 
                  time_duration_ms=50.0):
    """Create plots showing raw vs filtered data for both Fixed and Time Duration MA.
    
    Creates 4 subplots:
    - Fixed Window MA: IMU Acceleration
    - Fixed Window MA: Encoder Counts  
    - Time Duration MA: IMU Acceleration
    - Time Duration MA: Encoder Counts
    
    Args:
        fixed_results: Results from fixed window MA filter
        time_results: Results from time duration MA filter
        window_size: Window size used for both filters
        timeout: Timeout used for both filters
        time_duration_ms: Duration in milliseconds for time duration filter
    """
    fig = plt.figure(figsize=(16, 14))
    fig.suptitle(
        f'Sensor Data: Fixed Window MA vs Time Duration MA (window={window_size}, duration={time_duration_ms}ms, timeout={timeout}s)',
        fontsize=16,
        fontweight='bold'
    )
    
    # Use GridSpec for 4 subplots
    gs = GridSpec(4, 1, figure=fig, height_ratios=[1, 1, 1, 1])
    
    # Plot 1: Fixed Window MA - IMU Acceleration
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(fixed_results['timestamp_s'], fixed_results['accel_raw'], 
             label='Raw IMU (accel_x_mss)', 
             alpha=0.7, 
             linewidth=1.5,
             color='tab:blue')
    ax1.plot(fixed_results['timestamp_s'], fixed_results['accel_filtered'], 
             label=f'Fixed MA (window={window_size})', 
             linewidth=2,
             color='tab:orange')
    ax1.set_xlabel('Time (s)', fontsize=11)
    ax1.set_ylabel('Acceleration (m/s²)', fontsize=11)
    ax1.set_title('IMU X-Axis Acceleration - Fixed Window Moving Average', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    ax1.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot 2: Fixed Window MA - Encoder Counts
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(fixed_results['timestamp_s'], fixed_results['encoder_raw'], 
             label='Raw Encoder Counts', 
             alpha=0.7, 
             linewidth=1.5,
             color='tab:green')
    ax2.plot(fixed_results['timestamp_s'], fixed_results['encoder_filtered'], 
             label=f'Fixed MA (window={window_size})', 
             linewidth=2,
             color='tab:red')
    ax2.set_xlabel('Time (s)', fontsize=11)
    ax2.set_ylabel('Encoder Count', fontsize=11)
    ax2.set_title('Encoder Wheel Counts - Fixed Window Moving Average', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot 3: Time Duration MA - IMU Acceleration
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.plot(time_results['timestamp_s'], time_results['accel_raw'], 
             label='Raw IMU (accel_x_mss)', 
             alpha=0.7, 
             linewidth=1.5,
             color='tab:blue')
    ax3.plot(time_results['timestamp_s'], time_results['accel_filtered'], 
             label=f'Time MA (window={window_size}, duration={time_duration_ms}ms)', 
             linewidth=2,
             color='tab:purple')
    ax3.set_xlabel('Time (s)', fontsize=11)
    ax3.set_ylabel('Acceleration (m/s²)', fontsize=11)
    ax3.set_title('IMU X-Axis Acceleration - Time Duration Moving Average', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)
    ax3.tick_params(axis='both', which='major', labelsize=9)
    
    # Plot 4: Time Duration MA - Encoder Counts
    ax4 = fig.add_subplot(gs[3, 0])
    ax4.plot(time_results['timestamp_s'], time_results['encoder_raw'], 
             label='Raw Encoder Counts', 
             alpha=0.7, 
             linewidth=1.5,
             color='tab:green')
    ax4.plot(time_results['timestamp_s'], time_results['encoder_filtered'], 
             label=f'Time MA (window={window_size}, duration={time_duration_ms}ms)', 
             linewidth=2,
             color='tab:brown')
    ax4.set_xlabel('Time (s)', fontsize=11)
    ax4.set_ylabel('Encoder Count', fontsize=11)
    ax4.set_title('Encoder Wheel Counts - Time Duration Moving Average', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=9)
    ax4.tick_params(axis='both', which='major', labelsize=9)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.94, hspace=0.4)
    
    return fig


def main():
    parser = argparse.ArgumentParser(
        description='Visualize sensor data with moving average filters'
    )
    parser.add_argument(
        '--csv', 
        type=str, 
        default=os.path.join(os.path.dirname(__file__), 'confidential', 'sensor_log.csv'),
        help='Path to sensor log CSV file (default: confidential/sensor_log.csv)'
    )
    parser.add_argument(
        '--window-size', 
        type=int, 
        default=100,
        help='Window size for both filters (default: 100)'
    )
    parser.add_argument(
        '--timeout', 
        type=float, 
        default=0.1,
        help='Timeout in seconds for both filters (default: 0.1)'
    )
    parser.add_argument(
        '--time-duration', 
        type=float, 
        default=50.0,
        help='Time duration in milliseconds for Time Duration MA filter (default: 50.0)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='sensor_data_with_ma.png',
        help='Output image file path (default: sensor_data_with_ma.png)'
    )
    parser.add_argument(
        '--dpi', 
        type=int, 
        default=150,
        help='DPI for saved images'
    )
    parser.add_argument(
        '--show', 
        action='store_true',
        help='Show interactive plot instead of saving'
    )
    
    args = parser.parse_args()
    
    print(f"Loading data from: {args.csv}")
    print(f"Window size: {args.window_size}")
    print(f"Timeout: {args.timeout}s")
    print(f"Time Duration: {args.time_duration}ms")
    print("-" * 60)
    
    # Load data
    try:
        data = load_csv_data(args.csv)
        print(f"Loaded {len(data)} samples")
        print(f"Time range: {data['timestamp_s'].min():.2f}s to {data['timestamp_s'].max():.2f}s")
        print(f"Encoder range: {data['encoder_count'].min()} to {data['encoder_count'].max()}")
        print(f"Acceleration range: {data['accel_x_mss'].min():.3f} to {data['accel_x_mss'].max():.3f}")
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        sys.exit(1)
    
    window_size = args.window_size
    timeout = args.timeout
    time_duration = args.time_duration
    
    # Apply fixed window moving average filters
    try:
        print("\nApplying Fixed Window moving average filters...")
        fixed_results = apply_fixed_moving_averages(data, window_size, timeout)
        print("Fixed MA filters applied successfully")
    except Exception as e:
        print(f"Error applying fixed MA filters: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Apply time duration moving average filters
    try:
        print("\nApplying Time Duration moving average filters...")
        time_results = apply_time_moving_averages(data, window_size, time_duration, timeout)
        print("Time MA filters applied successfully")
    except Exception as e:
        print(f"Error applying time MA filters: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create plots
    print("\nCreating visualization...")
    fig = create_plots(fixed_results, time_results, window_size, timeout, time_duration)
    
    # Save or show
    if args.show:
        plt.show()
    else:
        fig.savefig(args.output, dpi=args.dpi, bbox_inches='tight')
        print(f"Saved plot to: {args.output}")
    
    plt.close(fig)


if __name__ == '__main__':
    main()
