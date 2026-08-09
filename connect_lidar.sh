#!/bin/bash
# Quick setup for Unitree 4D LiDAR L2 direct Ethernet connection
# Usage: source connect_lidar.sh [lidar_ip] [local_ip]

LIDAR_IP="${1:-192.168.1.62}"
LOCAL_IP="${2:-192.168.1.2}"
IFACE="enP8p1s0"

echo "🔌 Configurando conexión con LiDAR L2..."

# Assign IP (may need sudo)
if ! ip addr show $IFACE | grep -q "$LOCAL_IP"; then
    echo "   Asignando $LOCAL_IP/24 a $IFACE..."
    sudo ip addr add ${LOCAL_IP}/24 dev $IFACE
fi

# Verify connection
echo "   Verificando conexión con $LIDAR_IP..."
if ping -I $IFACE -c 2 -W 1 $LIDAR_IP > /dev/null 2>&1; then
    echo "✅ LiDAR reachable at $LIDAR_IP"
else
    echo "❌ LiDAR unreachable. ¿Está conectado y encendido?"
    return 1
fi

# Source workspace
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/install/setup.bash" ]; then
    source "$SCRIPT_DIR/install/setup.bash"
    echo "✅ Workspace ready"
fi

echo ""
echo "🚀 Comandos rápidos:"
echo "  ros2 launch unitree_lidar_test lidar_udp.launch.py"
echo "  ros2 launch unitree_lidar_test lidar_udp.launch.py enable_rviz:=true"
