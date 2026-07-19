from scipy.fft import fft, fftfreq
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error


def fit_sine_waves(timestamps, signal, num_sine_waves=3):
    # Check for NaN or inf
    if np.isnan(timestamps).any() or np.isnan(signal).any() or np.isinf(timestamps).any() or np.isinf(signal).any():
        raise ValueError("Input contains NaN or inf values. Clean the data first.")

    # Find dominant frequencies and amplitudes using FFT
    fs = 1.0 / (timestamps[1] - timestamps[0])
    n = len(signal)
    yf = fft(signal)
    xf = fftfreq(n, 1.0 / fs)[:n // 2]
    magnitudes = np.abs(yf[:n // 2])

    top_indices = np.argsort(magnitudes)[-num_sine_waves:]
    dominant_frequencies = xf[top_indices]
    dominant_magnitudes = magnitudes[top_indices] * 2 / n

    def sine_wave_model(t, *params):
        y = np.zeros_like(t)
        for i in range(0, len(params), 3):
            A, f, phi = params[i], params[i+1], params[i+2]
            y += A * np.sin(2 * np.pi * f * t + phi)
        return y

    initial_guess = []
    for f, mag in zip(dominant_frequencies, dominant_magnitudes):
        initial_guess.extend([mag, f, 0.0])

    bounds = ([-np.inf, f - 1, -np.inf] * len(dominant_frequencies), [np.inf, f + 1, np.inf] * len(dominant_frequencies))

    try:
        params, _ = curve_fit(sine_wave_model, timestamps, signal, p0=initial_guess, bounds=bounds)
    except Exception as e:
        print(f"Error in curve_fit: {e}")
        raise

    fitted_signal = sine_wave_model(timestamps, *params)
    mse = mean_squared_error(signal, fitted_signal)
    rmse = np.sqrt(mse)
    ss_res = np.sum((signal - fitted_signal) ** 2)
    ss_tot = np.sum((signal - np.mean(signal)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    print("\n--- Sine Wave Fit Metrics ---")
    print(f"Mean Squared Error (MSE): {mse:.6f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.6f}")
    print(f"R-squared: {r_squared:.6f}")

    return fitted_signal, params, mse, rmse, r_squared

def analyze_fft(signal, timestamps, num_peaks=5):
    """
    Perform FFT on a signal and return frequencies, magnitudes, and dominant peaks.

    Args:
        signal (np.array): Input signal (e.g., accel_x_mss).
        timestamps (np.array): Time in seconds.
        num_peaks (int): Number of dominant frequency peaks to identify (default: 5).

    Returns:
        tuple: (frequencies, magnitudes, dominant_frequencies, dominant_magnitudes)
    """
    # Sampling rate
    fs = 1.0 / (timestamps[1] - timestamps[0])
    n = len(signal)

    # Compute FFT
    yf = fft(signal)
    xf = fftfreq(n, 1.0 / fs)[:n // 2]  # Only positive frequencies
    magnitudes = np.abs(yf[:n // 2]) * 2 / n  # Normalized magnitude

    # Find dominant frequencies (peaks)
    peaks = np.argsort(magnitudes)[-num_peaks:][::-1]  # Indices of top peaks
    dominant_frequencies = xf[peaks]
    dominant_magnitudes = magnitudes[peaks]

    return xf, magnitudes, dominant_frequencies, dominant_magnitudes
