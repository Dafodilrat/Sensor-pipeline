#pragma once

#include "../tools/ring_buffer.hpp"
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
// Fixed size moving average class
// Maintains a fixed number of samples and calculates running average
// Optionally resets on timeout when time gap between samples exceeds threshold
// =============================================================================

template<typename T, size_t MaxSamples>
class FixedMovingAverage {
protected:
    RingBuffer<T, MaxSamples> buffer_;
    float sum_ = 0.0f;
    
    // Timeout functionality
    double timeout_seconds_;
    std::chrono::steady_clock::time_point last_update_time_;
    bool first_update_ = true;
    bool timeout_occurred_ = false;

    float safeUpdateSum(float current, float delta, const char* operation) {
        float test = current + delta;
        if (std::isfinite(current) && !std::isfinite(test)) {
            throw std::overflow_error(std::string("FixedMovingAverage: ") + operation);
        }
        return test;
    }

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
    
    // Validate timeout value
    static void validate_timeout(double timeout_seconds) {
        if (timeout_seconds <= 0.0) {
            throw std::invalid_argument("Timeout must be positive");
        }
    }

public:
    // Constructor with size and optional timeout
    // timeout_seconds = -1.0 means no timeout (default behavior)
    explicit FixedMovingAverage(size_t size = MaxSamples, double timeout_seconds = -1.0) 
        : buffer_(size), 
          timeout_seconds_(timeout_seconds) {
        if (size == 0) {
            throw std::invalid_argument("Size must be positive");
        }
        if (timeout_seconds > 0.0) {
            validate_timeout(timeout_seconds);
        }
    }

    virtual ~FixedMovingAverage() = default;

    virtual T update(T new_value) {
        auto now = std::chrono::steady_clock::now();
        
        // Check for timeout on first update (no previous time to compare)
        if (first_update_) {
            last_update_time_ = now;
            first_update_ = false;
        } else if (timeout_seconds_ > 0.0) {
            // Calculate time since last update
            auto dt = std::chrono::duration<double>(now - last_update_time_).count();
            
            // Reset if gap exceeds timeout
            if (dt > timeout_seconds_) {
                reset();
                timeout_occurred_ = true;
            } else {
                timeout_occurred_ = false;
            }
        }
        last_update_time_ = now;

        T old_value = buffer_.push(new_value);

        // If buffer was full, we removed an old value, so subtract it from sum
        if (old_value != new_value) {
            sum_ = safeUpdateSum(sum_, -static_cast<float>(old_value),
                                "overflow detected when removing value");
        }

        // Add new value to sum
        sum_ = safeUpdateSum(sum_, static_cast<float>(new_value),
                        "overflow detected when adding new value");

        // Calculate average
        float avg = sum_ / static_cast<float>(buffer_.size());
        return applyRounding<T>(static_cast<double>(avg));
    }
    
    virtual void reset() {
        buffer_.clear();
        sum_ = 0.0f;
        first_update_ = true;  // Reset first update flag so next update initializes timestamp
        timeout_occurred_ = false;
    }

    size_t currentSize() const {
        return buffer_.size();
    }

    size_t capacity() const {
        return buffer_.size_limit();
    }
    
    size_t maxCapacity() const {
        return MaxSamples;
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

    // Check if a timeout occurred during the last update
    bool timeout_occurred() const {
        return timeout_occurred_;
    }
};
