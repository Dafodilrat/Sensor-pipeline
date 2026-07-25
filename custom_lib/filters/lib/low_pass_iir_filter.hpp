#pragma once

#include <cstddef>
#include <limits>
#include <algorithm>
#include <cmath>
#include <type_traits>
#include <cstdlib>
#include <string>
#include <chrono>
#include <stdexcept>

// =============================================================================
// Low Pass IIR Filter class
// Implements a first-order IIR low-pass filter: output = alpha * input + (1 - alpha) * output_previous
// Optionally resets on timeout when time gap between samples exceeds threshold
// =============================================================================

template<typename T>
class LowPassIIRFilter {
protected:
    T output_ = 0.0;
    T alpha_ = 0.0;
    T cutoff_freq_ = 0.0;
    double last_dt_ = 0.0;
    
    // Timeout functionality
    double timeout_seconds_;
    std::chrono::steady_clock::time_point last_update_time_;
    bool first_update_ = true;

    template <typename U>
    U applyRounding(double value) const {
        if constexpr (std::is_integral_v<U>) {
            double sign = (value < 0.0) ? -1.0 : 1.0;
            double abs_value = std::abs(value);
            double intpart;
            double fracpart = std::modf(abs_value, &intpart);
            double rounded_abs_value;

            if (fracpart > 0.5) {
                rounded_abs_value = std::ceil(abs_value);
            } else if (fracpart == 0.5) {
                rounded_abs_value = (rand() % 2 == 0) ? std::ceil(abs_value) : std::floor(abs_value);
            } else {
                rounded_abs_value = intpart;
            }
            return static_cast<U>(rounded_abs_value * sign);
        } else {
            return static_cast<U>(value);
        }
    }
    
    // Calculate alpha from cutoff frequency and dt (time between samples)
    void computeAlpha(double dt) {
        if (cutoff_freq_ > 0.0 && dt > 0.0) {
            double rc = 1.0 / (2.0 * M_PI * cutoff_freq_);
            alpha_ = dt / (rc + dt);
        } else {
            alpha_ = 0.0;
        }
    }
    
    // Validate timeout value
    static void validate_timeout(double timeout_seconds) {
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
    }

    // Validate cutoff frequency
    static void validate_cutoff(double cutoff_freq) {
        if (cutoff_freq <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
    }

public:
    // Constructor with cutoff frequency and optional timeout
    // timeout_seconds = -1.0 means no timeout (default behavior)
    explicit LowPassIIRFilter(double cutoff_freq, double timeout_seconds = -1.0) 
        : cutoff_freq_(cutoff_freq),
          timeout_seconds_(timeout_seconds) {
        validate_cutoff(cutoff_freq);
        if (timeout_seconds > 0.0) {
            validate_timeout(timeout_seconds);
        }
    }

    virtual ~LowPassIIRFilter() = default;

    virtual T update(T new_value) {
        auto now = std::chrono::steady_clock::now();
        
        // Calculate time since last update
        if (first_update_) {
            last_update_time_ = now;
            first_update_ = false;
        } else {
            last_dt_ = std::chrono::duration<double>(now - last_update_time_).count();
            
            // Check for timeout
            if (timeout_seconds_ > 0.0 && last_dt_ > timeout_seconds_) {
                reset();
                return update(new_value); // Recursively call after reset
            }
        }
        last_update_time_ = now;

        // Compute alpha based on current cutoff and actual dt
        computeAlpha(last_dt_);
        
        // Apply IIR low-pass filter: output = alpha * input + (1 - alpha) * output_previous
        double input = static_cast<double>(new_value);
        output_ = alpha_ * input + (1.0 - alpha_) * output_;
        
        if constexpr (std::is_integral_v<T>) {
            return applyRounding<T>(output_);
        } else {
            return static_cast<T>(output_);
        }
    }
    
    virtual void reset() {
        output_ = 0.0;
        last_dt_ = 0.0;
        first_update_ = true;  // Reset first update flag so next update initializes timestamp
    }
    
    // Set cutoff frequency (will be used to compute alpha on next update)
    void set_cutoff(double cutoff_freq) {
        validate_cutoff(cutoff_freq);
        cutoff_freq_ = cutoff_freq;
    }
    
    // Get current cutoff frequency
    double get_cutoff() const {
        return cutoff_freq_;
    }

    // Get the last dt (time between samples)
    double get_last_dt() const {
        return last_dt_;
    }

    // Get current alpha value
    double get_alpha() const {
        return alpha_;
    }
    
    // Set timeout for reset on large dt gaps
    // timeout_seconds = -1.0 disables timeout
    void set_timeout(double timeout_seconds) {
        if (timeout_seconds > 0.0) {
            validate_timeout(timeout_seconds);
        }
        timeout_seconds_ = timeout_seconds;
    }
    
    // Get current timeout value
    // Returns -1.0 if timeout is disabled
    double get_timeout() const {
        return timeout_seconds_;
    }
    
    // Check if timeout is enabled
    bool has_timeout() const {
        return timeout_seconds_ > 0.0;
    }
};

// Type aliases for floating-point versions
using LowPassFilterDouble = LowPassIIRFilter<double>;
using LowPassFilterFloat = LowPassIIRFilter<float>;
