/**
 * Fixed Window Moving Average Processing Node for Signal Processing Pipeline
 * 
 * This node subscribes to integer and floating-point sensor streams,
 * applies FIXED WINDOW moving average filters using the standalone C++ library,
 * and publishes the filtered results.
 * 
 * Requirements:
 * - The custom_lib must be built and accessible
 * - ROS2 environment properly sourced
 * 
 * Usage:
 *     ros2 run signal_processing_cpp fixed_ma_node
 *     
 *     # With parameters
 *     ros2 run signal_processing_cpp fixed_ma_node --ros-args -p ma_window_size:=10 -p timeout_seconds:=0.15
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/float32.hpp>
#include <chrono>
#include <memory>

// Include the standalone signal processing library headers for moving average
#include "nawe_robotics_lib/running_data/lib/fixed_moving_average.hpp"

using namespace std::chrono_literals;

class FixedMANode : public rclcpp::Node {
public:
    FixedMANode()
        : Node("fixed_ma_node")
    {
        // Declare parameters with defaults
        this->declare_parameter<int>("ma_window_size", 5);
        this->declare_parameter<float>("timeout_seconds", 0.15f);  // 150ms timeout for dropout gaps

        // Get parameter values
        int ma_window_size = this->get_parameter("ma_window_size").as_int();
        float timeout_seconds = this->get_parameter("timeout_seconds").as_float();

        RCLCPP_INFO(this->get_logger(), 
                   "Fixed MA Parameters: window size=%d, timeout=%.3fs",
                   ma_window_size, timeout_seconds);

        // Initialize fixed moving average filter for accel with timeout
        // Use largest available buffer size (LARGE_BUFFER = 10000) for maximum capacity
        ma_accel_ = std::make_unique<FixedMovingAverage<float, 10000>>(ma_window_size, timeout_seconds);

        RCLCPP_INFO(this->get_logger(), "Fixed moving average filter created for accel with timeout");
        RCLCPP_INFO(this->get_logger(), "  Encoder: passthrough (no filtering)");

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
        ma_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("fixed_ma_encoder", 10);
        ma_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("fixed_ma_accel", 10);

        RCLCPP_INFO(this->get_logger(), "Fixed MA node initialized");
        RCLCPP_INFO(this->get_logger(), "Subscribed to: /encoder_count, /accel_x_mss");
        RCLCPP_INFO(this->get_logger(), "Publishing to: /fixed_ma_encoder, /fixed_ma_accel");
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
        
        // Publish raw value to fixed_ma_encoder topic
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
        float value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = (current_time - last_accel_time_).seconds();
        last_accel_time_ = current_time;
        
        // Apply fixed moving average
        float ma_result = ma_accel_->update(value);
        
        // Increment counter
        accel_update_count_++;
        
        // Publish results
        auto ma_msg = std_msgs::msg::Float32();
        ma_msg.data = ma_result;
        ma_accel_pub_->publish(ma_msg);
        
        // Log occasionally
        if (accel_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Accel fixed MA: raw=%.3f, ma=%.3f, dt=%.3fs",
                         value, ma_result, dt);
        }
    }

    // Subscribers
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr encoder_sub_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr accel_sub_;

    // Publishers
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr ma_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr ma_accel_pub_;

    // Filter instances - fixed moving average with largest buffer (10000)
    std::unique_ptr<FixedMovingAverage<float, 10000>> ma_accel_;
    
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
    auto node = std::make_shared<FixedMANode>();
    
    rclcpp::spin(node);
    rclcpp::shutdown();
    
    return 0;
}
