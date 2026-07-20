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


// ============================================================================= 
// RingBuffer: A generic circular buffer implementation
// ============================================================================= 
template<typename T, size_t Capacity>
class RingBuffer {
    private:
        std::array<T, Capacity> buffer_{};
        size_t head_ = 0;
        size_t count_ = 0;

    public:
        T push(const T& value) {
            T removed = value;
            
            if (full()) {
                removed = buffer_[head_];
            }
            
            buffer_[head_] = value;
            head_ = (head_ + 1) % Capacity;
            
            if (!full()) {
                count_++;
            }
            
            return removed;
        }

        T pop() {
            if (empty()) {
                throw std::runtime_error("RingBuffer: cannot pop from empty buffer");
            }
            T value = buffer_[head_];
            head_ = (head_ + 1) % Capacity;
            count_--;
            return value;
        }

        // Get latest element (most recently added) - front() is latest
        T& front() {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            return buffer_[(head_ + Capacity - 1) % Capacity];
        }

        // Get oldest element - back() is oldest
        T& back() {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            size_t oldest_index = (head_ + Capacity - count_) % Capacity;
            return buffer_[oldest_index];
        }

        // Const versions
        const T& front() const {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            return buffer_[(head_ + Capacity - 1) % Capacity];
        }

        const T& back() const {
            if (empty()) throw std::runtime_error("RingBuffer: buffer is empty");
            size_t oldest_index = (head_ + Capacity - count_) % Capacity;
            return buffer_[oldest_index];
        }

        size_t size() const { return count_; }
        size_t capacity() const { return Capacity; }
        bool empty() const { return count_ == 0; }
        bool full() const { return count_ == Capacity; }
        void clear() { head_ = 0; count_ = 0; }
};


// ============================================================================= 
// MovingAverage: Moving average filter with two modes
// ============================================================================= 
template<typename T, size_t MaxSamples>
class MovingAverage {
private:
    enum class Mode { FIXED_SAMPLES, TIME_DURATION };
    Mode mode_;

    // Common buffer for both modes
    RingBuffer<T, MaxSamples> buffer_;
    double sum_ = 0.0;
    
    // For FIXED_SAMPLES mode
    size_t fixed_sample_count_;

    // For TIME_DURATION mode
    RingBuffer<std::chrono::steady_clock::time_point, MaxSamples> timestamp_buffer_;
    std::chrono::milliseconds window_duration_;

    double safeUpdateSum(double current, double delta, const char* operation) {
        double test = current + delta;
        if (std::isfinite(current) && std::isinf(test)) {
            throw std::overflow_error(std::string("MovingAverage: ") + operation);
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

    void removeExpiredSamples() {
        auto now = std::chrono::steady_clock::now();
        
        while (!timestamp_buffer_.empty()) {
            auto oldest_time = timestamp_buffer_.back(); // back() is oldest
            
            if (now - oldest_time >= window_duration_ && !buffer_.empty()) {
                // Remove expired value and its timestamp
                T old_value = buffer_.back();
                sum_ = safeUpdateSum(sum_, -static_cast<double>(old_value),
                                  "overflow detected when removing expired value");
                buffer_.pop();
                timestamp_buffer_.pop();
            } else {
                break;
            }
        }
    }

public:
    explicit MovingAverage(size_t sample_count)
        : mode_(Mode::FIXED_SAMPLES),
          fixed_sample_count_(sample_count) {
        if (sample_count > MaxSamples) {
            throw std::invalid_argument("Sample count exceeds maximum buffer size");
        }
    }

    explicit MovingAverage(std::chrono::milliseconds duration)
        : mode_(Mode::TIME_DURATION),
          window_duration_(duration) {}

    T update(T new_value) {
        auto now = std::chrono::steady_clock::now();

        // Always push to main buffer
        T old_value = buffer_.push(new_value);
        
        // Handle mode-specific operations
        if (mode_ == Mode::TIME_DURATION) {
            removeExpiredSamples();
            timestamp_buffer_.push(now);
            
            // If buffer was full, we overwrote - remove old value from sum
            if (old_value != new_value) {
                sum_ = safeUpdateSum(sum_, -static_cast<double>(old_value),
                                  "overflow detected when removing value");
            }
        }
        
        // Add new value to sum (common for both modes)
        sum_ = safeUpdateSum(sum_, static_cast<double>(new_value),
                          "overflow detected when adding new value");

        // Calculate average based on mode
        if (mode_ == Mode::FIXED_SAMPLES) {
            size_t effective_count = std::min(buffer_.size(), fixed_sample_count_);
            double avg = sum_ / static_cast<double>(effective_count);
            return applyRounding<T>(avg);
        } else {
            double avg = sum_ / static_cast<double>(buffer_.size());
            return applyRounding<T>(avg);
        }
    }

    void reset() {
        buffer_.clear();
        timestamp_buffer_.clear();
        sum_ = 0.0;
    }

    size_t currentSize() const {
        return buffer_.size();
    }

    Mode mode() const { return mode_; }
};
