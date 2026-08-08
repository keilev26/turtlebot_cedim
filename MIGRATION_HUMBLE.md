# Plan de Migración: ROS2 Jazzy → ROS2 Humble

> **Objetivo:** Migrar todo el proyecto Unitree 4D LiDAR L2 de ROS2 Jazzy (Ubuntu 24.04) a ROS2 Humble (Ubuntu 22.04).
> **Motivación:** La mayoría de paquetes SLAM (Point-LIO, FAST-LIO2), drivers y la comunidad están probados y estables en Humble. Jazzy es más nuevo y tiene menos soporte del ecosistema de robótica.

---

## 0. ¿Por qué migrar?

| Aspecto | Jazzy (actual) | Humble (objetivo) |
|---|---|---|
| **Ubuntu** | 24.04 Noble | 22.04 Jammy |
| **EOL** | Mayo 2029 | Mayo 2027 |
| **Python** | 3.12 | 3.10 |
| **Point-LIO** | No probado, requiere adaptación | ✅ Oficialmente soportado |
| **FAST-LIO2** | Requiere patches | ✅ Oficialmente soportado |
| **Unitree SDK** | Funciona (compila OK) | ✅ Entorno original del SDK |
| **Comunidad** | Menor | Mayor (paquetes, tutorials, debugging) |
| **PCL** | 1.14 | 1.12 |

---

## 1. Estrategia de migración

Hay 2 caminos posibles:

### Opción A: Docker (recomendado para empezar)
- Mantienes Ubuntu 24.04 como host
- Creas un container Humble con acceso a red (host network para el LiDAR UDP)
- El workspace y SDK se montan como volúmenes
- Ventaja: No tocas tu sistema, pruebas rápido, fácil rollback
- Desventaja: Overhead mínimo de Docker, configuración de red

### Opción B: Instalación nativa
- Instalar Ubuntu 22.04 (dual boot o reinstalar)
- Instalar ROS2 Humble nativo
- Ventaja: Rendimiento nativo, sin capa Docker
- Desventaja: Requiere reinstalar SO o hacer dual boot

**→ Este plan cubre ambas opciones, con énfasis en la Opción A (Docker).**

---

## 2. Inventario de componentes a migrar

### 2.1 Paquete `unitree_lidar_ros2` [C++]

| Item | Estado en Jazzy | Cambios para Humble |
|---|---|---|
| `CMakeLists.txt` | Compila en Jazzy | Sin cambios. El SDK fue diseñado para Foxy/Humble. |
| `package.xml` | `ament_cmake`, `rclcpp`, `pcl_conversions`, `tf2_ros` | Cambiar dependencias de `ros-jazzy-*` a `ros-humble-*` (automático con apt). El XML no cambia. |
| `unitree_lidar_ros2.h` | API `rclcpp::Node` | Sin cambios. La API base de rclcpp no cambió entre Humble y Jazzy. |
| `unitree_lidar_ros2_node.cpp` | `main()` estándar | Sin cambios. |
| Librería SDK `libunilidar_sdk2.a` | x86_64 | Funciona igual — es un static lib precompilado sin dependencias de ROS. |

**Veredicto:** ✅ Migración directa, sin cambios de código.

### 2.2 Paquete `unitree_lidar_test` [Python]

| Item | Estado en Jazzy | Cambios para Humble |
|---|---|---|
| `package.xml` | `ament_python`, `rclpy`, `sensor_msgs` | Sin cambios estructurales. |
| `setup.py` | `console_scripts` entry_points | Sin cambios. |
| `setup.cfg` | Config estándar | Sin cambios. |
| `lidar_monitor.py` | `rclpy.spin()`, `QoSProfile` | Sin cambios. |
| `lidar_tester.py` | `create_subscription`, `tf2_ros.Buffer` | Sin cambios. |
| `pointcloud_saver.py` | `sensor_msgs_py.point_cloud2` | Verificar que `sensor_msgs_py` existe en Humble. Alternativa: `ros2_numpy` o convertir manualmente. |
| `lidar_udp.launch.py` | `launch_ros.actions.Node` | ✅ Compatible (launch system es igual en Humble/Jazzy). |
| `test_lidar.launch.py` | `ExecuteProcess`, `PathJoinSubstitution` | ✅ Compatible. |

**Veredicto:** ✅ Migración directa casi total. Verificar `sensor_msgs_py`.

### 2.3 Scripts auxiliares

| Script | Cambios |
|---|---|
| `connect_lidar.sh` | Sin cambios (usa comandos Linux estándar). |
| `setup_env.sh` | Cambiar `/opt/ros/jazzy` → `/opt/ros/humble`. |
| `check_udp.py` | Sin cambios (Python stdlib). |

---

## 3. Plan paso a paso — Opción A (Docker)

### Paso 1: Instalar Docker (si no está)

