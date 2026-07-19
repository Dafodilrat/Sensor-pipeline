import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

from sklearn.metrics import r2_score


def compare_original_vs_cleaned(original_data, cleaned_data):
    """
    Compare original and cleaned data by calculating:
    - Mean, Standard Deviation (std), Min, Max
    - R-squared (R²) error between original and cleaned signals.

    Args:
        original_data (pd.DataFrame): Original data with columns: timestamp_s, accel_x_mss, encoder_count.
        cleaned_data (pd.DataFrame): Cleaned data with the same columns.

    Returns:
        dict: A dictionary containing all calculated metrics.
    """
    # --- IMU Data (accel_x_mss) ---
    original_imu = original_data["accel_x_mss"].values
    cleaned_imu = cleaned_data["accel_x_mss"].values

    # Calculate metrics for IMU
    imu_metrics = {
        "original_mean": np.mean(original_imu),
        "original_std": np.std(original_imu),
        "original_min": np.min(original_imu),
        "original_max": np.max(original_imu),
        "cleaned_mean": np.mean(cleaned_imu),
        "cleaned_std": np.std(cleaned_imu),
        "cleaned_min": np.min(cleaned_imu),
        "cleaned_max": np.max(cleaned_imu),
        "r_squared": r2_score(original_imu, cleaned_imu),
    }

    # --- Encoder Data (encoder_count) ---
    original_encoder = original_data["encoder_count"].values
    cleaned_encoder = cleaned_data["encoder_count"].values

    # Calculate metrics for encoder
    encoder_metrics = {
        "original_mean": np.mean(original_encoder),
        "original_std": np.std(original_encoder),
        "original_min": np.min(original_encoder),
        "original_max": np.max(original_encoder),
        "cleaned_mean": np.mean(cleaned_encoder),
        "cleaned_std": np.std(cleaned_encoder),
        "cleaned_min": np.min(cleaned_encoder),
        "cleaned_max": np.max(cleaned_encoder),
        "r_squared": r2_score(original_encoder, cleaned_encoder),
    }

    # --- Print Report ---
    print("\n=== Original vs. Cleaned Data Report ===")
    print("\n--- IMU Data (accel_x_mss) ---")
    print(f"Original - Mean: {imu_metrics['original_mean']:.6f}, Std: {imu_metrics['original_std']:.6f}, Min: {imu_metrics['original_min']:.6f}, Max: {imu_metrics['original_max']:.6f}")
    print(f"Cleaned  - Mean: {imu_metrics['cleaned_mean']:.6f}, Std: {imu_metrics['cleaned_std']:.6f}, Min: {imu_metrics['cleaned_min']:.6f}, Max: {imu_metrics['cleaned_max']:.6f}")
    print(f"R-squared (IMU): {imu_metrics['r_squared']:.6f}")

    print("\n--- Encoder Data (encoder_count) ---")
    print(f"Original - Mean: {encoder_metrics['original_mean']:.6f}, Std: {encoder_metrics['original_std']:.6f}, Min: {encoder_metrics['original_min']:.6f}, Max: {encoder_metrics['original_max']:.6f}")
    print(f"Cleaned  - Mean: {encoder_metrics['cleaned_mean']:.6f}, Std: {encoder_metrics['cleaned_std']:.6f}, Min: {encoder_metrics['cleaned_min']:.6f}, Max: {encoder_metrics['cleaned_max']:.6f}")
    print(f"R-squared (Encoder): {encoder_metrics['r_squared']:.6f}")

    # Return metrics as a dictionary
    return {
        "imu": imu_metrics,
        "encoder": encoder_metrics,
    }

def plot_cleaned_vs_original(original_data, cleaned_data, output_path="cleaned_vs_original.png"):
    plt.figure(figsize=(14, 8))

    # Plot IMU data
    plt.subplot(2, 1, 1)
    plt.plot(original_data["timestamp_s"], original_data["accel_x_mss"], label="Original IMU", color="blue", alpha=0.7)
    plt.plot(cleaned_data["timestamp_s"], cleaned_data["accel_x_mss"], label="Cleaned IMU", color="red", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Acceleration (m/s²)")
    plt.title("Original vs. Cleaned IMU Data")
    plt.legend()
    plt.grid(True)

    # Plot encoder data
    plt.subplot(2, 1, 2)
    plt.plot(original_data["timestamp_s"], original_data["encoder_count"], label="Original Encoder", color="green", alpha=0.7)
    plt.plot(cleaned_data["timestamp_s"], cleaned_data["encoder_count"], label="Cleaned Encoder", color="orange", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Encoder Count")
    plt.title("Original vs. Cleaned Encoder Data")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    

def plot_sine_wave_fit(timestamps, cleaned_signal, fitted_signal, output_path="sine_wave_fit.png"):
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, cleaned_signal, label="Cleaned IMU Signal", color="blue", alpha=0.7)
    plt.plot(timestamps, fitted_signal, label="Fitted Sine Waves", color="red", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Acceleration (m/s²)")
    plt.title("Cleaned IMU Signal vs. Fitted Sine Waves")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    

def plot_fft_spectrum(
    timestamps,
    signal,
    dominant_frequencies=None,
    dominant_magnitudes=None,
    max_freq=None,
    save_path="fft_spectrum.png",
):
    """
    Plot the FFT magnitude spectrum and save as an image.

    Args:
        timestamps (np.array): Time in seconds.
        signal (np.array): Input signal (e.g., accel_x_mss).
        dominant_frequencies (np.array): Frequencies of dominant peaks.
        dominant_magnitudes (np.array): Magnitudes of dominant peaks.
        max_freq (float): Maximum frequency to display (default: Nyquist frequency).
        save_path (str): Path to save the plot (default: "fft_spectrum.png").
        show_plot (bool): Whether to display the plot (default: True).
    """
    fs = 1.0 / (timestamps[1] - timestamps[0])
    n = len(signal)

    # Compute FFT
    yf = fft(signal)
    xf = fftfreq(n, 1.0 / fs)[:n // 2]
    magnitudes = np.abs(yf[:n // 2]) * 2 / n

    # Set max frequency for x-axis
    if max_freq is None:
        max_freq = fs / 2  # Nyquist frequency

    # Create plot
    plt.figure(figsize=(12, 6))
    plt.plot(xf, magnitudes, label="FFT Magnitude", color="blue", alpha=0.7)

    # Highlight dominant frequencies
    if dominant_frequencies is not None:
        for f, mag in zip(dominant_frequencies, dominant_magnitudes):
            plt.axvline(x=f, color="red", linestyle="--", alpha=0.7)
            plt.text(f, mag + 0.05 * np.max(magnitudes), f"{f:.2f} Hz", color="red", ha="center")

    plt.title("FFT Magnitude Spectrum (IMU Data)")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.xlim(0, max_freq)
    plt.legend()

    # Save the plot
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    print(f"Plot saved to: {save_path}")