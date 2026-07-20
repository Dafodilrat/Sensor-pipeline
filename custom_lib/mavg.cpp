#include <cstddef>
#include <limits>
#include <algorithm>
#include <chrono>
#include <array>
#include <cmath>
#include <type_traits>
#include <cstdlib>
#include <iostream>
#include <string>

// Include the ring buffer
#include "ring_buffer.hpp"

// =============================================================================
// Base class for common moving average functionality
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


// =============================================================================
// Time duration based moving average - inherits from FixedMovingAverage
// 
// This class automatically calculates the appropriate buffer size based on:
// - sensor_hz: Expected sample rate in Hz (samples per second)
// - window_duration: Time window for averaging
// The calculated window size = ceil(sensor_hz * window_duration_seconds) + safety_margin
// =============================================================================
template<typename T, size_t MaxSamples>
class TimeDurationMovingAverage : public FixedMovingAverage<T, MaxSamples> {
private:
    RingBuffer<std::chrono::steady_clock::time_point, MaxSamples> timestamp_buffer_;
    std::chrono::milliseconds window_duration_;
    double sensor_hz_;
    size_t calculated_window_size_;

    double safeUpdateSum(double current, double delta, const char* operation) {
        double test = current + delta;
        if (std::isfinite(current) && std::isinf(test)) {
            throw std::overflow_error(std::string("TimeDurationMovingAverage: ") + operation);
        }
        return test;
    }

    void removeExpiredSamples() {
        auto now = std::chrono::steady_clock::now();
        
        while (!timestamp_buffer_.empty()) {
            auto oldest_time = timestamp_buffer_.back(); // back() is oldest
            
            if (now - oldest_time >= window_duration_ && !this->buffer_.empty()) {
                // Remove expired value and its timestamp
                T old_value = this->buffer_.back();
                this->sum_ = safeUpdateSum(this->sum_, -static_cast<double>(old_value),
                                  "overflow detected when removing expired value");
                this->buffer_.pop();
                timestamp_buffer_.pop();
            } else {
                break;
            }
        }
    }

    // Calculate optimal window size based on sensor rate and duration
    static size_t calculateWindowSize(double sensor_hz, std::chrono::milliseconds duration, size_t max_available) {
        if (sensor_hz <= 0.0) {
            throw std::invalid_argument("Sensor Hz must be positive");
        }
        
        double duration_seconds = std::chrono::duration<double>(duration).count();
        size_t base_size = static_cast<size_t>(std::ceil(sensor_hz * duration_seconds));
        
        // Add 20% safety margin to account for timing variations
        // and ensure we don't hit the buffer limit exactly
        size_t with_margin = static_cast<size_t>(base_size * 1.2);
        
        // Make sure we have at least 2 samples for meaningful average
        size_t min_size = std::max<size_t>(2, with_margin);
        
        // Don't exceed the maximum available capacity
        return std::min<size_t>(min_size, max_available);
    }

public:
    // Constructor with sensor Hz and window duration
    // Automatically calculates the optimal window size
    explicit TimeDurationMovingAverage(double sensor_hz, std::chrono::milliseconds duration)
        : sensor_hz_(sensor_hz),
          window_duration_(duration),
          calculated_window_size_(calculateWindowSize(sensor_hz, duration, MaxSamples)) {
        
        if (calculated_window_size_ > MaxSamples) {
            throw std::invalid_argument(
                "Calculated window size (" + std::to_string(calculated_window_size_) + 
                ") exceeds MaxSamples (" + std::to_string(MaxSamples) + 
                "). Increase MaxSamples template parameter."
            );
        }
    }

    // Constructor with just duration (assumes sensor will provide ~1 sample per time unit)
    // This maintains backward compatibility
    explicit TimeDurationMovingAverage(std::chrono::milliseconds duration)
        : TimeDurationMovingAverage(1.0, duration) {}

    T update(T new_value) override {
        auto now = std::chrono::steady_clock::now();

        // Always push to main buffer
        T old_value = this->buffer_.push(new_value);

        // Push timestamp
        timestamp_buffer_.push(now);
        removeExpiredSamples();

        // If buffer was full, we overwrote - remove old value from sum
        if (old_value != new_value) {
            this->sum_ = safeUpdateSum(this->sum_, -static_cast<double>(old_value),
                                "overflow detected when removing value");
            timestamp_buffer_.pop();
        }

        // Add new value to sum
        this->sum_ = safeUpdateSum(this->sum_, static_cast<double>(new_value),
                        "overflow detected when adding new value");

        // Calculate average
        double avg = this->sum_ / static_cast<double>(this->buffer_.size());
        return this->template applyRounding<T>(avg);
    }

    void reset() override {
        this->buffer_.clear();
        timestamp_buffer_.clear();
        this->sum_ = 0.0;
    }

    // Set both sensor Hz and window duration
    void setParameters(double sensor_hz, std::chrono::milliseconds duration) {
        if (sensor_hz <= 0.0) {
            throw std::invalid_argument("Sensor Hz must be positive");
        }
        
        sensor_hz_ = sensor_hz;
        window_duration_ = duration;
        calculated_window_size_ = calculateWindowSize(sensor_hz, duration, MaxSamples);
        
        if (calculated_window_size_ > MaxSamples) {
            throw std::invalid_argument(
                "Calculated window size (" + std::to_string(calculated_window_size_) + 
                ") exceeds MaxSamples (" + std::to_string(MaxSamples) + 
                "). Cannot accommodate these parameters."
            );
        }
        
        // Recalculate expired samples with new parameters
        removeExpiredSamples();
    }

    // Set just the window duration (keeps existing sensor Hz)
    void setWindowDuration(std::chrono::milliseconds duration) {
        setParameters(sensor_hz_, duration);
    }

    // Set just the sensor Hz (keeps existing window duration)
    void setSensorHz(double sensor_hz) {
        setParameters(sensor_hz, window_duration_);
    }

    std::chrono::milliseconds getWindowDuration() const {
        return window_duration_;
    }

    double getSensorHz() const {
        return sensor_hz_;
    }

    size_t getCalculatedWindowSize() const {
        return calculated_window_size_;
    }
};


// =============================================================================
// Factory methods for creating moving average instances
// =============================================================================
namespace MovingAverageFactory {
    template<typename T, size_t MaxSamples>
    FixedMovingAverage<T, MaxSamples> createFixedAverage(size_t sample_count = MaxSamples) {
        return FixedMovingAverage<T, MaxSamples>(sample_count);
    }

    // Create time duration average with sensor Hz and window duration
    template<typename T, size_t MaxSamples>
    TimeDurationMovingAverage<T, MaxSamples> createTimeDurationAverage(
        double sensor_hz, 
        std::chrono::milliseconds duration
    ) {
        return TimeDurationMovingAverage<T, MaxSamples>(sensor_hz, duration);
    }

    // Create time duration average with just duration (backward compatible)
    template<typename T, size_t MaxSamples>
    TimeDurationMovingAverage<T, MaxSamples> createTimeDurationAverage(
        std::chrono::milliseconds duration
    ) {
        return TimeDurationMovingAverage<T, MaxSamples>(duration);
    }
}
