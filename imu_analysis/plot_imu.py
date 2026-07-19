import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotter import plot_cleaned_vs_original, compare_original_vs_cleaned, plot_sine_wave_fit, plot_fft_spectrum
from cleaner import high_pass_filter, low_pass_filter, uniform_sensor_data, remove_outliers
from fft import analyze_fft, fit_sine_waves


# --- Main Workflow ---
if __name__ == "__main__":

    csv_path = "confidential/sensor_log.csv"
    original_data = pd.read_csv(csv_path)

    # Debug: Check for NaN/inf in original data
    print("NaN in original accel_x_mss:", original_data["accel_x_mss"].isna().any())
    print("Inf in original accel_x_mss:", np.isinf(original_data["accel_x_mss"]).any())

    original_data = uniform_sensor_data(csv_path)
    
    cleaned_data=original_data.copy()

    cleaned_data["accel_x_mss"] = remove_outliers(
        cleaned_data["accel_x_mss"],
        window_size=100,  # Larger window for stable median/std
        threshold=2.0    # Higher threshold to avoid over-removal
    )

    plot_cleaned_vs_original(original_data, cleaned_data, output_path="imu_analysis/pics/"+"original_vs_outlier.png")


    xf, magnitudes, dominant_frequencies, dominant_magnitudes = analyze_fft(cleaned_data["accel_x_mss"], cleaned_data["timestamp_s"], num_peaks=5)

    # Step 2: Print dominant frequencies
    print("Dominant Frequencies (Hz) and Magnitudes:")
    for f, mag in zip(dominant_frequencies, dominant_magnitudes):
        print(f"  {f:.2f} Hz: {mag:.4f}")

    # Step 3: Plot and save FFT spectrum (focus on 0-20 Hz)
    plot_fft_spectrum(
        cleaned_data["accel_x_mss"],
        cleaned_data["timestamp_s"],
        dominant_frequencies,
        dominant_magnitudes,
        max_freq=20,
        save_path="imu_analysis/pics/"+"fft_spectrum.png",  # Save as PNG
    )

    # Debug: Check for NaN/inf in cleaned data
    print("NaN in cleaned accel_x_mss:", cleaned_data["accel_x_mss"].isna().any())
    print("Inf in cleaned accel_x_mss:", np.isinf(cleaned_data["accel_x_mss"]).any())

    filtered_data=cleaned_data.copy()

    filtered_data["accel_x_mss"] = low_pass_filter(cleaned_data["accel_x_mss"], cleaned_data["timestamp_s"], cutoff_freq=4.5, order=5)

    plot_cleaned_vs_original(cleaned_data, filtered_data, output_path="imu_analysis/pics/"+"clean_vs_filtered.png")
    
    metrics = compare_original_vs_cleaned(cleaned_data, filtered_data)
    
    plot_fft_spectrum(
        filtered_data["accel_x_mss"],
        filtered_data["timestamp_s"],
        dominant_frequencies,
        dominant_magnitudes,
        max_freq=20,
        save_path="imu_analysis/pics/"+"fft_spectrum_2.png",  # Save as PNG
    )
    
    # Fit sine waves to cleaned IMU data
    fitted_signal, params, mse, rmse, r_squared = fit_sine_waves(
        filtered_data["timestamp_s"].values,
        filtered_data["accel_x_mss"].values,
        num_sine_waves=5
    )

    # Plot sine wave fit
    plot_sine_wave_fit(
        filtered_data["timestamp_s"].values,
        filtered_data["accel_x_mss"].values,
        fitted_signal,
        output_path="imu_analysis/pics/"+"sine_wave_fit.png"
    )