# config_wifi.py
# Configuración WiFi para ambos dispositivos

# Configuración de la red WiFi
WIFI_CONFIG = {
    'ssid': 'Casa4',        # Cambiar por tu SSID
    'password': 'cartago04',    # Cambiar por tu contraseña
    'server_ip': '192.168.18.15', # IP de la PC servidor
    'server_port_base': 5000      # Puerto base
}

# Configuración de cada Raspberry Pi Pico W
PICO_CONFIGS = {
    1: {  # Parqueo 1
        'parking_id': 1,
        'name': 'Parqueo-01',
        'port_offset': 0  # Usará puerto 5001
    },
    2: {  # Parqueo 2
        'parking_id': 2,
        'name': 'Parqueo-02',
        'port_offset': 1  # Usará puerto 5002
    }
}