```bash
# Verificar si ya está
docker --version

# Si no:
sudo apt update && sudo apt install docker.io -y
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

### Paso 2: Crear el Dockerfile de Humble

Crear `~/turtlebot_proyecto/Dockerfile.humble`:

```dockerfile
FROM osrf/ros:humble-desktop-full

# Dependencias del SDK
RUN apt-get update && apt-get install -y \
    ros-humble-pcl-conversions \
    ros-humble-pcl-ros \
    ros-humble-tf2 \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs \
    ros-humble-sensor-msgs \
    ros-humble-sensor-msgs-py \
    ros-humble-rosbag2 \
    ros-humble-rviz2 \
    libpcl-dev \
    libeigen3-dev \
    python3-pip \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root con mismo UID que el host
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID rosuser && \
    useradd -m -u $UID -g $GID -s /bin/bash rosuser

USER rosuser
WORKDIR /home/rosuser

# Entrypoint: source ROS + bash
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
CMD ["/bin/bash"]
```

### Paso 3: Construir la imagen

```bash
cd ~/turtlebot_proyecto
docker build -t lidar-humble \
  --build-arg UID=$(id -u) --build-arg GID=$(id -g) \
  -f Dockerfile.humble .
```

### Paso 4: Script para lanzar el container

Crear `~/turtlebot_proyecto/docker_run.sh`:

```bash
#!/bin/bash
# Ejecutar el workspace de LiDAR en ROS2 Humble (Docker)
# La red se comparte con el host para que el LiDAR UDP funcione

docker run -it --rm \
    --name lidar_humble \
    --network host \
    --ipc host \
    --pid host \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
    -v $HOME/.Xauthority:/home/rosuser/.Xauthority:ro \
    -v /home/cedim/turtlebot_proyecto:/home/rosuser/turtlebot_proyecto:rw \
    lidar-humble \
    /bin/bash -c "
        # Permitir acceso X11
        xhost +local: 2>/dev/null || true
        # Construir el workspace
        cd /home/rosuser/turtlebot_proyecto
        rm -rf build/ install/ log/
        colcon build --symlink-install
        source install/setup.bash
        echo '✅ Workspace Humble listo'
        exec /bin/bash
    "
```

### Paso 5: Build y verificación en el container

```bash
# Lanzar el container
./docker_run.sh

# Dentro del container:
# Verificar compilación
colcon build --symlink-install

# Verificar paquetes
ros2 pkg list | grep unitree
# Debe mostrar: unitree_lidar_ros2, unitree_lidar_test

# Verificar ejecutables
ros2 pkg executables unitree_lidar_test
# Debe mostrar: lidar_monitor, lidar_tester, pointcloud_saver

# Probar conexión con LiDAR (desde el container, con --network host)
ping -c 2 192.168.1.62

# Lanzar driver + monitor
ros2 launch unitree_lidar_test lidar_udp.launch.py
```

---

## 4. Plan paso a paso — Opción B (Nativo)

### Paso 0: Instalar Ubuntu 22.04 Jammy
- Dual boot junto a Ubuntu 24.04, o
- Instalación limpia en otra partición/SSD

### Paso 1: Instalar ROS2 Humble

```bash
# Setup sources
sudo apt update && sudo apt install curl gnupg lsb-release -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Instalar
sudo apt update
sudo apt install ros-humble-desktop -y
```

### Paso 2: Dependencias del proyecto

```bash
sudo apt install -y \
  ros-humble-pcl-conversions \
  ros-humble-pcl-ros \
  ros-humble-tf2 \
  ros-humble-tf2-ros \
  ros-humble-tf2-geometry-msgs \
  ros-humble-sensor-msgs \
  ros-humble-sensor-msgs-py \
  ros-humble-rosbag2 \
  ros-humble-rviz2 \
  libpcl-dev \
  libeigen3-dev \
  python3-pip \
  python3-numpy \
  python3-colcon-common-extensions
```

### Paso 3: Verificar que el SDK está presente

```bash
ls ~/turtlebot_proyecto/unilidar_sdk2-2.0.10/unitree_lidar_sdk/lib/x86_64/libunilidar_sdk2.a
```

### Paso 4: Actualizar `setup_env.sh` para Humble

```bash
# Cambiar en setup_env.sh:
# /opt/ros/jazzy/setup.bash → /opt/ros/humble/setup.bash
```

### Paso 5: Build limpio

```bash
cd ~/turtlebot_proyecto
rm -rf build/ install/ log/
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

### Paso 6: Verificación

```bash
source install/setup.bash
ros2 pkg list | grep unitree
ros2 run unitree_lidar_test lidar_tester
```

---

## 5. Cambios específicos por componente

### 5.1 `sensor_msgs_py` (pointcloud_saver.py)

En **Humble** el paquete Python para pointcloud se llama `sensor_msgs_py` igual que en Jazzy, así que no debería haber cambios. Si falla:

