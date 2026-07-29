#pragma once

#include <cstddef>
#include <stdexcept>
#include <algorithm>
#include <chrono>
#include <string>
#include "../tools/ring_buffer.hpp"
#include "../tools/fixed_heap.hpp"

// =============================================================================
// MedianFilter: Sliding window median filter using heaps with position tracking
//
// Uses RingBuffer to store SensorData structs that include position info.
// Maintains two heaps on fixed arrays: max-heap for lower half, min-heap for upper.
// Uses position tracking to efficiently remove expired elements.
//
// Key properties:
// - ZERO dynamic memory allocation (all storage is on stack/fixed arrays)
// - O(log n) insertion and median access
// - O(log n) removal using position lookup
// - Type-generic: works with int, float, double
// - Window size is now configurable at runtime (up to MaxWindowSize template param)
// - Optional timeout: resets filter if time gap between updates exceeds threshold
//
// Note: This file demonstrates extensibility - it can be added to the library
// without modifying any existing files. Users can instantiate it directly.
// =============================================================================

// Struct to store sensor data with its position in the ring buffer
// This allows us to find and remove elements from heaps when they expire
template<typename T, size_t MaxWindowSize>
struct SensorData {
    T value;
    size_t position;  // Index in ring buffer when inserted
    
    // For comparison in FixedHeap
    bool operator>(const SensorData& other) const {
        return value > other.value;
    }
    
    bool operator<(const SensorData& other) const {
        return value < other.value;
    }
};

template<typename T, size_t MaxWindowSize = 101>
class MedianFilter {
private:
    size_t window_size_;
    size_t lower_capacity_;
    size_t upper_capacity_;
    RingBuffer<SensorData<T, MaxWindowSize>, MaxWindowSize> window_;
    FixedHeap<SensorData<T, MaxWindowSize>, (MaxWindowSize + 1) / 2, MaxWindowSize, true> lower_;   // Max-heap for lower half
    FixedHeap<SensorData<T, MaxWindowSize>, (MaxWindowSize + 1) / 2, MaxWindowSize, false> upper_;  // Min-heap for upper half
    size_t next_position_ = 0;
    
    // Timeout functionality
    float timeout_seconds_;
    std::chrono::steady_clock::time_point last_update_time_;
    bool first_update_ = true;
    bool timeout_occurred_ = false;

    // Balance heaps so lower_ has at most one more than upper_
    void rebalance() {
        while (lower_.size() > upper_.size() + 1) {
            SensorData<T, MaxWindowSize> val = lower_.top();
            lower_.pop();
            upper_.push(val);
        }
        while (upper_.size() > lower_.size()) {
            SensorData<T, MaxWindowSize> val = upper_.top();
            upper_.pop();
            lower_.push(val);
        }
    }

    void insertIntoHeap(const SensorData<T, MaxWindowSize>& data) {
        if (lower_.empty() || data.value <= lower_.top().value) {
            lower_.push(data);
        } else {
            upper_.push(data);
        }
        rebalance();
    }

    // Helper to calculate lower heap capacity (ceil of window_size/2)
    static size_t calculateLowerCapacity(size_t window_size) {
        return (window_size + 1) / 2;
    }
    
    // Helper to calculate upper heap capacity (floor of window_size/2)
    static size_t calculateUpperCapacity(size_t window_size) {
        return window_size / 2;
    }
    
    // Validate timeout value
    static void validate_timeout(float timeout_seconds) {
        if (timeout_seconds <= 0.0f) {
            throw std::invalid_argument("Timeout must be positive");
        }
    }

public:
    // Constructor with window size and optional timeout
    // timeout_seconds <= 0 means no timeout (default behavior)
    explicit MedianFilter(size_t window_size, float timeout_seconds = -1.0f) 
        : window_size_(window_size),
          lower_capacity_(calculateLowerCapacity(window_size)),
          upper_capacity_(calculateUpperCapacity(window_size)),
          window_(),
          lower_(calculateLowerCapacity(window_size)),
          upper_(calculateUpperCapacity(window_size)),
          timeout_seconds_(timeout_seconds) {
        if (window_size == 0) {
            throw std::invalid_argument("Window size must be positive");
        }
        if (window_size > MaxWindowSize) {
            throw std::invalid_argument(
                "Window size (" + std::to_string(window_size) + 
                ") exceeds MaxWindowSize (" + std::to_string(MaxWindowSize) + 
                "). Increase MaxWindowSize template parameter."
            );
        }
        if (timeout_seconds > 0.0) {
            validate_timeout(timeout_seconds);
        }
    }

