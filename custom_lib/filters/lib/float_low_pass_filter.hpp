#pragma once

#include "base_iir_filter.hpp"
#include <chrono>

// =============================================================================
// FloatLowPassFilter: Floating-point IIR low-pass filter
// Uses standard floating-point arithmetic, alpha recomputed per sample
// 
// Template parameters:
//   T: floating-point type (double, float)
//   MaxSamples: buffer size for future extensions (currently unused)
// =============================================================================

template<typename T = double, size_t MaxSamples = 1000>
class FloatLowPassFilter : public BaseIIRFilter<T> {
private:
    std::chrono::steady_clock::time_point last_timestamp_;

public:
    explicit FloatLowPassFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : BaseIIRFilter<T>(cutoff_freq_hz, timeout_seconds),
          last_timestamp_(std::chrono::steady_clock::now()) {
        // Base constructor already validates parameters
    }
    
    // Update with new value and timestamp
    T update(T new_value, std::chrono::steady_clock::time_point timestamp) {
        auto current_time = timestamp;
        
        if (this->is_first_call()) {
            this->previous_output_ = new_value;
            last_timestamp_ = current_time;
            return this->previous_output_;
        }
        
        // Compute dt in seconds
        double dt = std::chrono::duration<double>(current_time - last_timestamp_).count();
        
        // Handle edge cases
        if (dt <= 0.0) {
            return this->previous_output_;
        }
        
        // Keep dt reasonable to avoid numerical issues
        if (dt > this->timeout_seconds_) {
            
            this->previous_output_ = new_value;
            last_timestamp_ = current_time;
            return this->previous_output_;
        }
        
        // Compute alpha for this specific dt
        double alpha = this->compute_alpha(dt);
        
        // Apply IIR filter
        this->previous_output_ = this->apply_iir_filter(new_value, alpha);
        
        last_timestamp_ = current_time;
        
        return this->previous_output_;
    }
    
    // Simplified update without explicit timestamp (uses system clock)
    T update(T new_value) {
        return update(new_value, std::chrono::steady_clock::now());
    }
};

// =============================================================================
// Type aliases for commonly used floating-point filter configurations
// =============================================================================

// Floating-point filters
using FloatLowPassFilterDouble = FloatLowPassFilter<double>;
using FloatLowPassFilterFloat = FloatLowPassFilter<float>;
