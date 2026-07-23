# =============================================================================
# Multi-stage Dockerfile for naweRobotics
# Stage 1: Build custom_lib C++/Python extensions
# Stage 2: Final ROS 2 Jazzy image with built libraries
# =============================================================================

# ========================================================================
# Stage 1: Build custom_lib
# ========================================================================
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /workspace/custom_lib

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    pip \
    setuptools \
    wheel \
    pybind11>=2.10.0 \
    pytest

# Copy custom_lib source
COPY custom_lib/ .

# Create build directory and configure
RUN mkdir -p build && cd build && \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTS=OFF \
        -DCMAKE_INSTALL_PREFIX=/tmp/installed_libs

# Build the library
RUN cd build && cmake --build . -j$(nproc)

# Install the Python modules to a temporary location
RUN cd build && cmake --install . && \
    # Move Python modules to site-packages for proper Python import
    mkdir -p /tmp/installed_libs/lib/python3.10/site-packages && \
    mv /tmp/installed_libs/lib/py_filter* /tmp/installed_libs/lib/python3.10/site-packages/ 2>/dev/null || true && \
    mv /tmp/installed_libs/lib/py_moving_average* /tmp/installed_libs/lib/python3.10/site-packages/ 2>/dev/null || true

# ========================================================================
# Stage 2: Final ROS 2 Jazzy Image
# ========================================================================
FROM ros:jazzy-ros-base

# Set environment variables
ENV ROS_DOMAIN_ID=0
ENV ROS_LOCALHOST_ONLY=0
ENV PYTHONUNBUFFERED=1

# Create workspace directory
WORKDIR /workspace

# Copy the built libraries from builder stage
COPY --from=builder /tmp/installed_libs /usr/local

# Install ROS 2 dependencies
RUN apt-get update && apt-get install -y \
    ros-jazzy-sensor-msgs \
    python3-colcon-common-extensions \
    python3-rosdep2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for ROS 2
RUN pip install --no-cache-dir \
    setuptools \
    pybind11>=2.10.0

# Copy the custom_lib source (for development)
COPY custom_lib/ ./custom_lib/

# Configure .bashrc for ROS 2 and workspace
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc && \
    echo "export ROS_LOCALHOST_ONLY=0" >> ~/.bashrc && \
    echo "if [ -f /workspace/colcon_ws/install/setup.bash ]; then source /workspace/colcon_ws/install/setup.bash; fi" >> ~/.bashrc && \
    echo "export PYTHONPATH=/usr/local/lib/python3.10/site-packages:/usr/local/lib:$PYTHONPATH" >> ~/.bashrc

# ========================================================================
# Alternative: Build from source in final image
# (Uncomment if you want to build fresh instead of copying from builder)
# ========================================================================
#
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     cmake \
#     git \
#     python3-dev \
#     python3-pip \
#     && rm -rf /var/lib/apt/lists/*
#
# RUN pip install --no-cache-dir pybind11>=2.10.0
#
# WORKDIR /workspace/custom_lib
# RUN mkdir -p build && cd build && \
#     cmake .. -DCMAKE_BUILD_TYPE=Release && \
#     cmake --build . -j$(nproc) && \
#     cmake --install . --prefix /usr/local

# ========================================================================
# Default command
# ========================================================================
CMD ["bash"]