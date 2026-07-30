# =============================================================================
# Multi-stage Dockerfile for naweRobotics
# Stage 1: Build custom_lib as pip-installable Python package with CMake config
# Stage 2: Final ROS 2 Jazzy image with pip-installed package and colcon workspace
# =============================================================================

# ========================================================================
# Stage 1: Build custom_lib as pip package with CMake config
# ========================================================================
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /workspace/custom_lib

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python build dependencies
RUN pip install --no-cache-dir \
    pip \
    setuptools \
    wheel \
    pytest \
    build

# Copy custom_lib source
COPY custom_lib/ .

# Build the Python package as a wheel
RUN python -m build --wheel --outdir /tmp/wheels

# Copy CMake config files and headers to install location
RUN mkdir -p /usr/local/include/nawe_robotics_lib/filters/lib && \
    mkdir -p /usr/local/include/nawe_robotics_lib/running_data/lib && \
    mkdir -p /usr/local/include/nawe_robotics_lib/tools && \
    cp -r /workspace/custom_lib/filters/lib/* /usr/local/include/nawe_robotics_lib/filters/lib/ && \
    cp -r /workspace/custom_lib/running_data/lib/* /usr/local/include/nawe_robotics_lib/running_data/lib/ && \
    cp -r /workspace/custom_lib/tools/* /usr/local/include/nawe_robotics_lib/tools/ && \
    mkdir -p /usr/local/include/fpm && \
    cp -r /workspace/custom_lib/third_party/fpm/include/fpm/* /usr/local/include/fpm/ && \
    mkdir -p /usr/local/lib/cmake/nawe_robotics_lib && \
    cp /workspace/custom_lib/cmake/nawe_robotics_libConfig.cmake /usr/local/lib/cmake/nawe_robotics_lib/ && \
    cp /workspace/custom_lib/cmake/nawe_robotics_libConfigVersion.cmake /usr/local/lib/cmake/nawe_robotics_lib/ && \
    echo "Builder stage - verifying paths:" && \
    ls -la /usr/local/include/nawe_robotics_lib/filters/lib/ && \
    ls -la /usr/local/include/nawe_robotics_lib/running_data/lib/ && \
    ls -la /usr/local/include/nawe_robotics_lib/tools/ && \
    ls -la /usr/local/include/fpm/

# ========================================================================
# Stage 2: Final ROS 2 Jazzy Image
# ========================================================================
FROM osrf/ros:jazzy-desktop

# Set environment variables (also set them directly for non-interactive shells)
ENV ROS_DOMAIN_ID=0
ENV ROS_LOCALHOST_ONLY=0
ENV PYTHONUNBUFFERED=1
ENV CMAKE_PREFIX_PATH=/opt/ros/jazzy:/usr/local/lib/cmake:$CMAKE_PREFIX_PATH
ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages:$PYTHONPATH
ENV AMENT_PREFIX_PATH=/opt/ros/jazzy
ENV LD_LIBRARY_PATH=/opt/ros/jazzy/lib:$LD_LIBRARY_PATH

# Create workspace directory
WORKDIR /workspace

# Copy the built wheel, headers, and CMake config from builder stage
COPY --from=builder /tmp/wheels /tmp/wheels
COPY --from=builder /usr/local/include/nawe_robotics_lib /usr/local/include/nawe_robotics_lib
COPY --from=builder /usr/local/include/fpm /usr/local/include/fpm
COPY --from=builder /usr/local/lib/cmake/nawe_robotics_lib /usr/local/lib/cmake/nawe_robotics_lib

# Verify header paths exist in final image
RUN echo "Verifying final header paths..." && \
    ls -la /usr/local/include/nawe_robotics_lib/filters/lib/ && \
    ls -la /usr/local/include/nawe_robotics_lib/running_data/lib/ && \
    ls -la /usr/local/include/nawe_robotics_lib/tools/ && \
    ls -la /usr/local/include/fpm/

# Install ROS 2 dependencies
RUN apt-get update && apt-get install -y \
    ros-jazzy-sensor-msgs \
    ros-jazzy-rclcpp \
    ros-jazzy-std-msgs \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    cmake \
    build-essential \
    python3-dev \
    libeigen3-dev \ 
    # ros-jazzy-eigen3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --break-system-packages \
    setuptools \
    wheel \
    pytest \
    pybind11>=2.6.0 \
    numpy

# Install the custom_lib Python package from wheel
RUN pip install --no-cache-dir --break-system-packages /tmp/wheels/nawe_robotics_lib-*.whl

# Create entrypoint that sources ROS 2 environment
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo 'source /opt/ros/jazzy/setup.bash' >> /entrypoint.sh && \
    echo 'if [ -f /workspace/colcon_ws/install/setup.bash ]; then source /workspace/colcon_ws/install/setup.bash; fi' >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Append to the global system profile instead of /root/.bashrc
RUN printf '%s\n' \
    'source /opt/ros/jazzy/setup.bash' \
    'export ROS_DOMAIN_ID=0' \
    'export ROS_LOCALHOST_ONLY=0' \
    'export PYTHONUNBUFFERED=1' \
    'export CMAKE_PREFIX_PATH=/usr/local/lib/cmake:$CMAKE_PREFIX_PATH' \
    'export PYTHONPATH=/usr/local/lib/python3.12/site-packages:$PYTHONPATH' \
    'if [ -f /workspace/colcon_ws/install/setup.bash ]; then' \
    '    source /workspace/colcon_ws/install/setup.bash' \
    'fi' >> /etc/bash.bashrc

