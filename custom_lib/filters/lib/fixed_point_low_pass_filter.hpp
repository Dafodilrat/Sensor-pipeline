#pragma once

#include <fpm/fixed.hpp>
#include <cstddef>
#include <limits>
#include <chrono>
#include <stdexcept>
#include <iostream>

// =============================================================================
// FixedPointLowPassFilter: Pure fixed-point (Q-format) low-pass IIR filter
//
// Does NOT use floating-point operations at all - designed for systems where
// floating-point computation is unavailable.
// Implements: output = alpha * input + (1 - alpha) * previous_output
// where alpha = dt / (rc + dt) and rc = 1 / (2 * pi * cutoff_freq)
//
// Uses fpm::fixed for all calculations with configurable Q-format precision.
//
// Template parameters:
//   T: Integer type for storage (int32_t, int64_t)
//   CalcT: Integer type for intermediate calculations (default: wider type than T)
//   FractionalBits: Number of fractional bits (default: 16 for int32_t, 32 for int64_t)
// =============================================================================

// Define 2*PI as fixed-point value in Q16.16 format (411377)
// 2 * pi * 65536 = 2 * 3.14159265358979323846 * 65536 ≈ 411377
constexpr std::int32_t TWO_PI_Q16_16_RAW = 411377;

template<typename T, typename CalcT = std::int64_t, unsigned int FractionalBits = (sizeof(T) == 4 ? 16u : 32u)>
class FixedPointLowPassFilter {
    static_assert(FractionalBits == 8 || FractionalBits == 16,
                  "Only 8 or 16 fractional bits are supported");
private:
    using FixedType = fpm::fixed<T, CalcT, FractionalBits>;
    using TimeFixedType = fpm::fixed<std::int32_t, std::int64_t, 16>; // Q16.16 for time calculations
    
    FixedType output_q_;
    unsigned int fractional_bits_;
    TimeFixedType rc_q_;  // Precomputed RC time constant in Q16.16 format
    
    // Timeout handling
    std::int64_t timeout_ns_; // Timeout in nanoseconds (0 = no timeout)
    std::chrono::steady_clock::time_point last_update_time_;
    bool first_update_ = true;
    bool clamp_warning_ = false;  // Set to true when clamping occurs
    bool verbose_warnings_ = false;  // Enable console warnings for clamping/saturation
    
    // Saturating conversion from T to FixedType
    // Sets clamp_warning_ to true when clamping occurs
    FixedType to_q(T value) {
        // For most Q-formats, we can use numeric_limits to get the range
        // The representable range for Qm.n format is:
        // max = (2^(m-1)) - 1 / 2^n  (positive)
        // min = -(2^(m-1)) / 2^n     (negative)
        // where m = sizeof(T)*8 - FractionalBits
        
        constexpr int total_bits = sizeof(T) * 8;
        constexpr int integral_bits = total_bits - FractionalBits;
        
        if (integral_bits <= 0) {
            // No integral bits - can only represent values very close to 0
            // This shouldn't happen with valid configurations
            return FixedType(value);
        }
        
        // Calculate max and min representable values
        // max = (2^(integral_bits) - 1) / (2^FractionalBits)
        // But we need to represent this in the same units as T
        // So we scale up: max_raw = (2^total_bits - 1) >> FractionalBits
        CalcT max_raw = (static_cast<CalcT>(1) << (total_bits - 1)) - 1;
        max_raw = max_raw >> FractionalBits;
        
        CalcT min_raw = -(static_cast<CalcT>(1) << (total_bits - 1));
        min_raw = min_raw >> FractionalBits;
        
        T max_val = static_cast<T>(max_raw);
        T min_val = static_cast<T>(min_raw);
        
        // Clamp the input value to the representable range
        if (value > max_val) {
            clamp_warning_ = true;
            if (verbose_warnings_) {
                std::cerr << "FixedPointLowPassFilter warning: input value " << value
                          << " exceeds maximum representable value (" << max_val << ") for Q"
                          << (total_bits - FractionalBits) << "." << FractionalBits << " format. Clamping to max." << std::endl;
            }
            return FixedType(max_val);
        } else if (value < min_val) {
            clamp_warning_ = true;
            if (verbose_warnings_) {
                std::cerr << "FixedPointLowPassFilter warning: input value " << value
                          << " below minimum representable value (" << min_val << ") for Q"
                          << (total_bits - FractionalBits) << "." << FractionalBits << " format. Clamping to min." << std::endl;
            }
            return FixedType(min_val);
        }
        
        return FixedType(value);
    }
    
