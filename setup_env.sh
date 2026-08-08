#!/bin/bash
# ───────────────────────────────────────────────────────────
# Unitree 4D LiDAR L2 — ROS2 Workspace Setup
# ───────────────────────────────────────────────────────────
# Source this script to set up the environment:
#   source setup_env.sh
# ───────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source ROS2 if not already sourced
if [ -z "$ROS_DISTRO" ]; then
    if [ -f /opt/ros/jazzy/setup.bash ]; then
        source /opt/ros/jazzy/setup.bash
    else
        echo "ERROR: ROS2 Jazzy not found at /opt/ros/jazzy/"
        return 1
    fi
fi

# Source this workspace
if [ -f "$SCRIPT_DIR/install/setup.bash" ]; then
    source "$SCRIPT_DIR/install/setup.bash"
    echo "✓ Unitree LiDAR workspace ready (ROS2 $ROS_DISTRO)"
    echo ""
    echo "Quick commands:"
    echo "  ros2 launch unitree_lidar_test lidar_udp.launch.py            ← Start LiDAR + monitor"
    echo "  ros2 launch unitree_lidar_test lidar_udp.launch.py enable_rviz:=true  ← With RViz"
    echo "  ros2 launch unitree_lidar_test lidar_udp.launch.py lidar_ip:=192.168.1.100  ← Custom IP"
    echo "  ros2 run unitree_lidar_test lidar_monitor                     ← Monitor only"
    echo "  ros2 run unitree_lidar_test pointcloud_saver                  ← Save PCD files"
    echo ""
else
    echo "ERROR: Workspace not built. Run: colcon build --symlink-install"
    return 1
fi
