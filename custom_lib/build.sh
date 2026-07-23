#!/bin/bash

# =============================================================================
# Build script for naweRobotics filter library
# =============================================================================

set -e  # Exit on error

# Default build type
BUILD_TYPE="Release"

# Default build directory
BUILD_DIR="build"

# Default install prefix
INSTALL_PREFIX=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --release)
            BUILD_TYPE="Release"
            shift
            ;;
        --relwithdebinfo)
            BUILD_TYPE="RelWithDebInfo"
            shift
            ;;
        --build-dir)
            BUILD_DIR="$2"
            shift 2
            ;;
        --install)
            INSTALL_PREFIX="$2"
            shift 2
            ;;
        --clean)
            rm -rf "$BUILD_DIR"
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --debug              Build with debug symbols"
            echo "  --release            Build with optimizations (default)"
            echo "  --relwithdebinfo    Build with optimizations and debug symbols"
            echo "  --build-dir DIR      Use DIR as build directory (default: build)"
            echo "  --install PREFIX     Install to PREFIX after building"
            echo "  --clean              Remove build directory and exit"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for available options"
            exit 1
            ;;
    esac
done

# Check CMake is available
if ! command -v cmake &> /dev/null; then
    echo "Error: CMake is not installed"
    echo "Please install CMake 3.15 or higher"
    exit 1
fi

# Check C++17 compiler
if ! c++ --version &> /dev/null; then
    echo "Error: C++ compiler not found"
    echo "Please install a C++17 compatible compiler"
    exit 1
fi

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure
 echo "Configuring build with type: $BUILD_TYPE"
cmake .. -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# Build
echo "Building..."
cmake --build . --config "$BUILD_TYPE" -j$(nproc 2>/dev/null || echo 1)

# Install if requested
if [[ -n "$INSTALL_PREFIX" ]]; then
    echo "Installing to: $INSTALL_PREFIX"
    cmake --install . --prefix "$INSTALL_PREFIX"
fi

echo ""
echo "Build complete!"
echo ""
echo "Python modules built:"
echo "  - py_filter: $(find . -name 'py_filter*.so' -o -name 'py_filter*.pyd' | head -1 | xargs dirname)"
echo "  - py_moving_average: $(find . -name 'py_moving_average*.so' -o -name 'py_moving_average*.pyd' | head -1 | xargs dirname)"
