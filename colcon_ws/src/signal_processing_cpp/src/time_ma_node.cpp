/**
 * Time Duration Moving Average Processing Node for Signal Processing Pipeline
 * 
 * This node subscribes to integer and floating-point sensor streams,
 * applies TIME DURATION moving average filters using the standalone C++ library,
 * and publishes the filtered results.
 * 
 * Requirements:
 * - The custom_lib must be built and accessible
 * - ROS2 environment properly sourced
 * 
 * Usage:
 *     ros2 run signal_processing_cpp time_ma_node
 *     
 *     # With parameters
 *     ros2 run signal_processing_cpp time_ma_node --ros-args -p ma_window_size:=10 -p ma_window_duration_ms:=200 -p timeout_seconds:=0.15
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/float32.hpp>
#include <chrono>
#include <memory>

// Include the standalone signal processing library headers for moving average
#include "nawe_robotics_lib/running_data/lib/time_duration_moving_average.hpp"

using namespace std::chrono_literals;

class TimeMANode : public rclcpp::Node {
public:
    TimeMANode()
        : Node("time_ma_node")
    {
        // Declare parameters with defaults
        this->declare_parameter<int>("ma_window_size", 5);
        this->declare_parameter<double>("ma_window_duration_ms", 200.0);
        this->declare_parameter<double>("timeout_seconds", 0.15);  // 150ms timeout for dropout gaps

        // Get parameter values
        int ma_window_size = this->get_parameter("ma_window_size").as_int();
        double ma_window_duration_ms = this->get_parameter("ma_window_duration_ms").as_double();
        double timeout_seconds = this->get_parameter("timeout_seconds").as_double();

        RCLCPP_INFO(this->get_logger(), 
                   "Time MA Parameters: window size=%d, duration=%.1fms, timeout=%.3fs",
                   ma_window_size, ma_window_duration_ms, timeout_seconds);

        // Initialize time duration moving average filters with timeout
        // Use largest available buffer size (LARGE_BUFFER = 10000) for maximum capacity
        ma_encoder_ = std::make_unique<TimeDurationMovingAverage<int, 10000>>(
            ma_window_size, std::chrono::milliseconds(static_cast<int>(ma_window_duration_ms)), timeout_seconds);
        ma_accel_ = std::make_unique<TimeDurationMovingAverage<double, 10000>>(
            ma_window_size, std::chrono::milliseconds(static_cast<int>(ma_window_duration_ms)), timeout_seconds);

        RCLCPP_INFO(this->get_logger(), "Time duration moving average filters created with timeout");

        // Create subscribers
        encoder_sub_ = this->create_subscription<std_msgs::msg::Int32>(
            "encoder_count", 10, 
            [this](const std_msgs::msg::Int32::SharedPtr msg) {
                this->encoder_callback(msg);
            });

        accel_sub_ = this->create_subscription<std_msgs::msg::Float32>(
            "accel_x_mss", 10, 
            [this](const std_msgs::msg::Float32::SharedPtr msg) {
                this->accel_callback(msg);
            });

        // Create publishers
        ma_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("time_ma_encoder", 10);
        ma_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("time_ma_accel", 10);

        RCLCPP_INFO(this->get_logger(), "Time MA node initialized");
        RCLCPP_INFO(this->get_logger(), "Subscribed to: /encoder_count, /accel_x_mss");
        RCLCPP_INFO(this->get_logger(), "Publishing to: /time_ma_encoder, /time_ma_accel");
    }

private:
    void encoder_callback(const std_msgs::msg::Int32::SharedPtr msg) {
        auto current_time = this->now();
        int32_t value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = (current_time - last_encoder_time_).seconds();
        last_encoder_time_ = current_time;
        
        // Pass through raw value without filtering for encoder motor topic
        int32_t ma_result = value;
        
        // Increment counter
        encoder_update_count_++;
        
        // Publish raw value to time_ma_encoder topic
        auto ma_msg = std_msgs::msg::Int32();
        ma_msg.data = ma_result;
        ma_encoder_pub_->publish(ma_msg);
        
        // Log occasionally
        if (encoder_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Encoder passthrough: raw=%d, published=%d, dt=%.3fs",
                         value, ma_result, dt);
        }
    }

    void accel_callback(const std_msgs::msg::Float32::SharedPtr msg) {
        auto current_time = this->now();
        double value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = (current_time - last_accel_time_).seconds();
        last_accel_time_ = current_time;
        
        // Apply time-based moving average
        // Note: timestamps are managed internally by the filter
        double ma_result = ma_accel_->update(value);
        
        // Increment counter
        accel_update_count_++;
        
        // Publish results
        auto ma_msg = std_msgs::msg::Float32();
        ma_msg.data = static_cast<float>(ma_result);
        ma_accel_pub_->publish(ma_msg);
        
        // Log occasionally
        if (accel_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Accel time MA: raw=%.3f, ma=%.3f, dt=%.3fs",
                         value, ma_result, dt);
        }
    }

    // Subscribers
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr encoder_sub_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr accel_sub_;

    // Publishers
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr ma_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr ma_accel_pub_;

    // Filter instances - time duration moving average with largest buffer (10000)
    std::unique_ptr<TimeDurationMovingAverage<int, 10000>> ma_encoder_;
    std::unique_ptr<TimeDurationMovingAverage<double, 10000>> ma_accel_;
    
    // Timestamps for dt calculation
    rclcpp::Time last_encoder_time_ = this->now();
    rclcpp::Time last_accel_time_ = this->now();
    
    // Counters for occasional logging
    size_t encoder_update_count_ = 0;
    size_t accel_update_count_ = 0;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<TimeMANode>();
    
    rclcpp::spin(node);
    rclcpp::shutdown();
    
    return 0;
}