    // Compute alpha in Q-format from dt (in seconds as Q16.16)
    FixedType compute_alpha_q(TimeFixedType dt_q) const {
        if (dt_q <= TimeFixedType(0)) return FixedType(0);
        
        // Check for very large dt (filter follows input immediately)
        if (dt_q > rc_q_ * TimeFixedType(4)) return FixedType(1);
        
        // alpha = dt / (rc + dt)
        TimeFixedType numerator = dt_q;
        TimeFixedType denominator = rc_q_ + dt_q;
        
        // Convert Q16.16 division to FixedType's Q-format
        // We do the division in Higher precision then convert
        CalcT num_raw = static_cast<CalcT>(numerator.raw_value());
        CalcT den_raw = static_cast<CalcT>(denominator.raw_value());
        
        // Divide with extra precision, then convert to FixedType's Q-format
        // alpha_raw in Q(16+16).16 = (numerator_q16.16 << 16) / denominator_q16.16
        CalcT alpha_raw = (num_raw << 16) / den_raw;
        
        // Convert from Q32.16 to FixedType's Q-format
        // Need to handle different cases based on fractional bits
        if (FractionalBits < 16) {
            // Scale up: Q32.16 -> Q-format with fewer fractional bits
            CalcT alpha_final = alpha_raw << (16 - FractionalBits);
            return FixedType::from_raw_value(static_cast<T>(alpha_final));
        } else if (FractionalBits > 16) {
            // Scale down: Q32.16 -> Q-format with more fractional bits
            CalcT alpha_final = alpha_raw >> (FractionalBits - 16);
            return FixedType::from_raw_value(static_cast<T>(alpha_final));
        } else {
            // Same number of fractional bits (16)
            return FixedType::from_raw_value(static_cast<T>(alpha_raw));
        }
    }
    
    // Convert duration to Q16.16 fixed-point seconds
    static TimeFixedType duration_to_q(std::chrono::nanoseconds ns) {
        // Convert nanoseconds to seconds in Q16.16 format
        // 1 second = 2^16 in Q16.16
        // So: seconds_q16 = (nanoseconds * 2^16) / 1e9
        std::int64_t ns_count = ns.count();
        std::int64_t q_value = (ns_count * (static_cast<std::int64_t>(1) << 16)) / 1000000000LL;
        return TimeFixedType::from_raw_value(static_cast<std::int32_t>(q_value));
    }
    
