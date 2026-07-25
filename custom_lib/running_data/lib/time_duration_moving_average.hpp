#pragma once

#include "fixed_moving_average.hpp"

#include "../tools/ring_buffer.hpp"
#include <chrono>

// =============================================================================
// Time duration based moving average
// Inherits from FixedMovingAverage with a fixed window size passed at construction
// Expires old samples based on sensor rate and desired time window
// =============================================================================

template<typename T, size_t MaxSamples>
class TimeDurationMovingAverage : public FixedMovingAverage<T, MaxSamples> {
private:
    RingBuffer<std::chrono::steady_clock::time_point, MaxSamples> timestamp_buffer_;
    std::chrono::milliseconds window_duration_;

    double safeUpdateSum(double current, double delta, const char* operation) {
        double test = current + delta;
        if (std::isfinite(current) && !std::isfinite(test)) {
            throw std::overflow_error(std::string("TimeDurationMovingAverage: ") + operation);
        }
        return test;
    }

    void removeExpiredSamples() {
        auto now = std::chrono::steady_clock::now();
        
        while (!timestamp_buffer_.empty()) {
            
            auto oldest_time = timestamp_buffer_.back();
            
            if (now - oldest_time >= window_duration_) {
                // Remove expired value and its timestamp
                // pop() returns the old value that was removed
                T old_value = this->buffer_.pop();
                timestamp_buffer_.pop();
                this->sum_ = safeUpdateSum(this->sum_, -static_cast<double>(old_value),
                                  "overflow detected when removing expired value");
            } else {
                break;
            }
        }
    }

public:
    // Constructor with window duration and optional timeout
    // timeout_seconds = -1.0 means no timeout reset (default)
    explicit TimeDurationMovingAverage(size_t window_size, std::chrono::milliseconds duration, 
                                         double timeout_seconds = -1.0)
        : FixedMovingAverage<T, MaxSamples>(window_size, timeout_seconds),
          timestamp_buffer_(window_size),
          window_duration_(duration) {
        
        if (window_size > MaxSamples) {
            throw std::invalid_argument(
                "Window size (" + std::to_string(window_size) + 
                ") exceeds MaxSamples (" + std::to_string(MaxSamples) + 
                "). Increase MaxSamples template parameter."
            );
        }
        // first_update_ is already initialized by parent
    }

    T update(T new_value) override {
        // Remove expired samples based on time window BEFORE calling parent update
        removeExpiredSamples();
        
        // Push current timestamp
        timestamp_buffer_.push(std::chrono::steady_clock::now());
        
        // Delegate to parent class to handle the actual value update
        // Parent handles: timeout check, buffer push, sum maintenance
        T result = FixedMovingAverage<T, MaxSamples>::update(new_value);
        
        // If timeout occurred in parent, also reset our timestamp buffer
        if (this->timeout_occurred()) {
            timestamp_buffer_.clear();
        }
        
        return result;
    }


    // Set the window duration
    void setWindowDuration(std::chrono::milliseconds duration) {
        if (duration <= std::chrono::milliseconds(0)) {
            throw std::invalid_argument("Window duration must be positive");
        }
        
        window_duration_ = duration;
        
        // Recalculate expired samples with new window duration
        removeExpiredSamples();
    }

    std::chrono::milliseconds getWindowDuration() const {
        return window_duration_;
    }
};