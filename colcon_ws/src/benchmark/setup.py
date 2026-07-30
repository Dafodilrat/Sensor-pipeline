from setuptools import setup

package_name = 'benchmark'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/benchmark_params.yaml', 'config/synthetic_params.yaml']),
        ('share/' + package_name + '/launch', ['launch/base_sensor_launch.py', 'launch/benchmark_low_pass.launch.py', 'launch/benchmark_mean_filter.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description="ROS2 benchmark package for testing signal processing pipeline performance",
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lp_benchmark_node = benchmark.lp_benchmark_node:main',
            'mean_benchmark_node = benchmark.mean_benchmark_node:main',
        ],
    },
)
