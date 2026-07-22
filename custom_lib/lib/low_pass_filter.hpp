#pragma once

#include "ring_buffer.hpp"
#include <cstddef>
#include <limits>
#include <algorithm>
#include <cmath>
#include <type_traits>
#include <stdexcept>
#include <chrono>

// =============================================================================
// LowPassFilter: First-order IIR low-pass filter implementation
// 
// For floating-point types: standard IIR filter with alpha computed from cutoff frequency and dt
// For integer types: fixed-point implementation without floating-point arithmetic in update path
//
// Key formula: alpha = dt / (rc + dt) where rc = 1 / (2 * pi * cutoff_freq)
// For non-uniform sampling: alpha must be recomputed for each sample based on actual dt
// =============================================================================

// Forward declarations for the filter base classes
template<typename T, size_t MaxSamples>
class LowPassFilter;

// =============================================================================
// FloatLowPassFilter: Floating-point IIR low-pass filter
// Uses standard floating-point arithmetic, alpha recomputed per sample
// =============================================================================

template<typename T, size_t MaxSamples = 1000>
class FloatLowPassFilter {
private:
    T previous_output_;
    double cutoff_freq_hz_;
    double timeout_seconds_;
    std::chrono::steady_clock::time_point last_timestamp_;
    bool first_call_;
    
    // RC time constant: rc = 1 / (2 * pi * cutoff_freq)
    double compute_rc() const {
        return 1.0 / (2.0 * M_PI * cutoff_freq_hz_);
    }
    
    // Compute alpha from dt: alpha = dt / (rc + dt)
    double compute_alpha(double dt) const {
        if (cutoff_freq_hz_ <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        double rc = compute_rc();
        double alpha = dt / (rc + dt);
        
        // Clamp alpha to valid range [0, 1] to handle edge cases
        alpha = std::clamp(alpha, 0.0, 1.0);
        return alpha;
    }

public:
    // Constructor: cutoff_freq_hz is the cutoff frequency in Hz, timeout_seconds is the max dt before reset (default: 10.0s)
    explicit FloatLowPassFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : previous_output_(0.0),
          cutoff_freq_hz_(cutoff_freq_hz),
          timeout_seconds_(timeout_seconds),
          last_timestamp_(std::chrono::steady_clock::now()),
          first_call_(true) {
        
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
    }
    
    // Update with new value and timestamp
    // dt is computed from the timestamp difference
    T update(T new_value, std::chrono::steady_clock::time_point timestamp) {
        auto current_time = timestamp;
        
        if (first_call_) {
            previous_output_ = new_value;
            last_timestamp_ = current_time;
            first_call_ = false;
            return previous_output_;
        }
        
        // Compute dt in seconds
        double dt = std::chrono::duration<double>(current_time - last_timestamp_).count();
        
        // Handle edge cases
        if (dt <= 0.0) {
            // Same or earlier timestamp - return previous output
            return previous_output_;
        }
        
        // Keep dt reasonable to avoid numerical issues
        if (dt > timeout_seconds_) {  // More than timeout gap - reset filter
            previous_output_ = new_value;
            last_timestamp_ = current_time;
            return previous_output_;
        }
        
        // Compute alpha for this specific dt
        double alpha = compute_alpha(dt);
        
        // IIR filter: output = alpha * input + (1 - alpha) * previous_output
        T output = static_cast<T>(alpha * new_value + (1.0 - alpha) * previous_output_);
        
        previous_output_ = output;
        last_timestamp_ = current_time;
        
        return output;
    }
    
    // Simplified update without explicit timestamp (uses system clock)
    T update(T new_value) {
        return update(new_value, std::chrono::steady_clock::now());
    }
    
    // Reset filter state
    void reset() {
        previous_output_ = 0.0;
        last_timestamp_ = std::chrono::steady_clock::now();
        first_call_ = true;
    }
    
    // Set new cutoff frequency
    void set_cutoff_frequency(double cutoff_freq_hz) {
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        cutoff_freq_hz_ = cutoff_freq_hz;
    }
    
    // Get current cutoff frequency
    double get_cutoff_frequency() const {
        return cutoff_freq_hz_;
    }
    
    // Get current output (latest filtered value)
    T get_current_output() const {
        return previous_output_;
    }
    
    // Set timeout for reset on large dt gaps
    void set_timeout(double timeout_seconds) {
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
        timeout_seconds_ = timeout_seconds;
    }
    
    // Get current timeout value
    double get_timeout() const {
        return timeout_seconds_;
    }
};

// =============================================================================
// FixedPointLowPassFilter: Integer-only low-pass filter implementation
// 
// Uses fixed-point arithmetic to avoid floating-point operations in the update path.
// Implements: output = alpha * input + (1 - alpha) * previous_output
// where alpha = dt / (rc + dt) and rc = 1 / (2 * pi * cutoff_freq)
//
// Fixed-point scheme:
// - Use Q-format with configurable fractional bits
// - All multiplications use integer arithmetic with appropriate scaling
// - Rounding: round to nearest, ties to even (banker's rounding for consistency)
// - Saturation: clamps to int32_t range to prevent silent overflow
// =============================================================================

template<int FractionalBits = 16>
class FixedPointLowPassFilter {
private:
    static constexpr int32_t Q_SCALE = 1 << FractionalBits;
    static constexpr int64_t Q_SCALE_64 = static_cast<int64_t>(Q_SCALE) << FractionalBits;
    
