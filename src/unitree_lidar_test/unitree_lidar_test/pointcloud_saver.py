#!/usr/bin/env python3
"""
PointCloud saver for Unitree 4D LiDAR L2.

Saves point clouds to PCD files on demand.
Press 's' and Enter to save the most recent point cloud.
"""

import os
import time
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2


class PointCloudSaver(Node):
    """Save point clouds to PCD files."""

    def __init__(self):
        super().__init__('pointcloud_saver')

        sensor_qos = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
        )

        self.cloud_sub = self.create_subscription(
            PointCloud2, 'unilidar/cloud', self.cloud_callback, sensor_qos
        )

        # Create output directory
        self.output_dir = os.path.expanduser(
            '~/unitree_lidar_data/pointclouds'
        )
        os.makedirs(self.output_dir, exist_ok=True)

        self.latest_cloud = None
        self.save_count = 0

        self.get_logger().info(
            f'PointCloud Saver ready — saving to {self.output_dir}'
        )
        self.get_logger().info(
            'Press Enter in this terminal to save the latest point cloud...'
        )

        # Timer to check for user input (non-blocking)
        self.create_timer(0.5, self.check_input)

    def cloud_callback(self, msg: PointCloud2):
        """Store latest point cloud."""
        self.latest_cloud = msg

    def check_input(self):
        """Non-blocking input check (handled via timer)."""
        pass  # Input handled by the spin thread below

    def save_cloud(self):
        """Save the latest point cloud to a PCD file."""
        if self.latest_cloud is None:
            self.get_logger().warn('No point cloud received yet!')
            return

        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'cloud_{timestamp}_{self.save_count:04d}.pcd'
        filepath = os.path.join(self.output_dir, filename)

        # Extract points
        points_list = []
        for point in point_cloud2.read_points(
            self.latest_cloud, field_names=('x', 'y', 'z', 'intensity'),
            skip_nans=True
        ):
            points_list.append(point)

        if not points_list:
            self.get_logger().warn('Point cloud is empty!')
            return

        # Write PCD file
        points_arr = np.array(points_list)
        num_points = len(points_list)

        with open(filepath, 'w') as f:
            f.write('# .PCD v0.7 - Point Cloud Data file format\n')
            f.write('VERSION 0.7\n')
            f.write('FIELDS x y z intensity\n')
            f.write('SIZE 4 4 4 4\n')
            f.write('TYPE F F F F\n')
            f.write('COUNT 1 1 1 1\n')
            f.write(f'WIDTH {num_points}\n')
            f.write('HEIGHT 1\n')
            f.write('VIEWPOINT 0 0 0 1 0 0 0\n')
            f.write(f'POINTS {num_points}\n')
            f.write('DATA ascii\n')
            for p in points_arr:
                f.write(f'{p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {p[3]:.6f}\n')

        self.save_count += 1
        self.get_logger().info(
            f'Saved {num_points} points → {filepath}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudSaver()
    try:
        # Spin in a separate thread so we can handle input
        from threading import Thread
        spin_thread = Thread(target=rclpy.spin, args=(node,), daemon=True)
        spin_thread.start()

        print('\n' + '=' * 50)
        print('PointCloud Saver — Interactive Mode')
        print('=' * 50)
        print('Commands:')
        print('  s / save  — Save latest point cloud')
        print('  q / quit  — Exit')
        print('=' * 50 + '\n')

        while rclpy.ok():
            cmd = input().strip().lower()
            if cmd in ('q', 'quit', 'exit'):
                break
            elif cmd in ('s', 'save', ''):
                node.save_cloud()
            else:
                print(f'Unknown command: {cmd}')
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
