#pragma once

#include <cstddef>
#include <stdexcept>
#include <algorithm>
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
    RingBuffer<SensorData<T, MaxWindowSize>, MaxWindowSize> window_;
    FixedHeap<SensorData<T, MaxWindowSize>, (MaxWindowSize + 1) / 2, MaxWindowSize, true> lower_;   // Max-heap for lower half
    FixedHeap<SensorData<T, MaxWindowSize>, (MaxWindowSize + 1) / 2, MaxWindowSize, false> upper_;  // Min-heap for upper half
    size_t next_position_ = 0;
    size_t window_size_;
    size_t lower_capacity_;
    size_t upper_capacity_;

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

public:
    explicit MedianFilter(size_t window_size) 
        : window_size_(window_size),
          lower_(calculateLowerCapacity(window_size)),
          upper_(calculateUpperCapacity(window_size)),
          lower_capacity_(calculateLowerCapacity(window_size)),
          upper_capacity_(calculateUpperCapacity(window_size)) {
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
    }

    T update(T new_value) {
        size_t position = next_position_ % MaxWindowSize;
        
        // If window has reached its configured size, remove oldest element from its heap
        if (window_.size() >= window_size_) {
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
    
    bool isFull() const { return window_.size() >= window_size_; }
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

// Double median filters
using MedianFilterDoubleSmall = MedianFilter<double, 101>;
using MedianFilterDoubleMedium = MedianFilter<double, 501>;
using MedianFilterDoubleLarge = MedianFilter<double, 1001>;