    // Validate cutoff frequency
    static void validate_cutoff(std::int32_t cutoff_freq_times_100) {
        if (cutoff_freq_times_100 <= 0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
    }

public:
    // Constructor: cutoff_freq_hz as integer representing Hz * 100 (e.g., 1000 = 10.00 Hz)
    // fractional_bits determines the Q-format precision
    // timeout_ns is timeout in nanoseconds (use 0 for no timeout)
    explicit FixedPointLowPassFilter(
        std::int32_t cutoff_freq_times_100,
        unsigned int fractional_bits = FractionalBits, 
        std::int64_t timeout_ns = 0
    ) : output_q_(FixedType(0)),
        fractional_bits_(fractional_bits),
        timeout_ns_(timeout_ns) {
        
        validate_cutoff(cutoff_freq_times_100);
        
        // Precompute RC constant: rc = 1 / (2 * pi * cutoff_freq)
        // cutoff_freq = cutoff_freq_times_100 / 100.0
        // rc = 100 / (2 * pi * cutoff_freq_times_100)
        // In Q16.16: rc_q16 = (100 * 65536 * 65536) / (2 * pi * cutoff_freq_times_100)
        std::int64_t numerator = 100LL * (1LL << 16) * (1LL << 16);
        std::int64_t denominator = cutoff_freq_times_100 * TWO_PI_Q16_16_RAW;
        std::int64_t rc_raw = numerator / denominator;
        rc_q_ = TimeFixedType::from_raw_value(static_cast<std::int32_t>(rc_raw));
    }
    
    // Update with integer value - converts to Q-format internally
    // Sets clamp_warning_ to true if clamping occurred
    T update(T new_value) {
        clamp_warning_ = false;
        
        auto now = std::chrono::steady_clock::now();
        
        // Handle first update
        if (first_update_) {
            FixedType input_q = to_q(new_value);
            output_q_ = input_q;
            last_update_time_ = now;
            first_update_ = false;
            return new_value;
        }
        
        // Calculate dt in Q16.16 format
        auto dt_ns = now - last_update_time_;
        TimeFixedType dt_q = duration_to_q(dt_ns);
        
        // Check for timeout
        if (timeout_ns_ > 0 && dt_ns.count() > timeout_ns_) {
            reset();
            return update(new_value);
        }
        
        last_update_time_ = now;
        
        // Compute alpha in Q-format
        FixedType alpha_q = compute_alpha_q(dt_q);
        FixedType one_minus_alpha_q = FixedType(1) - alpha_q;
        
        // Convert input to Q-format
        FixedType input_q = to_q(new_value);
        
        // Apply IIR filter in fixed-point: output = alpha * input + (1 - alpha) * previous_output
        FixedType term1 = alpha_q * input_q;
        FixedType term2 = one_minus_alpha_q * output_q_;
        output_q_ = term1 + term2;
        
        // Convert output to T using integer arithmetic only
        return static_cast<T>(output_q_.raw_value() >> fractional_bits_);
    }
    
    // Reset filter state
    void reset() {
        output_q_ = FixedType(0);
        first_update_ = true;
        clamp_warning_ = false;
    }
    
    // Check if clamping occurred in the last update
    bool had_clamp() const {
        return clamp_warning_;
    }
    
    // Enable verbose warning messages for clamping
    void enable_verbose_warnings(bool enable = true) {
        verbose_warnings_ = enable;
    }
    
    // Utility method to get the maximum representable value for this Q-format
    T get_max_value() const {
        constexpr int total_bits = sizeof(T) * 8;
        constexpr int integral_bits = total_bits - FractionalBits;
        
        if (integral_bits <= 0) return 1; // Avoid division by zero
        
        CalcT max_raw = (static_cast<CalcT>(1) << (total_bits - 1)) - 1;
        max_raw = max_raw >> FractionalBits;
        return static_cast<T>(max_raw);
    }
    
    // Utility method to get the minimum representable value for this Q-format
    T get_min_value() const {
        constexpr int total_bits = sizeof(T) * 8;
        constexpr int integral_bits = total_bits - FractionalBits;
        
        if (integral_bits <= 0) return -1; // Avoid division by zero
        
        CalcT min_raw = -(static_cast<CalcT>(1) << (total_bits - 1));
        min_raw = min_raw >> FractionalBits;
        return static_cast<T>(min_raw);
    }
    
    // Check if current output is close to saturation (within 10% of max/min)
    bool is_near_saturation(double threshold = 0.10) const {
        constexpr int total_bits = sizeof(T) * 8;
        constexpr int integral_bits = total_bits - FractionalBits;
        
        if (integral_bits <= 0) {
            return true; // No integral bits, always at limit
        }
        
        // Calculate max and min representable values
        CalcT max_raw = (static_cast<CalcT>(1) << (total_bits - 1)) - 1;
        max_raw = max_raw >> FractionalBits;
        CalcT min_raw = -(static_cast<CalcT>(1) << (total_bits - 1));
        min_raw = min_raw >> FractionalBits;
        
        T max_val = static_cast<T>(max_raw);
        T min_val = static_cast<T>(min_raw);
        
        // Get current output in raw integer form
        T current_output = static_cast<T>(output_q_.raw_value() >> fractional_bits_);
        
        // Check if within threshold of max or min
        CalcT range = static_cast<CalcT>(max_val) - min_val;
        CalcT distance_to_max = static_cast<CalcT>(max_val) - current_output;
        CalcT distance_to_min = current_output - min_val;
        
        return (distance_to_max < threshold * range) || (distance_to_min < threshold * range);
    }
    
    // Get fractional bits used
    unsigned int get_fractional_bits() const {
        return fractional_bits_;
    }
    
    // Get Q scale factor
    T get_q_scale() const {
        return static_cast<T>(static_cast<CalcT>(1) << fractional_bits_);
    }
    
    // Get current RC time constant in Q16.16 format
    std::int32_t get_rc_raw() const {
        return rc_q_.raw_value();
    }
    
    // Get current output as double (for debugging/testing)
    double get_current_output_double() const {
        // Convert output_q_ to double by dividing by 2^fractional_bits_
        return static_cast<double>(output_q_.raw_value()) / (static_cast<CalcT>(1) << fractional_bits_);
    }
    
    // Set new cutoff frequency (integer representing Hz * 100)
    void set_cutoff(std::int32_t cutoff_freq_times_100) {
        validate_cutoff(cutoff_freq_times_100);
        
        // Recompute RC constant in Q16.16 format
        std::int64_t numerator = 100LL * (1LL << 16) * (1LL << 16);
        std::int64_t denominator = cutoff_freq_times_100 * TWO_PI_Q16_16_RAW;
        std::int64_t rc_raw = numerator / denominator;
        rc_q_ = TimeFixedType::from_raw_value(static_cast<std::int32_t>(rc_raw));
    }
    
    // Set timeout in nanoseconds
    void set_timeout(std::int64_t timeout_ns) {
        if (timeout_ns < 0) {
            timeout_ns_ = 0;
        } else {
            timeout_ns_ = timeout_ns;
        }
    }
    
    // Get current timeout in nanoseconds
    std::int64_t get_timeout() const {
        return timeout_ns_;
    }
    
    // Check if timeout is enabled
    bool has_timeout() const {
        return timeout_ns_ > 0;
    }
};

// =============================================================================
// Type aliases for commonly used fixed-point filter configurations
// Only 8 or 16 fractional bits are supported
// =============================================================================

// int32_t filters with Q-format naming (integral_bits.fractional_bits)
using FixedPointLowPassFilter_24_8 = FixedPointLowPassFilter<int32_t, int64_t, 8>;   // Q24.8 (24 integral, 8 fractional)
using FixedPointLowPassFilter_16_16 = FixedPointLowPassFilter<int32_t, int64_t, 16>; // Q16.16 (16 integral, 16 fractional)

// Note: fpm library requires CalcT > BaseType and at least 1 integral bit.
// We cannot provide a 64-bit storage version because it requires an intermediate type
// larger than int64_t (like int128_t) which is not portable.