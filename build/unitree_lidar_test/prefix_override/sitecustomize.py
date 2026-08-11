import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/cedim/turtlebot_proyecto/install/unitree_lidar_test'
