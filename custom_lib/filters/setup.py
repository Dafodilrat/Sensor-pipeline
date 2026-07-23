#!/usr/bin/env python3
"""
Setup script for building the py_filter Python extension module.

This script uses pybind11 to create Python bindings for the C++ filter classes.
"""

from setuptools import setup, Extension
import os
import sys
import platform

# Check if pybind11 is installed
try:
    import pybind11
    print("pybind11 is available")
except ImportError:
    print("pybind11 not found. Installing via pip...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pybind11"])
    import pybind11

# Get the current directory
here = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(here)

# Include directories
include_dirs = [
    here,  # Current directory for our headers
    os.path.join(here, 'lib'),  # Include filters lib directory
    os.path.join(parent_dir, 'fpm', 'include'),  # Include fpm library
    os.path.join(parent_dir, 'tools'),  # Include tools directory
    pybind11.get_include(),  # pybind11 include directory
]

# Define the extension module
filter_ext = Extension(
    'py_filter',
    sources=[
        'src/py_filter_module.cpp',
    ],
    include_dirs=include_dirs,
    language='c++',
    extra_compile_args=[
        '-std=c++17',
        '-O3',  # Optimize
        '-Wall',  # Enable warnings
        '-Wextra',
        '-fPIC',
    ],
    extra_link_args=[],
)

# Platform-specific settings
if platform.system() == 'Windows':
    filter_ext.extra_compile_args.append('/EHsc')  # Exception handling model
    filter_ext.extra_compile_args.append('/O2')  # Optimize
elif platform.system() == 'Darwin':  # macOS
    filter_ext.extra_compile_args.append('-stdlib=libc++')
    filter_ext.extra_compile_args.append('-mmacosx-version-min=10.14')

# Setup configuration
setup(
    name='py_filter',
    version='1.0.0',
    description='Python bindings for Filter Library',
    author='naweRobotics',
    author_email='',
    url='',
    ext_modules=[filter_ext],
    python_requires='>=3.7',
    install_requires=[
        'pybind11>=2.6.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: C++',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
    ],
    zip_safe=False,
)

print(f"""
Filter module setup completed. To build and install:

1. Build in development mode:
   cd {here}
   pip install -e .

2. Or build and install:
   python setup.py build_ext --inplace
   pip install .

3. To test the module:
   python test_filter_bindings.py
""")
