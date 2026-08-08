#!/usr/bin/env python3
"""
Test launch for Unitree 4D LiDAR L2.

Launches:
  1. LiDAR driver (C++)
  2. lidar_tester — data quality analysis
  3. lidar_monitor — real-time stats
  4. rosbag recording (optional)

Usage:
  ros2 launch unitree_lidar_test test_lidar.launch.py
  ros2 launch unitree_lidar_test test_lidar.launch.py record:=true
  ros2 launch unitree_lidar_test test_lidar.launch.py test_duration:=30.0
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    # ── Arguments ──────────────────────────────────────────────
    record_arg = DeclareLaunchArgument(
        'record', default_value='false',
        description='Record rosbag during test'
    )
    test_duration_arg = DeclareLaunchArgument(
        'test_duration', default_value='15.0',
        description='Test duration in seconds'
    )
    bag_name_arg = DeclareLaunchArgument(
        'bag_name', default_value='lidar_test',
        description='Rosbag output name'
    )

    # ── LiDAR Driver ───────────────────────────────────────────
    lidar_node = Node(
        package='unitree_lidar_ros2',
        executable='unitree_lidar_ros2_node',
        name='unitree_lidar_ros2_node',
        output='screen',
        parameters=[{
            'initialize_type': 2,
            'work_mode': 0,
            'use_system_timestamp': True,
            'range_min': 0.05,
            'range_max': 30.0,
            'cloud_scan_num': 18,
            'lidar_port': 6101,
            'lidar_ip': '192.168.1.62',
            'local_port': 6201,
            'local_ip': '192.168.1.2',
            'cloud_frame': 'unilidar_lidar',
            'cloud_topic': 'unilidar/cloud',
            'imu_frame': 'unilidar_imu',
            'imu_topic': 'unilidar/imu',
        }],
    )

    # ── Monitor ────────────────────────────────────────────────
    monitor_node = Node(
        package='unitree_lidar_test',
        executable='lidar_monitor',
        name='lidar_monitor',
        output='screen',
    )

    # ── Tester ─────────────────────────────────────────────────
    tester_node = Node(
        package='unitree_lidar_test',
        executable='lidar_tester',
        name='lidar_tester',
        output='screen',
        parameters=[{'test_duration': LaunchConfiguration('test_duration')}],
    )

    # ── Rosbag recording (optional) ────────────────────────────
    bag_base = '/home/calebcamargo/unitree_lidar_data/bags'
    bag_record = ExecuteProcess(
        condition=IfCondition(LaunchConfiguration('record')),
        cmd=[
            'ros2', 'bag', 'record',
            '-o', PathJoinSubstitution([bag_base, LaunchConfiguration('bag_name')]),
            '/unilidar/cloud',
            '/unilidar/imu',
            '/tf',
            '/tf_static',
        ],
        output='screen',
    )

    return LaunchDescription([
        record_arg,
        test_duration_arg,
        bag_name_arg,
        LogInfo(msg=['🧪 Starting LiDAR tests...']),
        lidar_node,
        monitor_node,
        tester_node,
        bag_record,
    ])
