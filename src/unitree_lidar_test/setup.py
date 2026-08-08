from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'unitree_lidar_test'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include launch files
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),
        # Include config files
        (os.path.join('share', package_name, 'config'),
         glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Caleb Camargo',
    maintainer_email='calebcamargo@example.com',
    description='Real-time testing and visualization for Unitree 4D LiDAR L2',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lidar_monitor = unitree_lidar_test.lidar_monitor:main',
            'pointcloud_saver = unitree_lidar_test.pointcloud_saver:main',
            'lidar_tester = unitree_lidar_test.lidar_tester:main',
        ],
    },
)
