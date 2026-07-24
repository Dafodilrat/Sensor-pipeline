#!/usr/bin/env python3

from setuptools import setup
import os

package_name = 'signal_processing_nodes'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='user@example.com',
    description='ROS2 signal processing nodes using the standalone signal processing library',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'python_processing_node = signal_processing_nodes.python_processing_node:main',
        ],
    },
)
