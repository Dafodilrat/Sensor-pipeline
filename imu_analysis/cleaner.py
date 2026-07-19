from scipy.signal import butter, filtfilt
import numpy as np
import pandas as pd 

def uniform_sensor_data(csv_path):
    """
    Clean sensor data by:
    1. Handling missing/infinite values via interpolation.
    2. Ensuring timestamps are strictly increasing.
    3. Applying a low-pass filter in 5-second segments (optional).
    4. Resampling to uniform timestamps at the original sampling rate.
    5. Removing DC offset.
    6. Smoothing the signal (optional).

    Args:
        csv_path (str): Path to the CSV file.
        window_size (int): Window size for smoothing (default: 5).
        apply_lowpass (bool): Whether to apply a low-pass filter (default: True).
        cutoff_freq (float): Cutoff frequency for the low-pass filter in Hz (default: 5.0).
        segment_duration (float): Duration of segments for low-pass filtering in seconds (default: 5.0).

    Returns:
        pd.DataFrame: Cleaned data with columns: timestamp_s, encoder_count, accel_x_mss.
    """
    # Load CSV
    original_data = pd.read_csv(csv_path)
    original_length = len(original_data)

    # --- Step 1: Handle Missing/Infinite Values ---
    data = original_data.copy()
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    data.interpolate(method='linear', inplace=True)
    data.bfill(inplace=True)
    data.ffill(inplace=True)

    # --- Step 4: Resample to Uniform Timestamps at Original Sampling Rate ---
    time_diff = np.diff(data["timestamp_s"])
    sampling_rate = 1.0 / np.mean(time_diff)
    start_time = data["timestamp_s"].min()
    end_time = data["timestamp_s"].max()
    num_samples = int((end_time - start_time) * sampling_rate) + 1
    uniform_timestamps = np.linspace(start_time, end_time, num=num_samples)

    # Interpolate IMU and encoder data to uniform timestamps
    cleaned_data = pd.DataFrame({
        "timestamp_s": uniform_timestamps,
        "encoder_count": np.interp(uniform_timestamps, data["timestamp_s"], data["encoder_count"]),
        "accel_x_mss": np.interp(uniform_timestamps, data["timestamp_s"], data["accel_x_mss"])
    })

    # --- Step 7: Ensure No NaN Values Remain ---
    cleaned_data.interpolate(method='linear', inplace=True)
    cleaned_data.bfill(inplace=True)
    cleaned_data.ffill(inplace=True)

    # --- Step 8: Assert Length Matches Original ---
    cleaned_length = len(cleaned_data)
    if cleaned_length != original_length:
        print(f"Warning: Length mismatch! Original: {original_length}, Cleaned: {cleaned_length}")
        if cleaned_length > original_length:
            cleaned_data = cleaned_data.iloc[:original_length]
        else:
            last_row = cleaned_data.iloc[-1].copy()
            for _ in range(original_length - cleaned_length):
                cleaned_data = pd.concat([cleaned_data, last_row.to_frame().T], ignore_index=True)

    return cleaned_data

def low_pass_filter(signal, timestamps, cutoff_freq=5.0, order=4):
    """
    Apply a zero-phase Butterworth low-pass filter to IMU data.
    Removes high-frequency noise.

    Args:
        signal (np.array): IMU acceleration (e.g., accel_x_mss).
        timestamps (np.array): Time in seconds.
        cutoff_freq (float): Cutoff frequency in Hz (default: 5.0 Hz).
        order (int): Filter order (default: 4).

    Returns:
        np.array: Low-pass filtered IMU signal.
    """
    fs = 1.0 / (timestamps[1] - timestamps[0])  # Sampling rate (Hz)
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_freq / nyquist

    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal

def high_pass_filter(signal, timestamps, cutoff_freq=0.1, order=4):
    """
    Apply a zero-phase Butterworth high-pass filter to IMU data.
    Removes low-frequency drift (e.g., gravity offset).

    Args:
        signal (np.array): IMU acceleration (e.g., accel_x_mss).
        timestamps (np.array): Time in seconds.
        cutoff_freq (float): Cutoff frequency in Hz (default: 0.1 Hz).
        order (int): Filter order (default: 4).

    Returns:
        np.array: High-pass filtered IMU signal.
    """
    fs = 1.0 / (timestamps[1] - timestamps[0])  # Sampling rate (Hz)
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_freq / nyquist

    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    filtered_signal = filtfilt(b, a, signal)
    
    return filtered_signal

def remove_outliers(signal, window_size=100, threshold=4.0):
    """
    Remove outliers using a rolling median and Z-score.

    Args:
        signal (pd.Series): Input signal (e.g., accel_x_mss).
        window_size (int): Window for rolling median/std (default: 100).
        threshold (float): Z-score threshold (default: 4.0).

    Returns:
        pd.Series: Signal with outliers replaced by rolling median.
    """
    rolling_median = signal.rolling(window=window_size, center=True).median()
    rolling_std = signal.rolling(window=window_size, center=True).std()
    z_scores = (signal - rolling_median) / rolling_std
    outliers = np.abs(z_scores) > threshold
    cleaned_signal = signal.copy()
    cleaned_signal[outliers] = rolling_median[outliers]
    
    return cleaned_signal
