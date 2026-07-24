#pragma once

#include <cstddef>
#include <stdexcept>
#include <algorithm>
#include <functional>

// =============================================================================
// FixedPriorityQueue: A fixed-capacity priority queue with O(1) element removal
//
// Implements a heap-based priority queue using fixed-size arrays.
// Supports O(log n) push, pop, and O(log n) removal of arbitrary elements
// via position tracking.
//
// Key properties:
// - ZERO dynamic memory allocation (all storage is on stack/fixed arrays)
// - O(log n) push and pop
// - O(log n) removal by position
// - Configurable as max-heap or min-heap via comparator
// - Type-generic: works with any CopyConstructible type
// - Capacity is configurable at runtime (up to MaxCapacity template param)
//
// Template parameters:
// - T: The type of elements stored
// - MaxCapacity: Maximum possible capacity (compile-time)
// - Compare: Comparison function (defaults to std::less<T> for max-heap)
//
// Note: This requires elements to have a unique 'position' field for tracking.
// =============================================================================

template<typename T, size_t MaxCapacity, typename Compare = std::less<T>>
class FixedPriorityQueue {
private:
    T data_[MaxCapacity];
    size_t size_ = 0;
    size_t capacity_; // Runtime capacity (up to MaxCapacity)
    size_t position_map_[MaxCapacity]; // Maps element's position -> index in heap
    Compare comp_;
    
    // Get the position field from an element
    // Requires T to have a 'position' member
    size_t getPosition(const T& elem) const {
        return elem.position;
    }
    
    void heapifyUp(size_t index) {
        while (index > 0) {
            size_t parent = (index - 1) / 2;
            if (comp_(data_[index], data_[parent])) {
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
            
            if (left < size_ && comp_(data_[left], data_[target])) {
                target = left;
            }
            if (right < size_ && comp_(data_[right], data_[target])) {
                target = right;
            }
            
            if (target == index) break;
            
            std::swap(data_[index], data_[target]);
            position_map_[getPosition(data_[index])] = index;
            position_map_[getPosition(data_[target])] = target;
            index = target;
        }
    }
    
public:
    // Constructor with runtime capacity
    explicit FixedPriorityQueue(size_t capacity) : size_(0), capacity_(capacity), comp_(Compare()) {
        if (capacity == 0) {
            throw std::invalid_argument("FixedPriorityQueue: capacity must be positive");
        }
        if (capacity > MaxCapacity) {
            throw std::invalid_argument(
                "FixedPriorityQueue: capacity (" + std::to_string(capacity) + 
                ") exceeds MaxCapacity (" + std::to_string(MaxCapacity) + 
                "). Increase MaxCapacity template parameter."
            );
        }
        for (size_t i = 0; i < MaxCapacity; ++i) {
            position_map_[i] = MaxCapacity; // Invalid index marker
        }
    }
    
    // Constructor with runtime capacity and custom comparator
    explicit FixedPriorityQueue(size_t capacity, const Compare& comp) : size_(0), capacity_(capacity), comp_(comp) {
        if (capacity == 0) {
            throw std::invalid_argument("FixedPriorityQueue: capacity must be positive");
        }
        if (capacity > MaxCapacity) {
            throw std::invalid_argument(
                "FixedPriorityQueue: capacity (" + std::to_string(capacity) + 
                ") exceeds MaxCapacity (" + std::to_string(MaxCapacity) + 
                "). Increase MaxCapacity template parameter."
            );
        }
        for (size_t i = 0; i < MaxCapacity; ++i) {
            position_map_[i] = MaxCapacity;
        }
    }
    
    // Check if empty
    bool empty() const {
        return size_ == 0;
    }
    
    // Check if full
    bool full() const {
        return size_ >= capacity_;
    }
    
    // Get number of elements
    size_t size() const {
        return size_;
    }
    
    // Get current capacity
    size_t capacity() const {
        return capacity_;
    }
    
    // Get maximum capacity
    constexpr size_t maxCapacity() const {
        return MaxCapacity;
    }
    
    // Set capacity at runtime
    void setCapacity(size_t capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("FixedPriorityQueue: capacity must be positive");
        }
        if (capacity > MaxCapacity) {
            throw std::invalid_argument(
                "FixedPriorityQueue: capacity (" + std::to_string(capacity) + 
                ") exceeds MaxCapacity (" + std::to_string(MaxCapacity) + 
                "). Increase MaxCapacity template parameter."
            );
        }
        capacity_ = capacity;
    }
    
    // Access the top element (highest priority)
    const T& top() const {
        if (empty()) {
            throw std::runtime_error("FixedPriorityQueue: cannot access top of empty queue");
        }
        return data_[0];
    }
    
    // Push a new element
    // Returns true if successful, false if queue is full
    bool push(const T& value) {
        if (full()) {
            return false;
        }
        
        size_t pos = getPosition(value);
        if (pos >= MaxCapacity) {
            return false; // Invalid position
        }
        
        data_[size_] = value;
        position_map_[pos] = size_;
        heapifyUp(size_);
        size_++;
        return true;
    }
    
    // Pop the top element
    void pop() {
        if (empty()) {
            throw std::runtime_error("FixedPriorityQueue: cannot pop from empty queue");
        }
        
        size_t pos = getPosition(data_[0]);
        position_map_[pos] = MaxCapacity; // Clear mapping
        
        if (size_ > 1) {
            data_[0] = data_[size_ - 1];
            position_map_[getPosition(data_[0])] = 0;
        }
        
        size_--;
        if (size_ > 0) {
            heapifyDown(0);
        }
    }
    
    // Remove element by its position (O(log n))
    // Returns true if element was found and removed
    bool removeByPosition(size_t position) {
        if (position >= MaxCapacity) {
            return false;
        }
        
        size_t index = position_map_[position];
        if (index >= size_) {
            return false; // Not in heap or already invalid
        }
        
        position_map_[position] = MaxCapacity; // Clear mapping
        
        // If removing the last element, just decrement size
        if (index == size_ - 1) {
            size_--;
            return true;
        }
        
        // Move last element to this position
        data_[index] = data_[size_ - 1];
        position_map_[getPosition(data_[index])] = index;
        size_--;
        
        // Heapify from this position (might need to go up or down)
        if (index < size_) {
            heapifyUp(index);
            heapifyDown(index);
        }
        
        return true;
    }
    
    // Check if an element with given position exists in the queue
    bool containsPosition(size_t position) const {
        if (position >= MaxCapacity) {
            return false;
        }
        return position_map_[position] < size_;
    }
    
    // Clear all elements
    void clear() {
        size_ = 0;
        for (size_t i = 0; i < MaxCapacity; ++i) {
            position_map_[i] = MaxCapacity;
        }
    }
};

// =============================================================================
// Convenience type aliases
// =============================================================================

// Max-heap versions (largest element on top)
// Note: Actual capacity is now set at runtime via constructor
template<typename T, size_t MaxCapacity>
using MaxHeap = FixedPriorityQueue<T, MaxCapacity, std::less<T>>;

// Min-heap versions (smallest element on top)
// Note: Actual capacity is now set at runtime via constructor
template<typename T, size_t MaxCapacity>
using MinHeap = FixedPriorityQueue<T, MaxCapacity, std::greater<T>>;
