#!/usr/bin/env python3
"""Check if Unitree LiDAR is sending UDP data."""
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    sock.bind(('192.168.1.2', 6201))
except OSError as e:
    print(f'❌ No se pudo hacer bind: {e}')
    exit(1)

sock.settimeout(5.0)
print('📡 Escuchando UDP en 192.168.1.2:6201...')
print('   (esperando datos del LiDAR)')

try:
    data, addr = sock.recvfrom(65536)
    print(f'✅ Datos recibidos! {len(data)} bytes desde {addr}')
except socket.timeout:
    print('❌ Timeout: 5 segundos sin datos UDP')
    print('   El LiDAR podría estar en modo Serial, no en modo UDP.')
    print('   Hay que cambiarlo con el ejemplo set_to_udp_mode del SDK.')
sock.close()
