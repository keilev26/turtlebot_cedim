#!/usr/bin/env python3
"""
Launch file for Unitree 4D LiDAR L2 — UDP (Ethernet) mode.

Launches:
  1. unitree_lidar_ros2_node — LiDAR driver (C++)
  2. lidar_monitor — Real-time statistics display (Python)
  3. pointcloud_saver — Save point clouds on demand (Python) [disabled by default]

Usage:
  ros2 launch unitree_lidar_test lidar_udp.launch.py
  ros2 launch unitree_lidar_test lidar_udp.launch.py enable_saver:=true
  ros2 launch unitree_lidar_test lidar_udp.launch.py lidar_ip:=192.168.2.100
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # ── Launch arguments ──────────────────────────────────────────
    lidar_ip_arg = DeclareLaunchArgument(
        'lidar_ip', default_value='192.168.1.62',
        description='IP address of the Unitree LiDAR L2'
    )
    local_ip_arg = DeclareLaunchArgument(
        'local_ip', default_value='192.168.1.2',
        description='IP address of this PC'
    )
    enable_rviz_arg = DeclareLaunchArgument(
        'enable_rviz', default_value='false',
        description='Launch RViz2 for visualization'
    )
    enable_saver_arg = DeclareLaunchArgument(
        'enable_saver', default_value='false',
        description='Launch pointcloud saver node'
    )

    # ── LiDAR Driver Node (C++) ───────────────────────────────────
    lidar_node = Node(
        package='unitree_lidar_ros2',
        executable='unitree_lidar_ros2_node',
        name='unitree_lidar_ros2_node',
        output='screen',
        parameters=[{
            'initialize_type': 2,              # Auto-init
            'work_mode': 0,                    # UDP mode
            'use_system_timestamp': True,
            'range_min': 0.05,
            'range_max': 30.0,
            'cloud_scan_num': 18,
            'lidar_port': 6101,                # int — LiDAR data port
            'lidar_ip': LaunchConfiguration('lidar_ip'),
            'local_port': 6201,                # int — local receive port
            'local_ip': LaunchConfiguration('local_ip'),
            'cloud_frame': 'unilidar_lidar',
            'cloud_topic': 'unilidar/cloud',
            'imu_frame': 'unilidar_imu',
            'imu_topic': 'unilidar/imu',
        }],
        # Respawn if it crashes
        respawn=True,
        respawn_delay=2.0,
    )

    # ── Monitor Node (Python) ─────────────────────────────────────
    monitor_node = Node(
        package='unitree_lidar_test',
        executable='lidar_monitor',
        name='lidar_monitor',
        output='screen',
    )

    # ── PointCloud Saver (Python, optional) ───────────────────────
    saver_node = Node(
        package='unitree_lidar_test',
        executable='pointcloud_saver',
        name='pointcloud_saver',
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_saver')),
    )

    # ── RViz2 (optional) ──────────────────────────────────────────
    rviz_config = PathJoinSubstitution([
        FindPackageShare('unitree_lidar_ros2'),
        'view.rviz',
    ])
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='log',
        condition=IfCondition(LaunchConfiguration('enable_rviz')),
    )

    # ── Status message ────────────────────────────────────────────
    status_msg = LogInfo(msg=[
        '\n'
        '╔══════════════════════════════════════════════════╗\n'
        '║   Unitree 4D LiDAR L2 — UDP Mode                 ║\n'
        '╠══════════════════════════════════════════════════╣\n'
        '║   LiDAR IP:  ', LaunchConfiguration('lidar_ip'), '                      ║\n'
        '║   Local IP:  ', LaunchConfiguration('local_ip'), '                       ║\n'
        '║   Topics:                                        ║\n'
        '║     - unilidar/cloud  (PointCloud2)              ║\n'
        '║     - unilidar/imu    (Imu)                      ║\n'
        '╚══════════════════════════════════════════════════╝\n'
    ])

    return LaunchDescription([
        # Arguments
        lidar_ip_arg,
        local_ip_arg,
        enable_rviz_arg,
        enable_saver_arg,
        # Status
        status_msg,
        # Nodes
        lidar_node,
        monitor_node,
        saver_node,
        rviz_node,
    ])
