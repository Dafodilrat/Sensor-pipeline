#!/usr/bin/env python3

from setuptools import setup
import os

package_name = 'signal_processing_py'

setup(
    name=package_name, # <-- CHANGE THIS from 'signal-processing-py' to package_name
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/' + package_name, ['package.xml']),
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ],
    install_requires=[
        'setuptools',
        'nawe_robotics_lib',
        'py_moving_average'
    ],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='user@example.com',
    description='ROS2 Python signal processing nodes using the standalone signal processing library',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'fixed_ma_node = signal_processing_py.fixed_ma_node:main',
            'time_ma_node = signal_processing_py.time_ma_node:main',
            'lp_node = signal_processing_py.lp_node:main',
        ],
    },
)