    T update(T new_value) {
        auto now = std::chrono::steady_clock::now();
        
        // Check for timeout on first update (no previous time to compare)
        if (first_update_) {
            last_update_time_ = now;
            first_update_ = false;
        } else if (timeout_seconds_ > 0.0f) {
            // Calculate time since last update
            auto dt = std::chrono::duration<float>(now - last_update_time_).count();
            
            // Reset if gap exceeds timeout
            if (dt > timeout_seconds_) {
                reset();
                timeout_occurred_ = true;
            } else {
                timeout_occurred_ = false;
            }
        }
        last_update_time_ = now;
        
        size_t position = next_position_ % MaxWindowSize;
        
        // If window has reached its configured size, remove oldest element from its heap
        if (window_.size() >= static_cast<std::size_t>(window_size_)) {
            SensorData<T, MaxWindowSize> oldest = window_.back();
            if (!lower_.removeByPosition(oldest.position)) {
                upper_.removeByPosition(oldest.position);
            }
            rebalance();
        }
        
        // Add new element
        SensorData<T, MaxWindowSize> new_data{new_value, position};
        window_.push(new_data);
        insertIntoHeap(new_data);
        
        next_position_++;
        
        // Median is top of lower_ (max-heap)
        if (!lower_.empty()) {
            return lower_.top().value;
        }
        return T{};
    }

    void reset() {
        window_.clear();
        lower_.clear();
        upper_.clear();
        next_position_ = 0;
        first_update_ = true;  // Reset first update flag so next update initializes timestamp
        timeout_occurred_ = false;
    }

    size_t windowSize() const { return window_size_; }
    size_t currentSize() const { return window_.size(); }
    size_t maxWindowSize() const { return MaxWindowSize; }
    
    void setWindowSize(size_t window_size) {
        if (window_size == 0) {
            throw std::invalid_argument("Window size must be positive");
        }
        if (window_size > MaxWindowSize) {
            throw std::invalid_argument(
                "Window size (" + std::to_string(window_size) + 
                ") exceeds MaxWindowSize (" + std::to_string(MaxWindowSize) + 
                "). Increase MaxWindowSize template parameter."
            );
        }
        window_size_ = window_size;
        lower_capacity_ = calculateLowerCapacity(window_size);
        upper_capacity_ = calculateUpperCapacity(window_size);
        lower_.setCapacity(lower_capacity_);
        upper_.setCapacity(upper_capacity_);
    }
    
    bool isFull() const { return window_.size() >= static_cast<std::size_t>(window_size_); }
    
    // Set timeout for reset on large dt gaps
    // timeout_seconds <= 0 disables timeout
    void set_timeout(float timeout_seconds) {
        if (timeout_seconds > 0.0f) {
            validate_timeout(timeout_seconds);
        }
        timeout_seconds_ = timeout_seconds;
    }
    
    // Get current timeout value
    // Returns <= 0 if timeout is disabled
    float get_timeout() const {
        return timeout_seconds_;
    }
    
    // Check if timeout is enabled
    bool has_timeout() const {
        return timeout_seconds_ > 0.0f;
    }
    
    // Check if a timeout occurred during the last update
    bool timeout_occurred() const {
        return timeout_occurred_;
    }
};

// =============================================================================
// Convenience type aliases
// =============================================================================

// Median filters with different maximum window sizes
// Note: Actual window size is now set at runtime via constructor
using MedianFilterIntSmall = MedianFilter<int, 101>;
using MedianFilterIntMedium = MedianFilter<int, 501>;
using MedianFilterIntLarge = MedianFilter<int, 1001>;

// Floating-point median filters
using MedianFilterFloatSmall = MedianFilter<float, 101>;
using MedianFilterFloatMedium = MedianFilter<float, 501>;
using MedianFilterFloatLarge = MedianFilter<float, 1001>;