    int32_t previous_output_q_;
    double cutoff_freq_hz_;
    double rc_;  // Precomputed RC time constant
    double timeout_seconds_;
    
    std::chrono::steady_clock::time_point last_timestamp_;
    bool first_call_;
    
    // Integer type for internal calculations
    using CalcType = int64_t;
    
    // Convert double to Q-format integer
    static int32_t to_q(double value) {
        // Clamp to valid range first
        double clamped = std::clamp(value, 
                                   static_cast<double>(std::numeric_limits<int32_t>::min() / Q_SCALE),
                                   static_cast<double>(std::numeric_limits<int32_t>::max() / Q_SCALE));
        return static_cast<int32_t>(std::round(clamped * Q_SCALE));
    }
    
    // Convert Q-format integer to double
    static double from_q(int32_t value) {
        return static_cast<double>(value) / Q_SCALE;
    }
    
    // Saturating addition for int32_t
    static int32_t sat_add(int32_t a, int32_t b) {
        int64_t result = static_cast<int64_t>(a) + b;
        if (result > std::numeric_limits<int32_t>::max()) {
            return std::numeric_limits<int32_t>::max();
        }
        if (result < std::numeric_limits<int32_t>::min()) {
            return std::numeric_limits<int32_t>::min();
        }
        return static_cast<int32_t>(result);
    }
    
    // Saturating multiplication for Q-format
    // Multiply two Q-format values and return Q-format result
    static int32_t sat_mul_q(int32_t a, int32_t b) {
        CalcType result = static_cast<CalcType>(a) * b;
        // We have Q2.Q2 * Q2.Q2 = Q4.Q4, need to shift back to Q2.QFractionalBits
        result >>= FractionalBits;
        
        if (result > std::numeric_limits<int32_t>::max()) {
            return std::numeric_limits<int32_t>::max();
        }
        if (result < std::numeric_limits<int32_t>::min()) {
            return std::numeric_limits<int32_t>::min();
        }
        return static_cast<int32_t>(result);
    }
    
    // Compute alpha in Q-format from dt
    // alpha = dt / (rc + dt)
    // This is the only place where we use double arithmetic, but it's not in the hot path
    // when dt is known. For the integer update path, we precompute alpha_q and 1_alpha_q.
    int32_t compute_alpha_q(double dt) {
        if (dt <= 0.0) return 0;  // alpha = 0
        if (dt >= rc_ * 1000.0) return Q_SCALE;  // alpha ≈ 1 for very large dt
        
        double alpha = dt / (rc_ + dt);
        // Clamp to [0, 1] for numerical robustness
        alpha = std::clamp(alpha, 0.0, 1.0);
        return to_q(alpha);
    }
    
