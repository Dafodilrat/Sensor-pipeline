from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'sensor_streamer'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/synthetic_params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dafodilrat',
    maintainer_email='your@email.com',
    description='Package for generating and processing synthetic sensor data',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'synthetic_sensor = sensor_streamer.generator:main',
            'replay = sensor_streamer.replay:main',
            'sensor_play = sensor_streamer.sensor_play:main',
        ],
    },
)