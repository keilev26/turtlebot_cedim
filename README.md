# Unitree 4D LiDAR L2 — ROS2 Real-Time Testing

Proyecto ROS2 Humble para pruebas en tiempo real del **Unitree 4D LiDAR L2**.

## Estructura

```
turtlebot_proyecto/                    # ROS2 workspace + SDK integrado
├── connect_lidar.sh                   # Configurar IP + cargar workspace
├── setup_env.sh                       # Solo cargar entorno
├── check_udp.py                       # Diagnóstico de conexión UDP
├── README.md
├── MIGRATION_HUMBLE.md
├── unilidar_sdk2-2.0.10/             # [SDK] Unitree SDK oficial
│   ├── unitree_lidar_ros2/            # Driver C++ (fuente original)
│   ├── unitree_lidar_ros/             # Driver ROS1
│   └── unitree_lidar_sdk/             # Librería core + static lib
├── src/
│   ├── unitree_lidar_ros2 →           # Symlink → ../unilidar_sdk2-2.0.10/.../unitree_lidar_ros2
│   └── unitree_lidar_test/            # [Python] Testing y monitoreo
│       ├── unitree_lidar_test/
│       │   ├── lidar_monitor.py       # Stats en tiempo real
│       │   ├── lidar_tester.py        # Test automático de calidad
│       │   └── pointcloud_saver.py    # Guardar nubes a PCD
│       ├── launch/
│       │   ├── lidar_udp.launch.py    # Launch normal
│       │   └── test_lidar.launch.py   # Launch de testing
│       └── config/
│           └── params_udp.yaml
```

## Requisitos

- **ROS2 Humble** (Ubuntu 22.04)
- **PCL** (`libpcl-dev`)
- Paquetes ROS2: `ros-humble-pcl-conversions`, `ros-humble-tf2`, `ros-humble-sensor-msgs`, `ros-humble-rosbag2`

## Quick Start

```bash
# Si es la primera vez
colcon build --symlink-install
./setup_env.sh # Previamente dar permisos con chmod 777 
```

```bash
# 1. Conectar y configurar
source connect_lidar.sh

# 2. Lanzar (con RViz)
ros2 launch unitree_lidar_test lidar_udp.launch.py enable_rviz:=true
```

---

# 🧪 Testing

## 1. Test automático de calidad de datos

Evalúa conectividad, frecuencias, densidad de nube, rangos, IMU, y TF tree:

```bash
ros2 launch unitree_lidar_test test_lidar.launch.py

# Ajustar duración del test
ros2 launch unitree_lidar_test test_lidar.launch.py test_duration:=30.0

# Con grabación de rosbag
ros2 launch unitree_lidar_test test_lidar.launch.py record:=true bag_name:=mi_test
```

**Salida esperada:**
```
🧪 LiDAR Tester — collecting data...
⏳ 8s / 15s | ☁️ 10.0Hz (80 msgs) | 📐 200.0Hz (1600 msgs)
📊 FINAL TEST REPORT
  ✅ PASS | PointCloud received  | 150 messages
  ✅ PASS | IMU received         | 3000 messages
  ✅ PASS | Cloud frequency      | 10.0 Hz (expected 5-30 Hz)
  ✅ PASS | IMU frequency        | 200.1 Hz (expected 50-500 Hz)
  ✅ PASS | Points per cloud     | avg 24000 pts/cloud
  ✅ PASS | Range coverage       | min=0.05m max=28.5m mean=8.2m
  ✅ PASS | Intensity data       | range=[0, 255]
  ✅ PASS | IMU accel magnitude  | avg=9.80 m/s² (expect ~9.81)
  ✅ PASS | TF tree (lidar↔imu)  | Transform exists
🏁 RESULT: 8/8 tests passed ✅
```

## 2. Inspección manual de topics

```bash
# Frecuencias
ros2 topic hz /unilidar/cloud
ros2 topic hz /unilidar/imu

# Ver mensajes (sin arrays)
ros2 topic echo /unilidar/imu
ros2 topic echo /unilidar/cloud --no-arr --once

# Inspeccionar campos del pointcloud
ros2 topic echo /unilidar/cloud --once | head -30

# Ver TF tree
ros2 run tf2_tools view_frames
```

