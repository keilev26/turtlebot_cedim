import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/calebcamargo/proyects/Unitree/lidar_ws/install/unitree_lidar_test'
