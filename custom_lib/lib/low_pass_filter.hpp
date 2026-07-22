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
    
    // Check if this is the first call (useful for derived classes)
    bool is_first_call() const {
        return first_call_;
    }
    
    // Mark first call as complete
    void mark_first_call_complete() {
        first_call_ = false;
    }
};

// =============================================================================
// BaseIIRFilter: Base class for IIR (Infinite Impulse Response) filters
// Provides common IIR functionality: previous output, update template method
// =============================================================================

template<typename T>
class BaseIIRFilter : public BaseFilter<T> {
protected:
    T previous_output_;
    
    // Apply IIR filter formula: output = alpha * input + (1 - alpha) * previous_output
    T apply_iir_filter(T new_value, double alpha) {
        return static_cast<T>(alpha * new_value + (1.0 - alpha) * this->previous_output_);
    }

public:
    explicit BaseIIRFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : BaseFilter<T>(cutoff_freq_hz, timeout_seconds),
          previous_output_(T(0)) {}
    
    ~BaseIIRFilter() override = default;
    
    // Reset filter state
    void reset() override {
        this->previous_output_ = T(0);
        this->mark_first_call_complete(); // Reset first call flag
    }
    
    // Get current output (latest filtered value)
    virtual T get_current_output() const {
        return previous_output_;
    }
};

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
            this->mark_first_call_complete();
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
//
// Template parameters:
//   FractionalBits: number of fractional bits in Q-format (default: 16)
// =============================================================================

template<int FractionalBits = 16>
class FixedPointLowPassFilter : public BaseFilter<int32_t> {
private:
    static constexpr int32_t Q_SCALE = 1 << FractionalBits;
    
    int32_t previous_output_q_;
    double rc_;  // Precomputed RC time constant
    
    std::chrono::steady_clock::time_point last_timestamp_;
    
    // Integer type for internal calculations
    using CalcType = int64_t;
    
    // Convert double to Q-format integer
    static int32_t to_q(double value) {
        // Clamp to valid range first
        double clamped = std::clamp(value, 
                                   static_cast<double>(std::numeric_limits<int32_t>::min()) / Q_SCALE,
                                   static_cast<double>(std::numeric_limits<int32_t>::max()) / Q_SCALE);
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
    static int32_t sat_mul_q(int32_t a, int32_t b) {
        CalcType result = static_cast<CalcType>(a) * b;
        // Qn.Qn * Qn.Qn = Q2n.Q2n, need to shift back to Qn.Qn
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
    int32_t compute_alpha_q(double dt) const {
        if (dt <= 0.0) return 0;
        if (dt >= rc_ * 1000.0) return Q_SCALE;
        
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
    // Constructor: cutoff_freq_hz is the cutoff frequency in Hz, timeout_seconds is the max dt before reset
    explicit FixedPointLowPassFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : BaseFilter<int32_t>(cutoff_freq_hz, timeout_seconds),
          previous_output_q_(0),
          rc_(1.0 / (2.0 * M_PI * cutoff_freq_hz)),
          last_timestamp_(std::chrono::steady_clock::now()) {
        // Base constructor already validates parameters
    }
    
    // Update with integer value and timestamp
    int32_t update(int32_t new_value, std::chrono::steady_clock::time_point timestamp) {
        auto current_time = timestamp;
        
        if (this->is_first_call()) {
            previous_output_q_ = to_q(static_cast<double>(new_value));
            last_timestamp_ = current_time;
            this->mark_first_call_complete();
            return new_value;
        }
        
        // Compute dt in seconds
        double dt = std::chrono::duration<double>(current_time - last_timestamp_).count();
        
        if (dt <= 0.0) {
            return static_cast<int32_t>(std::round(from_q(previous_output_q_)));
        }
        
        if (dt > this->timeout_seconds_) {
            previous_output_q_ = to_q(static_cast<double>(new_value));
            last_timestamp_ = current_time;
            return new_value;
        }
        
        // Compute alpha and (1-alpha) in Q-format
        int32_t alpha_q = compute_alpha_q(dt);
        int32_t one_minus_alpha_q = compute_one_minus_alpha_q(alpha_q);
        
        // Convert input to Q-format
        int32_t input_q = to_q(static_cast<double>(new_value));
        
        // Apply IIR filter in fixed-point:
        // output_q = alpha_q * input_q + (1 - alpha_q) * previous_output_q
        int32_t term1 = sat_mul_q(alpha_q, input_q);
        int32_t term2 = sat_mul_q(one_minus_alpha_q, previous_output_q_);
        int32_t output_q = sat_add(term1, term2);
        
        previous_output_q_ = output_q;
        last_timestamp_ = current_time;
        
        return static_cast<int32_t>(std::round(from_q(output_q)));
    }
    
    // Simplified update without explicit timestamp (uses system clock)
    int32_t update(int32_t new_value) {
        return update(new_value, std::chrono::steady_clock::now());
    }
    
    // Reset filter state
    void reset() override {
        previous_output_q_ = 0;
        last_timestamp_ = std::chrono::steady_clock::now();
        this->mark_first_call_complete();
    }
    
    // Get current Q-format output as double for debugging
    double get_current_output_double() const {
        return from_q(previous_output_q_);
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
// VariadicLowPassFilter: Version that accepts variable dt directly
// Useful when timestamp information is not available but dt is known
// 
// Template parameters:
//   T: data type (double, float, int32_t)
//   MaxSamples: buffer size for future extensions (currently unused)
// =============================================================================

template<typename T = double, size_t MaxSamples = 1000>
class VariadicLowPassFilter : public BaseIIRFilter<T> {
public:
    explicit VariadicLowPassFilter(double cutoff_freq_hz, double timeout_seconds = 10.0)
        : BaseIIRFilter<T>(cutoff_freq_hz, timeout_seconds) {
        // Base constructor already validates parameters
    }
    
    // Update with value and dt (in seconds)
    T update_with_dt(T new_value, double dt) {
        if (this->is_first_call()) {
            this->previous_output_ = new_value;
            this->mark_first_call_complete();
            return this->previous_output_;
        }
        
        if (dt <= 0.0) {
            return this->previous_output_;
        }
        
        if (dt > this->timeout_seconds_) {
            this->previous_output_ = new_value;
            return this->previous_output_;
        }
        
        double alpha = this->compute_alpha(dt);
        this->previous_output_ = this->apply_iir_filter(new_value, alpha);
        return this->previous_output_;
    }
    
    // Reset filter state
    void reset() override {
        BaseIIRFilter<T>::reset();
    }
};

// =============================================================================
// Type aliases for commonly used filter configurations
// =============================================================================

// Floating-point filters
using FloatLowPassFilterDouble = FloatLowPassFilter<double>;
using FloatLowPassFilterFloat = FloatLowPassFilter<float>;

// Fixed-point filters  
using FixedPointLowPassFilter16 = FixedPointLowPassFilter<16>;
using FixedPointLowPassFilter32 = FixedPointLowPassFilter<32>;

// Variadic filters
using VariadicLowPassFilterDouble = VariadicLowPassFilter<double>;
using VariadicLowPassFilterFloat = VariadicLowPassFilter<float>;
using VariadicLowPassFilterInt32 = VariadicLowPassFilter<int32_t>;