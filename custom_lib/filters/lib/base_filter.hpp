#pragma once

#include <cstddef>
#include <limits>
#include <algorithm>
#include <cmath>
#include <type_traits>
#include <stdexcept>
#include <chrono>

// =============================================================================
// BaseFilter: Abstract base class for all filters
// Provides common functionality: cutoff frequency, timeout, RC calculation, alpha computation
// =============================================================================

template<typename T>
class BaseFilter {
protected:
    double cutoff_freq_hz_;
    double timeout_seconds_;
    bool first_call_;
    
    // RC time constant: rc = 1 / (2 * pi * cutoff_freq)
    double compute_rc() const {
        return 1.0 / (2.0 * M_PI * cutoff_freq_hz_);
    }
    
    // Compute alpha from dt: alpha = dt / (rc + dt)
    // Returns alpha clamped to [0, 1] for numerical robustness
    double compute_alpha(double dt) const {
        if (cutoff_freq_hz_ <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        double rc = compute_rc();
        double alpha = dt / (rc + dt);
        return std::clamp(alpha, 0.0, 1.0);
    }
    
    // Validate timeout value
    static void validate_timeout(double timeout_seconds) {
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
    }
    
    // Validate cutoff frequency value
    static void validate_cutoff_frequency(double cutoff_freq_hz) {
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
    }

public:
    // Constructor with cutoff frequency and timeout
    explicit BaseFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : cutoff_freq_hz_(cutoff_freq_hz),
          timeout_seconds_(timeout_seconds),
          first_call_(true) {
        validate_cutoff_frequency(cutoff_freq_hz);
        validate_timeout(timeout_seconds);
    }
    
    virtual ~BaseFilter() = default;
    
    // Reset filter state - to be implemented by derived classes
    virtual void reset() = 0;
    
    // Set new cutoff frequency
    void set_cutoff_frequency(double cutoff_freq_hz) {
        validate_cutoff_frequency(cutoff_freq_hz);
        cutoff_freq_hz_ = cutoff_freq_hz;
    }
    
    // Get current cutoff frequency
    double get_cutoff_frequency() const {
        return cutoff_freq_hz_;
    }
    
    // Set timeout for reset on large dt gaps
    void set_timeout(double timeout_seconds) {
        validate_timeout(timeout_seconds);
        timeout_seconds_ = timeout_seconds;
    }
    
    // Get current timeout value
    double get_timeout() const {
        return timeout_seconds_;
    }
    
    // Check if this is the first call and mark as complete
    // Returns true if this was the first call, false otherwise
    bool is_first_call() {
        if (first_call_) {
            first_call_ = false;
            return true;
        }
        return false;
    }
};
