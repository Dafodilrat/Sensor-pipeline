#pragma once

#include <cstddef>
#include <stdexcept>
#include <algorithm>

// =============================================================================
// FixedHeap: A fixed-size heap implementation with position tracking
//
// Features:
// - Fixed maximum capacity (no dynamic memory allocation)
// - O(log n) insertion, removal, and access
// - Position tracking for efficient removal of arbitrary elements
// - Configurable as max-heap or min-heap via template parameter
// - Position map size matches the position space, not the heap capacity
// - Capacity is configurable at runtime (up to MaxCapacity template param)
// =============================================================================

template<typename T, size_t MaxCapacity, size_t PositionSpace, bool IsMaxHeap = true>
class FixedHeap {
private:
    T data_[MaxCapacity];
    size_t size_ = 0;
    size_t capacity_; // Runtime capacity (up to MaxCapacity)
    size_t position_map_[PositionSpace]; // Maps position -> heap index
    
    void heapifyUp(size_t index) {
        while (index > 0) {
            size_t parent = (index - 1) / 2;
            if (compare_(data_[index], data_[parent])) {
                std::swap(data_[parent], data_[index]);
                position_map_[getPosition(data_[parent])] = parent;
                position_map_[getPosition(data_[index])] = index;
                index = parent;
            } else {
                break;
            }
        }
    }
    
    void heapifyDown(size_t index) {
        while (true) {
            size_t left = 2 * index + 1;
            size_t right = 2 * index + 2;
            size_t target = index;
            
            if (left < size_ && compare_(data_[left], data_[target])) {
                target = left;
            }
            if (right < size_ && compare_(data_[right], data_[target])) {
                target = right;
            }
            
            if (target == index) break;
            
            std::swap(data_[index], data_[target]);
            position_map_[getPosition(data_[index])] = index;
            position_map_[getPosition(data_[target])] = target;
            index = target;
        }
    }
    
    // Comparison function based on heap type
    static bool compare_(const T& a, const T& b) {
        if (IsMaxHeap) {
            return a > b; // Max-heap: parent > children
        } else {
            return a < b; // Min-heap: parent < children
        }
    }
    
    // Helper to extract position from the stored type
    // This requires T to have a 'position' member
    static size_t getPosition(const T& item) {
        return item.position;
    }
    
public:
    explicit FixedHeap(size_t capacity) : size_(0), capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("FixedHeap: capacity must be positive");
        }
        if (capacity > MaxCapacity) {
            throw std::invalid_argument(
                "FixedHeap: capacity (" + std::to_string(capacity) + 
                ") exceeds MaxCapacity (" + std::to_string(MaxCapacity) + 
                "). Increase MaxCapacity template parameter."
            );
        }
        for (size_t i = 0; i < PositionSpace; ++i) {
            position_map_[i] = MaxCapacity; // Invalid
        }
    }
    
    void push(const T& val) {
        if (size_ >= capacity_) return;
        data_[size_] = val;
        position_map_[getPosition(val)] = size_;
        heapifyUp(size_);
        size_++;
    }
    
    T top() const {
        if (size_ == 0) throw std::runtime_error("Heap is empty");
        return data_[0];
    }
    
    void pop() {
        if (size_ == 0) return;
        position_map_[getPosition(data_[0])] = MaxCapacity;
        if (size_ > 1) {
            data_[0] = data_[size_ - 1];
            position_map_[getPosition(data_[0])] = 0;
        }
        size_--;
        if (size_ > 0) {
            heapifyDown(0);
        }
    }
    
    // Remove element at given position (O(log n))
    bool removeByPosition(size_t position) {
        if (position >= PositionSpace) return false;
        
        size_t index = position_map_[position];
        if (index >= size_) return false;
        
        position_map_[position] = MaxCapacity; // Clear mapping
        
        // Move last element to this position
        if (index < size_ - 1) {
            data_[index] = data_[size_ - 1];
            position_map_[getPosition(data_[index])] = index;
        }
        size_--;
        
        // Heapify from this position
        if (index < size_) {
            heapifyUp(index);
            heapifyDown(index);
        }
        
        return true;
    }
    
    void clear() {
        size_ = 0;
        for (size_t i = 0; i < PositionSpace; ++i) {
            position_map_[i] = MaxCapacity;
        }
    }
    
    size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
    
    // Get current capacity
    size_t capacity() const { return capacity_; }
    
    // Get maximum capacity
    constexpr size_t maxCapacity() const { return MaxCapacity; }
    
    // Set capacity at runtime
    void setCapacity(size_t capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("FixedHeap: capacity must be positive");
        }
        if (capacity > MaxCapacity) {
            throw std::invalid_argument(
                "FixedHeap: capacity (" + std::to_string(capacity) + 
                ") exceeds MaxCapacity (" + std::to_string(MaxCapacity) + 
                "). Increase MaxCapacity template parameter."
            );
        }
        capacity_ = capacity;
    }
};