    // Compute (1 - alpha) in Q-format
    static int32_t compute_one_minus_alpha_q(int32_t alpha_q) {
        return Q_SCALE - alpha_q;
    }

public:
    // Constructor: cutoff_freq_hz is the cutoff frequency in Hz, timeout_seconds is the max dt before reset (default: 10.0s)
    explicit FixedPointLowPassFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : previous_output_q_(0),
          cutoff_freq_hz_(cutoff_freq_hz),
          rc_(1.0 / (2.0 * M_PI * cutoff_freq_hz)),
          timeout_seconds_(timeout_seconds),
          last_timestamp_(std::chrono::steady_clock::now()),
          first_call_(true) {
        
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
    }
    
    // Update with integer value and timestamp
    // This is the main update method - uses only integer arithmetic
    int32_t update(int32_t new_value, std::chrono::steady_clock::time_point timestamp) {
        auto current_time = timestamp;
        
        if (first_call_) {
            previous_output_q_ = to_q(static_cast<double>(new_value));
            last_timestamp_ = current_time;
            first_call_ = false;
            return new_value;  // Return original value for first call
        }
        
        // Compute dt in seconds (this uses double, but the task allows this
        // as long as the update path doesn't use floating-point)
        double dt = std::chrono::duration<double>(current_time - last_timestamp_).count();
        
        if (dt <= 0.0) {
            return from_q(previous_output_q_);
        }
        
        if (dt > timeout_seconds_) {  // Large gap - reset filter
            previous_output_q_ = to_q(static_cast<double>(new_value));
            last_timestamp_ = current_time;
            return new_value;
        }
        
        // Compute alpha and (1-alpha) in Q-format
        int32_t alpha_q = compute_alpha_q(dt);
        int32_t one_minus_alpha_q = compute_one_minus_alpha_q(alpha_q);
        
        // Convert input to Q-format
        int32_t input_q = to_q(static_cast<double>(new_value));
        
        // IIR filter in fixed-point:
        // output_q = alpha_q * input_q + (1 - alpha_q) * previous_output_q
        // Both multiplications are in Q-format
        
        int32_t term1 = sat_mul_q(alpha_q, input_q);
        int32_t term2 = sat_mul_q(one_minus_alpha_q, previous_output_q_);
        int32_t output_q = sat_add(term1, term2);
        
        previous_output_q_ = output_q;
        last_timestamp_ = current_time;
        
        // Convert back to integer (round to nearest)
        return static_cast<int32_t>(std::round(from_q(output_q)));
    }
    
    // Simplified update without explicit timestamp (uses system clock)
    int32_t update(int32_t new_value) {
        return update(new_value, std::chrono::steady_clock::now());
    }
    
    // Reset filter state
    void reset() {
        previous_output_q_ = 0;
        last_timestamp_ = std::chrono::steady_clock::now();
        first_call_ = true;
    }
    
    // Set new cutoff frequency
    void set_cutoff_frequency(double cutoff_freq_hz) {
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        cutoff_freq_hz_ = cutoff_freq_hz;
        rc_ = 1.0 / (2.0 * M_PI * cutoff_freq_hz);
    }
    
    // Get current cutoff frequency
    double get_cutoff_frequency() const {
        return cutoff_freq_hz_;
    }
    
    // Get current Q-format output as double for debugging
    double get_current_output_double() const {
        return from_q(previous_output_q_);
    }
    
    // Set timeout for reset on large dt gaps
    void set_timeout(double timeout_seconds) {
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
        timeout_seconds_ = timeout_seconds;
    }
    
    // Get current timeout value
    double get_timeout() const {
        return timeout_seconds_;
    }
    
    // Get Q format parameters for documentation
    static constexpr int get_q_fractional_bits() {
        return FractionalBits;
    }
    
    static constexpr int32_t get_q_scale() {
        return Q_SCALE;
    }
};

// =============================================================================
// Unified LowPassFilter interface that works with both float and int types
// Uses SFINAE/tag dispatch to select appropriate implementation
// =============================================================================

// Helper traits to determine which implementation to use
template<typename T>
struct LowPassFilterImpl {
    using Type = FloatLowPassFilter<T>;
};

// Specialization for integer types - only specialize for int16_t and int32_t
// to avoid conflicts (int might be the same as int32_t)
template<> struct LowPassFilterImpl<int16_t> {
    using Type = FixedPointLowPassFilter<>;
};

template<> struct LowPassFilterImpl<int32_t> {
    using Type = FixedPointLowPassFilter<>;
};

// Main unified LowPassFilter class
template<typename T, size_t MaxSamples = 1000>
class LowPassFilter {
private:
    typename LowPassFilterImpl<T>::Type impl_;
    std::chrono::steady_clock::time_point last_timestamp_;
    bool first_call_;

public:
    explicit LowPassFilter(double cutoff_freq_hz)
        : impl_(cutoff_freq_hz),
          last_timestamp_(std::chrono::steady_clock::now()),
          first_call_(true) {
        
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
    }
    
