# Use ROS 2 Jazzy as the base image
FROM ros:jazzy-ros-base

# Set environment variables
ENV ROS_DOMAIN_ID=0
ENV ROS_LOCALHOST_ONLY=0

# Create and set the workspace directory
WORKDIR /workspace

# Configure .bashrc to source ROS 2 Jazzy and workspace setup
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc && \
    echo "export ROS_LOCALHOST_ONLY=0" >> ~/.bashrc && \
    echo "if [ -f /workspace/colcon_ws/install/setup.bash ]; then source /workspace/install/setup.bash; fi" >> ~/.bashrc

# Install additional dependencies (if any)
RUN apt-get update && apt-get install -y ros-jazzy-sensor-msgs