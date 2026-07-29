/**
 * Low Pass Filter Processing Node for Signal Processing Pipeline
 * 
 * This node subscribes to integer and floating-point sensor streams,
 * applies low-pass filters using the standalone C++ library,
 * and publishes the filtered results.
 * 
 * Requirements:
 * - The custom_lib must be built and accessible
 * - ROS2 environment properly sourced
 * 
 * Usage:
 *     ros2 run signal_processing_cpp lp_node
 *       
 *     # With parameters
 *     ros2 run signal_processing_cpp lp_node --ros-args -p lp_cutoff_hz:=10.0 -p fixed_point_bits:=16 -p timeout_seconds:=10.0
 */

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/float32.hpp>
#include <chrono>
#include <memory>

// Include the standalone signal processing library headers
// Installed to /usr/local/include/nawe_robotics_lib via Docker
#include "nawe_robotics_lib/filters/lib/fixed_point_low_pass_filter.hpp"
#include "nawe_robotics_lib/filters/lib/low_pass_iir_filter.hpp"

using namespace std::chrono_literals;

class LPNode : public rclcpp::Node {
public:
    LPNode()
        : Node("lp_node")
    {
        // Declare parameters with defaults
        this->declare_parameter<double>("lp_cutoff_hz", 10.0);
        this->declare_parameter<int>("fixed_point_bits", 16);
        this->declare_parameter<double>("timeout_seconds", 10.0);

        // Get parameter values
        double lp_cutoff_hz = this->get_parameter("lp_cutoff_hz").as_double();
        int fixed_point_bits = this->get_parameter("fixed_point_bits").as_int();
        double timeout_seconds = this->get_parameter("timeout_seconds").as_double();

        RCLCPP_INFO(this->get_logger(), 
                   "LP Parameters: cutoff=%.1fHz, FP bits=%d, timeout=%.3fs",
                   lp_cutoff_hz, fixed_point_bits, timeout_seconds);

        // Convert parameters to the format expected by the new filter classes
        // cutoff_freq_times_100 is int32_t (e.g., 1000 = 10.00 Hz)
        // timeout_ns is int64_t in nanoseconds
        int32_t cutoff_freq_times_100 = static_cast<int32_t>(lp_cutoff_hz * 100.0);
        int64_t timeout_ns = static_cast<int64_t>(timeout_seconds * 1e9);

        // Initialize low-pass filters based on fixed-point bits
        // For encoder (integer) stream, use fixed-point filter with appropriate Q-format
        if (fixed_point_bits == 8) {
            // Q24.8 format
            lp_encoder_24_8_ = std::make_unique<FixedPointLowPassFilter_24_8>(cutoff_freq_times_100, 8, timeout_ns);
            active_encoder_filter_ = 8;
        } else {
            // Q16.16 format (default for 16, 24, 30, or any other value)
            lp_encoder_16_16_ = std::make_unique<FixedPointLowPassFilter_16_16>(cutoff_freq_times_100, 16, timeout_ns);
            active_encoder_filter_ = 16;
        }

        // For accel (float) stream, use float filter
        // Note: LowPassFilterDouble uses Hz and seconds (not times_100 and ns)
        lp_accel_ = std::make_unique<LowPassFilterDouble>(lp_cutoff_hz, timeout_seconds);

        RCLCPP_INFO(this->get_logger(), "Low-pass filters created");
        RCLCPP_INFO(this->get_logger(), "  Encoder LP: FixedPointLowPassFilter (Q%d.%d)", 
                   (32 - active_encoder_filter_), active_encoder_filter_);
        RCLCPP_INFO(this->get_logger(), "  Accel LP: LowPassFilterDouble");

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
        lp_encoder_pub_ = this->create_publisher<std_msgs::msg::Int32>("lp_encoder", 10);
        lp_accel_pub_ = this->create_publisher<std_msgs::msg::Float32>("lp_accel", 10);

        RCLCPP_INFO(this->get_logger(), "C++ LP node initialized");
        RCLCPP_INFO(this->get_logger(), "Subscribed to: /encoder_count, /accel_x_mss");
        RCLCPP_INFO(this->get_logger(), "Publishing to: /lp_encoder, /lp_accel");
    }

private:
    void encoder_callback(const std_msgs::msg::Int32::SharedPtr msg) {
        auto current_time = this->now();
        int32_t value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = (current_time - last_encoder_time_).seconds();
        last_encoder_time_ = current_time;
        
        // Apply low-pass filter based on which type is active
        // Using update() without timestamp - uses system clock internally
        int32_t lp_result = 0;
        switch (active_encoder_filter_) {
            case 8:
                lp_result = lp_encoder_24_8_->update(value);
                break;
            case 16:
                lp_result = lp_encoder_16_16_->update(value);
                break;
            default:
                // Fallback to simple update without timestamp
                lp_result = value;
                break;
        }
        
        // Increment counter
        encoder_update_count_++;
        
        // Publish results
        auto lp_msg = std_msgs::msg::Int32();
        lp_msg.data = lp_result;
        lp_encoder_pub_->publish(lp_msg);
        
        // Log occasionally
        if (encoder_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Encoder LP: raw=%d, lp=%d, dt=%.3fs",
                         value, lp_result, dt);
        }
    }

    void accel_callback(const std_msgs::msg::Float32::SharedPtr msg) {
        auto current_time = this->now();
        double value = msg->data;
        
        // Calculate dt if we have a previous timestamp
        double dt = (current_time - last_accel_time_).seconds();
        last_accel_time_ = current_time;
        
        // Apply low-pass filter
        // Using update() without timestamp - uses system clock internally
        double lp_result = lp_accel_->update(value);
        
        // Increment counter
        accel_update_count_++;
        
        // Publish results
        auto lp_msg = std_msgs::msg::Float32();
        lp_msg.data = static_cast<float>(lp_result);
        lp_accel_pub_->publish(lp_msg);
        
        // Log occasionally
        if (accel_update_count_ % 10 == 0) {
            RCLCPP_DEBUG(this->get_logger(), "Accel LP: raw=%.3f, lp=%.3f, dt=%.3fs",
                         value, lp_result, dt);
        }
    }

    // Subscribers
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr encoder_sub_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr accel_sub_;

    // Publishers
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr lp_encoder_pub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr lp_accel_pub_;

    // Filter instances
    // Low-pass filter for encoder (integer) - multiple Q-format options
    std::unique_ptr<FixedPointLowPassFilter_24_8> lp_encoder_24_8_;
    std::unique_ptr<FixedPointLowPassFilter_16_16> lp_encoder_16_16_;
    
    // Low-pass filter for accel (float)
    std::unique_ptr<LowPassFilterDouble> lp_accel_;
    
    // Track which encoder filter is active
    int active_encoder_filter_ = 16; // 8 or 16

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
    auto node = std::make_shared<LPNode>();
    
    rclcpp::spin(node);
    rclcpp::shutdown();
    
    return 0;
}