## 3. Grabar rosbag

```bash
# Desde launch
ros2 launch unitree_lidar_test test_lidar.launch.py record:=true bag_name:=office_scan

# Manual
ros2 bag record -o ~/unitree_lidar_data/bags/test1 \
  /unilidar/cloud \
  /unilidar/imu \
  /tf /tf_static

# Reproducir
ros2 bag play ~/unitree_lidar_data/bags/test1
```

## 4. Guardar nubes individuales (PCD)

```bash
ros2 run unitree_lidar_test pointcloud_saver
# Presiona Enter para guardar la nube actual
# Las PCD se guardan en ~/unitree_lidar_data/pointclouds/
```

## 5. Probar diferentes configuraciones

```bash
# Ajustar rango máximo
ros2 run unitree_lidar_ros2 unitree_lidar_ros2_node \
  --ros-args -p range_max:=15.0 -p cloud_scan_num:=9

# Probar con RViz sin el launch
ros2 launch unitree_lidar_test lidar_udp.launch.py enable_rviz:=true
```

---

# 🗺️ SLAM

Hay 2 opciones principales compatibles con el Unitree L2 en ROS2:

## Opción A: Point-LIO (recomendado para L2)

**Repo:** [dfloreaa/point_lio_ros2](https://github.com/dfloreaa/point_lio_ros2)

✅ Tiene configuración explícita para Unitree L2 (`unilidar_l2.yaml`)  
✅ Usa los mismos topics `/unilidar/cloud` + `/unilidar/imu`  
✅ Odometría LiDAR-Inercial en tiempo real  
✅ Probado en Humble — compatible con este proyecto

```bash
# Instalación
cd ~/turtlebot_proyecto/..
git clone https://github.com/dfloreaa/point_lio_ros2.git
cd point_lio_ros2

# Instalar dependencias
sudo apt install ros-humble-pcl-ros ros-humble-pcl-conversions libeigen3-dev
# NOTA: Necesita livox_ros_driver2 (incluso sin Livox)
git clone https://github.com/Ericsii/livox_ros_driver2.git
# Build livox_ros_driver2 primero, luego point_lio_ros2

# El config para L2 ya viene incluido:
# config/unilidar_l2.yaml  (lidar_type: 5, scan_line: 18)
```

## Opción B: FAST-LIO2

**Repo:** [Ericsii/FAST_LIO_ROS2](https://github.com/Ericsii/FAST_LIO_ROS2)

✅ Más battle-tested, comunidad grande  
✅ Filtro Kalman iterado + ikd-Tree  
⚠️ Necesita crear config para Unitree L2 manualmente  
⚠️ También requiere `livox_ros_driver2`

---

# Troubleshooting

| Problema | Solución |
|---|---|
| `bind udp port failed` | Puerto ocupado: `pkill -9 unitree_lidar` |
| `Unilidar is not initialized` | Verificar IP: `ping -I enp3s0 192.168.1.62` |
| IP se pierde al reiniciar | Usar `source connect_lidar.sh` cada vez |
| No se ven puntos en RViz | Fixed Frame = `unilidar_lidar`, topic = `/unilidar/cloud` |
| LiDAR no envía UDP | Puede estar en modo Serial; usar `set_to_udp_mode` del SDK |

---

## Topics

| Topic | Tipo | Frame |
|---|---|---|
| `/unilidar/cloud` | `sensor_msgs/PointCloud2` | `unilidar_lidar` |
| `/unilidar/imu`   | `sensor_msgs/Imu` | `unilidar_imu` |

## Especificaciones L2

- **FOV**: 360° × 90° (96° en modo negativo)
- **Rango**: 0.05 – 30 m
- **IMU**: 6-axis integrada
- **Point rate**: ~200,000 pts/s
- **Interfaces**: Ethernet UDP / TTL UART
