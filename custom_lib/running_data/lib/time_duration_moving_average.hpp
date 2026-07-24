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

public:
    // Constructor with window duration only
    explicit TimeDurationMovingAverage(size_t window_size, std::chrono::milliseconds duration)
        : FixedMovingAverage<T, MaxSamples>(window_size),
          timestamp_buffer_(window_size),
          window_duration_(duration) {
        
        if (window_size > MaxSamples) {
            throw std::invalid_argument(
                "Window size (" + std::to_string(window_size) + 
                ") exceeds MaxSamples (" + std::to_string(MaxSamples) + 
                "). Increase MaxSamples template parameter."
            );
        }
    }

    T update(T new_value) override {
        auto now = std::chrono::steady_clock::now();

        // Push to main buffer - returns old value if buffer was full
        T old_value = this->buffer_.push(new_value);

        // Push timestamp - returns old timestamp if buffer was full
        auto old_timestamp = timestamp_buffer_.push(now);
        
        removeExpiredSamples();

        // If main buffer removed an old value, subtract it from sum
        if (old_value != new_value) {
            this->sum_ = safeUpdateSum(this->sum_, -static_cast<double>(old_value),
                                "overflow detected when removing value");
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