```python
# Alternativa en Humble si sensor_msgs_py no está:
from sensor_msgs.msg import PointCloud2
import struct

def read_points_manual(msg: PointCloud2):
    """Leer puntos sin sensor_msgs_py."""
    fmt = '<' + 'f' * (msg.point_step // 4)  # little-endian floats
    for i in range(0, len(msg.data), msg.point_step):
        yield struct.unpack(fmt, msg.data[i:i+msg.point_step])
```

### 5.2 `setup_env.sh`

```bash
# Línea a cambiar:
if [ -f /opt/ros/humble/setup.bash ]; then   # antes: jazzy
    source /opt/ros/humble/setup.bash
```

### 5.3 `connect_lidar.sh`

Sin cambios. Usa comandos Linux estándar (`ip`, `ping`) que no dependen de ROS.

### 5.4 Dockerfile

Si usas Docker, crear el archivo como se describe en la sección 3.

---

## 6. Checklist de verificación post-migración

- [ ] `colcon build` termina sin errores
- [ ] `ros2 pkg list | grep unitree` muestra ambos paquetes
- [ ] `ros2 run unitree_lidar_ros2 unitree_lidar_ros2_node` inicia sin crash
- [ ] `ros2 run unitree_lidar_test lidar_monitor` muestra stats
- [ ] `ros2 run unitree_lidar_test lidar_tester` ejecuta los 8 tests
- [ ] `ros2 run unitree_lidar_test pointcloud_saver` guarda PCD
- [ ] `ros2 launch unitree_lidar_test lidar_udp.launch.py` funciona
- [ ] `ros2 launch unitree_lidar_test test_lidar.launch.py` funciona
- [ ] RViz2 muestra nube de puntos (`enable_rviz:=true`)
- [ ] Rosbag recording funciona (`record:=true`)
- [ ] `ping -I enp3s0 192.168.1.62` OK (red funciona)
- [ ] IMU publica a ~200 Hz, Cloud a frecuencia esperada

---

## 7. Después de migrar: SLAM

Una vez en Humble, la instalación de SLAM es directa:

### Point-LIO (recomendado para L2)

```bash
cd ~/turtlebot_proyecto/..
git clone https://github.com/dfloreaa/point_lio_ros2.git

# Instalar livox_ros_driver2 (dependencia)
git clone https://github.com/Ericsii/livox_ros_driver2.git
cd livox_ros_driver2
source /opt/ros/humble/setup.bash
colcon build --symlink-install

# Build Point-LIO
cd ../point_lio_ros2
source ../livox_ros_driver2/install/setup.bash
colcon build --symlink-install

# Ejecutar con config de L2
ros2 launch point_lio_ros2 mapping_unilidar_l2.launch.py
```

### FAST-LIO2

```bash
cd ~/turtlebot_proyecto/..
git clone https://github.com/Ericsii/FAST_LIO_ROS2.git --recursive
cd FAST_LIO_ROS2
source /opt/ros/humble/setup.bash
source ../livox_ros_driver2/install/setup.bash
colcon build --symlink-install
```

---

## 8. Rollback a Jazzy

Si algo falla, volver es trivial porque el código es el mismo:

```bash
# En Docker: simplemente no usar el container de Humble
# En nativo (dual boot): reiniciar en Ubuntu 24.04
cd ~/turtlebot_proyecto
source setup_env.sh  # que apunta a /opt/ros/jazzy
colcon build --symlink-install
```

---

## 9. Línea de tiempo estimada

| Fase | Tiempo |
|---|---|
| Docker: instalar y construir imagen | 20 min |
| Docker: build workspace + verificación | 10 min |
| Docker: probar con LiDAR real | 10 min |
| Nativo: instalar Ubuntu 22.04 (dual boot) | 1–2 horas |
| Nativo: instalar ROS2 Humble + dependencias | 20 min |
| Nativo: build + verificación | 10 min |
| SLAM: instalar Point-LIO / FAST-LIO2 | 30 min |
| **Total Docker** | **~40 min** |
| **Total Nativo** | **~2.5 horas** |

---

## 10. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| `sensor_msgs_py` no disponible en Humble | Baja | Usar lectura manual de PointCloud2 (sección 5.1) |
| PCL 1.12 (Humble) vs 1.14 (Jazzy) incompatibilidad | Muy baja | El SDK usa PCL estándar, sin features específicos de versión |
| `libunilidar_sdk2.a` incompatible con glibc de 22.04 | Baja | La lib fue compilada para Ubuntu 20.04/22.04 originalmente según el SDK README |
| Docker: X11 forwarding falla para RViz | Media | Usar `--network host` + `xhost +local:` o VNC alternativo |
| Docker: UDP no funciona con `--network host` | Baja | `--network host` comparte la stack de red del host, UDP pasa directo |
