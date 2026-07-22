#pragma once

#include "../../tools/ring_buffer.hpp"
#include <cstddef>
#include <limits>
#include <algorithm>
#include <cmath>
#include <type_traits>
#include <cstdlib>
#include <string>

// =============================================================================
// Fixed size moving average class
// Maintains a fixed number of samples and calculates running average
// =============================================================================

template<typename T, size_t MaxSamples>
class FixedMovingAverage {
protected:
    RingBuffer<T, MaxSamples> buffer_;
    double sum_ = 0.0;

    double safeUpdateSum(double current, double delta, const char* operation) {
        double test = current + delta;
        if (std::isfinite(current) && std::isinf(test)) {
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

public:
    explicit FixedMovingAverage(size_t sample_count = MaxSamples) {
        if (sample_count > MaxSamples) {
            throw std::invalid_argument("Sample count exceeds maximum buffer size");
        }
    }

    virtual ~FixedMovingAverage() = default;

    virtual T update(T new_value) {
        T old_value = buffer_.push(new_value);

        // If buffer was full, we overwrote - remove old value from sum
        if (old_value != new_value) {
            sum_ = safeUpdateSum(sum_, -static_cast<double>(old_value),
                                "overflow detected when removing value");
        }

        // Add new value to sum
        sum_ = safeUpdateSum(sum_, static_cast<double>(new_value),
                        "overflow detected when adding new value");

        // Calculate average
        double avg = sum_ / static_cast<double>(buffer_.size());
        return applyRounding<T>(avg);
    }
    
    virtual void reset() {
        buffer_.clear();
        sum_ = 0.0;
    }

    size_t currentSize() const {
        return buffer_.size();
    }

    size_t capacity() const {
        return MaxSamples;
    }
};
