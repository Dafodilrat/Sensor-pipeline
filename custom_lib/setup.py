#!/usr/bin/env python3
"""
Unified setup script for naweRobotics custom library Python bindings.

This script builds all Python extension modules:
- py_filter: Low-pass filters (FixedPoint and Float)
- py_moving_average: Fixed and Time Duration Moving Average filters
- py_median_filter: Median filter

Usage:
    # Install in development mode (recommended for development)
    pip install -e .
    
    # Or build and install normally
    pip install .
    
    # To build all modules manually
    python setup.py build_ext --inplace
"""

from setuptools import setup, Extension
import os
import sys
import platform
import subprocess
import shutil

# Check Python version
if sys.version_info < (3, 7):
    sys.exit("Python 3.7 or later is required")

# Check if pybind11 is installed
try:
    import pybind11
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pybind11>=2.6.0"])
    import pybind11

# Get the current directory
here = os.path.abspath(os.path.dirname(__file__))


def get_fpm_include_dir():
    """Get the fpm library include directory, cloning it if necessary."""
    fpm_dir = os.path.join(here, "third_party", "fpm")
    fpm_include_dir = os.path.join(fpm_dir, "include")
    
    # Check if fpm is already cloned and header exists
    if os.path.exists(os.path.join(fpm_include_dir, "fpm", "fixed.hpp")):
        print(f"Found existing fpm library at: {fpm_include_dir}")
        return fpm_include_dir
    
    # Clone fpm from GitHub
    print("Cloning fpm library from GitHub...")
    fpm_repo = "https://github.com/MikeLankamp/fpm.git"
    
    try:
        # Create third_party directory if it doesn't exist
        os.makedirs(os.path.join(here, "third_party"), exist_ok=True)
        
        # Clone the repository (shallow clone for speed)
        subprocess.check_call(
            ["git", "clone", "--depth", "1", fpm_repo, fpm_dir],
            cwd=os.path.join(here, "third_party")
        )
        
        # Verify the header exists
        if not os.path.exists(os.path.join(fpm_include_dir, "fpm", "fixed.hpp")):
            raise FileNotFoundError(
                f"fpm/fixed.hpp not found in {fpm_include_dir}"
            )
        
        print(f"fpm library cloned to: {fpm_include_dir}")
        return fpm_include_dir
        
    except Exception as e:
        print(f"Failed to clone fpm: {e}")
        # Fallback: check if it exists in the CMake build directory
        cmake_fpm = os.path.join(here, "build", "_deps", "fpm-src", "include")
        if os.path.exists(os.path.join(cmake_fpm, "fpm", "fixed.hpp")):
            print(f"Found fpm in CMake build directory: {cmake_fpm}")
            return cmake_fpm
        sys.exit(f"Could not find or clone fpm library: {e}")


# Get fpm include directory
fpm_include = get_fpm_include_dir()

# Common include directories
common_include_dirs = [
    here,
    os.path.join(here, 'filters', 'lib'),
    os.path.join(here, 'running_data', 'lib'),
    os.path.join(here, 'tools'),
    fpm_include,
    pybind11.get_include(),
]

# Common compile arguments
common_extra_compile_args = [
    '-std=c++17',
    '-O3',
    '-Wall',
    '-Wextra',
    '-fPIC',
]

# Platform-specific settings
if platform.system() == 'Windows':
    common_extra_compile_args.extend(['/EHsc', '/O2'])
elif platform.system() == 'Darwin':
    common_extra_compile_args.extend(['-stdlib=libc++', '-mmacosx-version-min=10.14'])

# Define all extension modules
filter_ext = Extension(
    'py_filter',
    sources=[
        'filters/src/py_filter_module.cpp',
    ],
    include_dirs=common_include_dirs + [
        os.path.join(here, 'filters', 'src'),
    ],
    language='c++',
    extra_compile_args=common_extra_compile_args,
)

ma_ext = Extension(
    'py_moving_average',
    sources=[
        'running_data/src/py_moving_average_module.cpp',
        'running_data/src/py_moving_average_bindings.cpp',
    ],
    include_dirs=common_include_dirs,
    language='c++',
    extra_compile_args=common_extra_compile_args,
)

median_ext = Extension(
    'py_median_filter',
    sources=[
        'running_data/src/py_median_filter_module.cpp',
        'running_data/src/median_filter_bindings.cpp',
    ],
    include_dirs=common_include_dirs,
    language='c++',
    extra_compile_args=common_extra_compile_args,
)

setup(
    name='nawe_robotics_lib',
    version='1.0.0',
    description='naweRobotics Custom Library - Python bindings for C++ signal processing',
    author='naweRobotics',
    ext_modules=[filter_ext, ma_ext, median_ext],
    python_requires='>=3.7',
    install_requires=['pybind11>=2.6.0', 'numpy'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
    ],
    zip_safe=False,
)
