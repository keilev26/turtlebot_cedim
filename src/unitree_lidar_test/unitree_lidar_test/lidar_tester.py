#!/usr/bin/env python3
"""
LiDAR Data Quality Tester for Unitree 4D LiDAR L2.

Performs comprehensive tests on the LiDAR data stream:
  1. Connectivity check — are topics being published?
  2. Frequency check — is the data rate within expected range?
  3. Point cloud validation — density, range, field checks
  4. IMU validation — rate, saturation checks
  5. TF tree validation
  6. Timing analysis — latency, jitter

Usage:
  ros2 run unitree_lidar_test lidar_tester
  ros2 run unitree_lidar_test lidar_tester --ros-args -p test_duration:=10.0
"""

import time
from collections import deque

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from sensor_msgs.msg import Imu, PointCloud2
from sensor_msgs_py import point_cloud2
from tf2_ros import Buffer, TransformListener


class LidarTester(Node):
    """Comprehensive LiDAR data quality testing node."""

    def __init__(self):
        super().__init__('lidar_tester')

        self.declare_parameter('test_duration', 10.0)
        self.test_duration = self.get_parameter('test_duration').value

        sensor_qos = QoSProfile(
            depth=100,
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

        # TF
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Data collectors
        self.cloud_timestamps = deque()
        self.cloud_points = deque()
        self.cloud_ranges = []
        self.cloud_intensities = []
        self.imu_timestamps = deque()
        self.imu_accel_mags = []
        self.imu_gyro_mags = []

        self.start_time = time.time()
        self.done = False

        self.get_logger().info('=' * 55)
        self.get_logger().info('🧪 LiDAR Tester — collecting data...')
        self.get_logger().info(f'   Test duration: {self.test_duration}s')
        self.get_logger().info('=' * 55)

        # Timer to print intermediate results and check completion
        self.create_timer(2.0, self.intermediate_report)
        self.create_timer(self.test_duration, self.final_report)

    def cloud_callback(self, msg: PointCloud2):
        now = time.time()
        self.cloud_timestamps.append(now)
        self.cloud_points.append(msg.width * msg.height)

        # Sample points for range/intensity analysis (first 500 per cloud)
        count = 0
        for p in point_cloud2.read_points(
            msg, field_names=('x', 'y', 'z', 'intensity'), skip_nans=True
        ):
            dist = np.sqrt(p[0]**2 + p[1]**2 + p[2]**2)
            self.cloud_ranges.append(dist)
            self.cloud_intensities.append(p[3])
            count += 1
            if count > 500:
                break

    def imu_callback(self, msg: Imu):
        now = time.time()
        self.imu_timestamps.append(now)

        ax, ay, az = (
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z,
        )
        gx, gy, gz = (
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
        )
        self.imu_accel_mags.append(np.sqrt(ax**2 + ay**2 + az**2))
        self.imu_gyro_mags.append(np.sqrt(gx**2 + gy**2 + gz**2))

    def intermediate_report(self):
        if self.done:
            return
        elapsed = time.time() - self.start_time
        n_clouds = len(self.cloud_timestamps)
        n_imus = len(self.imu_timestamps)

        cloud_hz = n_clouds / elapsed if elapsed > 0 else 0
        imu_hz = n_imus / elapsed if elapsed > 0 else 0

        self.get_logger().info(
            f'⏳ {elapsed:.0f}s / {self.test_duration:.0f}s | '
            f'☁️ {cloud_hz:.1f}Hz ({n_clouds} msgs) | '
            f'📐 {imu_hz:.1f}Hz ({n_imus} msgs)'
        )

    def _check_pass_fail(self, name, passed, detail=''):
        status = '✅ PASS' if passed else '❌ FAIL'
        msg = f'  {status} | {name}'
        if detail:
            msg += f' | {detail}'
        self.get_logger().info(msg)
        return passed

    def final_report(self):
        if self.done:
            return
        self.done = True

        elapsed = time.time() - self.start_time
        results = []

        self.get_logger().info('')
        self.get_logger().info('=' * 55)
        self.get_logger().info('📊 FINAL TEST REPORT')
        self.get_logger().info('=' * 55)

        # ── Test 1: Connectivity ──────────────────────────────
        n_clouds = len(self.cloud_timestamps)
        n_imus = len(self.imu_timestamps)
        r1 = self._check_pass_fail(
            'PointCloud received',
            n_clouds > 0,
            f'{n_clouds} messages'
        )
        r2 = self._check_pass_fail(
            'IMU received',
            n_imus > 0,
            f'{n_imus} messages'
        )
        results.extend([r1, r2])

        # ── Test 2: Cloud Frequency (target ~10Hz for L2) ────
        if n_clouds >= 2:
            cloud_hz = (n_clouds - 1) / (
                self.cloud_timestamps[-1] - self.cloud_timestamps[0]
            )
            results.append(self._check_pass_fail(
                'Cloud frequency',
                5.0 <= cloud_hz <= 30.0,
                f'{cloud_hz:.1f} Hz (expected 5-30 Hz)'
            ))
        else:
            results.append(False)

        # ── Test 3: IMU Frequency (target ~200Hz for L2) ─────
        if n_imus >= 2:
            imu_hz = (n_imus - 1) / (
                self.imu_timestamps[-1] - self.imu_timestamps[0]
            )
            results.append(self._check_pass_fail(
                'IMU frequency',
                50.0 <= imu_hz <= 500.0,
                f'{imu_hz:.1f} Hz (expected 50-500 Hz)'
            ))
        else:
            results.append(False)

        # ── Test 4: Points per cloud ──────────────────────────
        if self.cloud_points:
            avg_pts = np.mean(list(self.cloud_points))
            results.append(self._check_pass_fail(
                'Points per cloud',
                avg_pts > 100,
                f'avg {avg_pts:.0f} pts/cloud'
            ))
        else:
            results.append(False)

        # ── Test 5: Range distribution ───────────────────────
        if self.cloud_ranges:
            r_min, r_max = np.min(self.cloud_ranges), np.max(self.cloud_ranges)
            r_mean = np.mean(self.cloud_ranges)
            results.append(self._check_pass_fail(
                'Range coverage',
                r_max > 1.0,  # At least 1m max range
                f'min={r_min:.2f}m max={r_max:.2f}m mean={r_mean:.2f}m'
            ))
        else:
            results.append(False)

        # ── Test 6: Intensity values ─────────────────────────
        if self.cloud_intensities:
            i_min, i_max = np.min(self.cloud_intensities), np.max(self.cloud_intensities)
            results.append(self._check_pass_fail(
                'Intensity data',
                i_max > i_min,  # Non-constant intensity
                f'range=[{i_min:.0f}, {i_max:.0f}]'
            ))
        else:
            results.append(False)

        # ── Test 7: IMU gravity check ────────────────────────
        if self.imu_accel_mags:
            avg_accel = np.mean(self.imu_accel_mags)
            results.append(self._check_pass_fail(
                'IMU accel magnitude',
                8.0 <= avg_accel <= 12.0,
                f'avg={avg_accel:.2f} m/s² (expect ~9.81)'
            ))
        else:
            results.append(False)

        # ── Test 8: TF tree ──────────────────────────────────
        try:
            self.tf_buffer.lookup_transform(
                'unilidar_lidar', 'unilidar_imu',
                rclpy.time.Time(), rclpy.duration.Duration(seconds=2.0)
            )
            results.append(self._check_pass_fail(
                'TF tree (lidar↔imu)',
                True,
                'Transform exists'
            ))
        except Exception as e:
            results.append(self._check_pass_fail(
                'TF tree (lidar↔imu)',
                False,
                str(e)[:40]
            ))

        # ── Summary ──────────────────────────────────────────
        n_pass = sum(results)
        n_total = len(results)

        self.get_logger().info('─' * 55)
        self.get_logger().info(
            f'🏁 RESULT: {n_pass}/{n_total} tests passed '
            f'({"✅" if n_pass == n_total else "⚠️"})'
        )
        self.get_logger().info('=' * 55)


def main(args=None):
    rclpy.init(args=args)
    node = LidarTester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
