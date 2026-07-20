#include <iostream>
#include <chrono>
#include <thread>
#include "mavg.cpp"

int main() {
    std::cout << "=== Moving Average Library Test ===" << std::endl;

    // Test 1: Fixed Moving Average
    std::cout << "\n1. Testing FixedMovingAverage (window size = 5)" << std::endl;
    FixedMovingAverage<double, 10> fixedMA(5);
    
    std::cout << "Adding values: 1, 2, 3, 4, 5" << std::endl;
    std::cout << "Average: " << fixedMA.update(1.0) << std::endl;
    std::cout << "Average: " << fixedMA.update(2.0) << std::endl;
    std::cout << "Average: " << fixedMA.update(3.0) << std::endl;
    std::cout << "Average: " << fixedMA.update(4.0) << std::endl;
    std::cout << "Average: " << fixedMA.update(5.0) << std::endl;
    
    std::cout << "Current size: " << fixedMA.currentSize() << std::endl;
    std::cout << "Capacity: " << fixedMA.capacity() << std::endl;
    
    std::cout << "\nAdding value 6 (should remove 1 from window)" << std::endl;
    std::cout << "Average: " << fixedMA.update(6.0) << std::endl;
    
    std::cout << "\nResetting..." << std::endl;
    fixedMA.reset();
    std::cout << "Current size after reset: " << fixedMA.currentSize() << std::endl;

    // Test 2: Time Duration Moving Average with Hz and duration
    std::cout << "\n2. Testing TimeDurationMovingAverage with sensor Hz" << std::endl;
    // 100Hz sensor, 200ms window -> calculated window size = ceil(100 * 0.2) * 1.2 = 24
    TimeDurationMovingAverage<double, 100> timeMA(100.0, std::chrono::milliseconds(200));
    
    std::cout << "Sensor Hz: " << timeMA.getSensorHz() << std::endl;
    std::cout << "Window duration: " << timeMA.getWindowDuration().count() << "ms" << std::endl;
    std::cout << "Calculated window size: " << timeMA.getCalculatedWindowSize() << std::endl;
    std::cout << "Actual buffer capacity: " << timeMA.capacity() << std::endl;
    
    std::cout << "\nAdding values every 10ms (simulating 100Hz sensor)..." << std::endl;
    for (int i = 1; i <= 10; i++) {
        std::cout << "Adding " << i << " - Average: " << timeMA.update(i) << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    
    std::cout << "\nCurrent size: " << timeMA.currentSize() << std::endl;
    
    std::cout << "\nWaiting 250ms for samples to expire..." << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
    std::cout << "Current size after waiting: " << timeMA.currentSize() << std::endl;
    
    std::cout << "\nChanging parameters to 50Hz, 300ms window" << std::endl;
    timeMA.setParameters(50.0, std::chrono::milliseconds(300));
    std::cout << "New sensor Hz: " << timeMA.getSensorHz() << std::endl;
    std::cout << "New window duration: " << timeMA.getWindowDuration().count() << "ms" << std::endl;
    std::cout << "New calculated window size: " << timeMA.getCalculatedWindowSize() << std::endl;
    
    std::cout << "\nResetting..." << std::endl;
    timeMA.reset();
    std::cout << "Current size after reset: " << timeMA.currentSize() << std::endl;

    // Test 3: Using factory methods
    std::cout << "\n3. Testing Factory Methods" << std::endl;
    auto fixedFromFactory = MovingAverageFactory::createFixedAverage<double, 10>(3);
    auto timeFromFactory = MovingAverageFactory::createTimeDurationAverage<double, 100>(50.0, std::chrono::milliseconds(100));
    
    std::cout << "Factory fixed MA: " << fixedFromFactory.update(10.0) << std::endl;
    std::cout << "Factory time MA: " << timeFromFactory.update(20.0) << std::endl;
    std::cout << "Factory time MA calculated size: " << timeFromFactory.getCalculatedWindowSize() << std::endl;

    // Test 4: Integer rounding
    std::cout << "\n4. Testing Integer Rounding" << std::endl;
    FixedMovingAverage<int, 5> intMA(3);
    std::cout << "Adding: 1 (-> " << intMA.update(1) << ")" << std::endl;
    std::cout << "Adding: 2 (-> " << intMA.update(2) << ")" << std::endl;
    std::cout << "Adding: 3 (-> " << intMA.update(3) << ")" << std::endl;

    // Test 5: RingBuffer standalone usage
    std::cout << "\n5. Testing RingBuffer standalone" << std::endl;
    RingBuffer<int, 5> ringBuf;
    ringBuf.push(10);
    ringBuf.push(20);
    ringBuf.push(30);
    std::cout << "RingBuffer size: " << ringBuf.size() << ", front: " << ringBuf.front() << std::endl;

    std::cout << "\n=== All tests completed ===" << std::endl;
    return 0;
}
