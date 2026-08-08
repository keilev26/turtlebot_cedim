#!/usr/bin/env python3
"""
Real-time LiDAR data monitor for Unitree 4D LiDAR L2.

Subscribes to /unilidar/cloud and /unilidar/imu topics and displays:
- Point cloud statistics (points per scan, frequency, ranges)
- IMU data (orientation, angular velocity, linear acceleration)
- Connection status and health indicators
"""

import sys
import time
from collections import deque

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from sensor_msgs.msg import Imu, PointCloud2
from sensor_msgs_py import point_cloud2


class LidarMonitor(Node):
    """Monitor node that subscribes to LiDAR topics and prints statistics."""

    def __init__(self):
        super().__init__('lidar_monitor')

        # QoS: Best-effort for sensor data (UDP transport)
        sensor_qos = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
        )

        # Subscribers
        self.cloud_sub = self.create_subscription(
            PointCloud2, 'unilidar/cloud', self.cloud_callback, sensor_qos
        )
        self.imu_sub = self.create_subscription(
            Imu, 'unilidar/imu', self.imu_callback, sensor_qos
        )

        # Stats tracking
        self.cloud_count = 0
        self.cloud_times = deque(maxlen=100)
        self.imu_count = 0
        self.imu_times = deque(maxlen=100)
        self.last_cloud_points = 0
        self.last_print = time.time()
        self.print_interval = 2.0  # seconds

        self.get_logger().info('LiDAR Monitor started — waiting for data...')
        self.get_logger().info('  Subscribed to: unilidar/cloud (PointCloud2)')
        self.get_logger().info('  Subscribed to: unilidar/imu (Imu)')

    def cloud_callback(self, msg: PointCloud2):
        """Process incoming point cloud message."""
        now = time.time()
        self.cloud_times.append(now)
        self.cloud_count += 1

        # Count points
        point_step = msg.point_step
        row_step = msg.row_step
        if point_step > 0:
            num_points = msg.width * msg.height
        else:
            num_points = row_step // point_step if point_step > 0 else 0

        self.last_cloud_points = num_points

        # Forward to pointcloud_saver if it exists (loose coupling)
        self._maybe_print_stats()

    def imu_callback(self, msg: Imu):
        """Process incoming IMU message."""
        now = time.time()
        self.imu_times.append(now)
        self.imu_count += 1
        self._maybe_print_stats()

    def _maybe_print_stats(self):
        """Print statistics at regular intervals."""
        now = time.time()
        if now - self.last_print < self.print_interval:
            return
        self.last_print = now

        # Cloud frequency
        cloud_hz = 0.0
        if len(self.cloud_times) >= 2:
            cloud_hz = (len(self.cloud_times) - 1) / (
                self.cloud_times[-1] - self.cloud_times[0]
            )

        # IMU frequency
        imu_hz = 0.0
        if len(self.imu_times) >= 2:
            imu_hz = (len(self.imu_times) - 1) / (
                self.imu_times[-1] - self.imu_times[0]
            )

        # Status line
        status = (
            f'\n╔══════════════════════════════════════════════╗\n'
            f'║  Unitree 4D LiDAR L2 — Real-Time Monitor    ║\n'
            f'╠══════════════════════════════════════════════╣\n'
            f'║  PointCloud: {cloud_hz:6.1f} Hz  |  {self.last_cloud_points:6d} pts   ║\n'
            f'║  IMU:        {imu_hz:6.1f} Hz  |  msgs: {self.cloud_count:5d}       ║\n'
            f'║  Total cloud msgs: {self.cloud_count:5d}                 ║\n'
            f'║  Total IMU msgs:   {self.imu_count:5d}                 ║\n'
            f'╚══════════════════════════════════════════════╝'
        )
        print(status)


def main(args=None):
    rclpy.init(args=args)
    node = LidarMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\nShutting down LiDAR Monitor...')
    except rclpy._rclpy_pybind11.RCLError:
        pass  # Context already shut down by launch system
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