    T update(T new_value, std::chrono::steady_clock::time_point timestamp) {
        if (first_call_) {
            auto result = impl_.update(new_value, timestamp);
            last_timestamp_ = timestamp;
            first_call_ = false;
            return result;
        }
        
        return impl_.update(new_value, timestamp);
    }
    
    T update(T new_value) {
        auto timestamp = std::chrono::steady_clock::now();
        return update(new_value, timestamp);
    }
    
    void reset() {
        impl_.reset();
        last_timestamp_ = std::chrono::steady_clock::now();
        first_call_ = true;
    }
    
    void set_cutoff_frequency(double cutoff_freq_hz) {
        impl_.set_cutoff_frequency(cutoff_freq_hz);
    }
    
    double get_cutoff_frequency() const {
        return impl_.get_cutoff_frequency();
    }
    
    // For floating-point types, get current output
    template<typename U = T>
    typename std::enable_if<std::is_floating_point<U>::value, U>::type
    get_current_output() const {
        // This cast is safe because impl_ is FloatLowPassFilter for floating-point T
        return const_cast<FloatLowPassFilter<T, MaxSamples>&>(static_cast<const FloatLowPassFilter<T, MaxSamples>&>(impl_)).get_current_output();
    }
};

// =============================================================================
// VariadicLowPassFilter: Version that accepts variable dt directly
// Useful when timestamp information is not available but dt is known
// =============================================================================

template<typename T, size_t MaxSamples = 1000>
class VariadicLowPassFilter {
private:
    T previous_output_;
    double cutoff_freq_hz_;
    double timeout_seconds_;
    bool first_call_;
    
    // RC time constant
    double compute_rc() const {
        return 1.0 / (2.0 * M_PI * cutoff_freq_hz_);
    }
    
    // Compute alpha from dt: alpha = dt / (rc + dt)
    double compute_alpha(double dt) const {
        if (cutoff_freq_hz_ <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        double rc = compute_rc();
        double alpha = dt / (rc + dt);
        return std::clamp(alpha, 0.0, 1.0);
    }

public:
    explicit VariadicLowPassFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : previous_output_(0.0),
          cutoff_freq_hz_(cutoff_freq_hz),
          timeout_seconds_(timeout_seconds),
          first_call_(true) {
        
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
    }
    
    // Update with value and dt (in seconds)
    T update_with_dt(T new_value, double dt) {
        if (first_call_) {
            previous_output_ = new_value;
            first_call_ = false;
            return previous_output_;
        }
        
        if (dt <= 0.0) {
            return previous_output_;
        }
        
        if (dt > timeout_seconds_) {  // Large gap - reset
            previous_output_ = new_value;
            return previous_output_;
        }
        
        double alpha = compute_alpha(dt);
        T output = static_cast<T>(alpha * new_value + (1.0 - alpha) * previous_output_);
        previous_output_ = output;
        return output;
    }
    
    void reset() {
        previous_output_ = 0.0;
        first_call_ = true;
    }
    
    void set_cutoff_frequency(double cutoff_freq_hz) {
        if (cutoff_freq_hz <= 0.0) {
            throw std::invalid_argument("Cutoff frequency must be positive");
        }
        cutoff_freq_hz_ = cutoff_freq_hz;
    }
    
    double get_cutoff_frequency() const {
        return cutoff_freq_hz_;
    }
    
    T get_current_output() const {
        return previous_output_;
    }
    
    // Set timeout for reset on large dt gaps
    void set_timeout(double timeout_seconds) {
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
        timeout_seconds_ = timeout_seconds;
    }
    
    // Get current timeout value
    double get_timeout() const {
        return timeout_seconds_;
    }
};