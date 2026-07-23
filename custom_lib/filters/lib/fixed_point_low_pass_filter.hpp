#pragma once

#include "base_filter.hpp"
#include "../../../external/fpm/include/fpm/fixed.hpp"
#include <cstddef>
#include <limits>
#include <algorithm>
#include <cmath>
#include <chrono>

// =============================================================================
// FixedPointLowPassFilter: Integer-only low-pass filter implementation
//
// Uses fixed-point arithmetic via fpm library to avoid floating-point operations
// in the update path.
// Implements: output = alpha * input + (1 - alpha) * previous_output
// where alpha = dt / (rc + dt) and rc = 1 / (2 * pi * cutoff_freq)
//
// Fixed-point scheme:
// - Use Q-format via fpm::fixed with configurable fractional bits
// - All multiplications use fpm's built-in Q-format arithmetic
// - Rounding: round to nearest (controlled by fpm's EnableRounding template param)
// - Saturation: clamps to T range to prevent silent overflow
//
// Template parameters:
//   T: Integer type for storage (int32_t, int64_t)
//   CalcT: Integer type for intermediate calculations (default: wider type than T)
//
// The fractional bits can be configured via the constructor parameter.
// Default: 16 fractional bits for int32_t (Q16.16), 32 for int64_t (Q32.32)
// =============================================================================

template<typename T, typename CalcT = std::int64_t, int FractionalBits = (sizeof(T) == 4 ? 16 : 32)>
class FixedPointLowPassFilter : public BaseFilter<T> {
private:
    using FixedType = fpm::fixed<T, CalcT, FractionalBits>;
    
    FixedType previous_output_q_;
    double rc_;  // Precomputed RC time constant
    int fractional_bits_;
    
    std::chrono::steady_clock::time_point last_timestamp_;
    
    // Compute alpha in Q-format from dt
    FixedType compute_alpha_q(double dt) const {
        if (dt <= 0.0) return FixedType(0);
        if (dt >= rc_ * 1000.0) return FixedType(1);
        
        double alpha = dt / (rc_ + dt);
        // Clamp to [0, 1] for numerical robustness
        alpha = std::clamp(alpha, 0.0, 1.0);
        return FixedType(alpha);
    }
    
    // Saturating conversion from T to FixedType
    FixedType to_q_sat(T value, bool* is_clamped = nullptr) const {
        FixedType result(value);
        T raw = result.raw_value();
        
        // Check for overflow
        FixedType max_val = FixedType::from_raw_value(std::numeric_limits<T>::max());
        FixedType min_val = FixedType::from_raw_value(std::numeric_limits<T>::min());
        
        if (value > 0 && raw == std::numeric_limits<T>::max() && 
            static_cast<double>(FixedType::from_raw_value(raw)) < static_cast<double>(value)) {
            if (is_clamped) *is_clamped = true;
            return max_val;
        } else if (value < 0 && raw == std::numeric_limits<T>::min() &&
                   static_cast<double>(FixedType::from_raw_value(raw)) > static_cast<double>(value)) {
            if (is_clamped) *is_clamped = true;
            return min_val;
        }
        
        if (is_clamped) *is_clamped = false;
        return result;
    }

public:
    // Constructor: cutoff_freq_hz is the cutoff frequency in Hz
    // fractional_bits determines the Q-format precision
    // For T=int32_t: default 16 (Q16.16), for T=int64_t: default 32 (Q32.32)
    // timeout_seconds is the max dt before reset
    explicit FixedPointLowPassFilter(
        double cutoff_freq_hz, 
        int fractional_bits = FractionalBits, 
        double timeout_seconds = 10.0
    ) : BaseFilter<T>(cutoff_freq_hz, timeout_seconds),
        previous_output_q_(FixedType(0)),
        rc_(1.0 / (2.0 * M_PI * cutoff_freq_hz)),
        fractional_bits_(fractional_bits),
        last_timestamp_(std::chrono::steady_clock::now()) {
        // Base constructor already validates parameters
    }
    
    // Update with integer value and timestamp
    // If is_clamped !== nullptr, sets *is_clamped to true if clamping occurred
    T update(T new_value, std::chrono::steady_clock::time_point timestamp, bool* is_clamped = nullptr) {
        
        auto current_time = timestamp;
        bool local_clamped = false;
        bool* clamped_ptr = is_clamped ? is_clamped : &local_clamped;
        
        if (this->is_first_call()) {
            previous_output_q_ = to_q_sat(new_value, clamped_ptr);
            last_timestamp_ = current_time;
            if (is_clamped) *is_clamped = local_clamped;
            return new_value;
        }
        
        // Compute dt in seconds
        double dt = std::chrono::duration<double>(current_time - last_timestamp_).count();
        
        if (dt <= 0.0) {
            if (is_clamped) *is_clamped = false;
            return static_cast<T>(std::round(static_cast<double>(previous_output_q_)));
        }
        
        if (dt > this->timeout_seconds_) {
            previous_output_q_ = to_q_sat(new_value, clamped_ptr);
            last_timestamp_ = current_time;
            if (is_clamped) *is_clamped = local_clamped;
            return new_value;
        }
        
        // Compute alpha and (1-alpha) in Q-format
        FixedType alpha_q = compute_alpha_q(dt);
        FixedType one_minus_alpha_q = FixedType(1) - alpha_q;
        
        // Convert input to Q-format
        FixedType input_q = to_q_sat(new_value, clamped_ptr);
        
        // Apply IIR filter in fixed-point using fpm's built-in operators
        // output_q = alpha_q * input_q + (1 - alpha_q) * previous_output_q
        FixedType term1 = alpha_q * input_q;
        FixedType term2 = one_minus_alpha_q * previous_output_q_;
        FixedType output_q = term1 + term2;
        
        previous_output_q_ = output_q;
        last_timestamp_ = current_time;
        
        if (is_clamped) *is_clamped = local_clamped;
        return static_cast<T>(std::round(static_cast<double>(output_q)));
    }
    
    // Simplified update without explicit timestamp (uses system clock)
    T update(T new_value) {
        return update(new_value, std::chrono::steady_clock::now(), nullptr);
    }
    
    // Simplified update with clamping detection
    T update(T new_value, bool* is_clamped) {
        return update(new_value, std::chrono::steady_clock::now(), is_clamped);
    }
    
    // Reset filter state
    void reset() override {
        previous_output_q_ = FixedType(0);
        last_timestamp_ = std::chrono::steady_clock::now();
        this->first_call_ = true;
    }
    
    // Get current Q-format output as double for debugging
    double get_current_output_double() const {
        return static_cast<double>(previous_output_q_);
    }
    
    // Get fractional bits used
    int get_fractional_bits() const {
        return fractional_bits_;
    }
    
    // Get Q scale factor
    T get_q_scale() const {
        return static_cast<T>(static_cast<CalcT>(1) << fractional_bits_);
    }
};

// =============================================================================
// Type aliases for commonly used fixed-point filter configurations
// =============================================================================

// int32_t filters (Q16.16 by default)
using FixedPointLowPassFilter32 = FixedPointLowPassFilter<int32_t>;

// int64_t filters (Q32.32 by default)  
using FixedPointLowPassFilter64 = FixedPointLowPassFilter<int64_t, int64_t>;

// Specific fractional bit configurations
using FixedPointLowPassFilter32_16 = FixedPointLowPassFilter<int32_t>;
using FixedPointLowPassFilter32_32 = FixedPointLowPassFilter<int32_t, int64_t, 32>;
using FixedPointLowPassFilter64_32 = FixedPointLowPassFilter<int64_t, int64_t, 32>;
