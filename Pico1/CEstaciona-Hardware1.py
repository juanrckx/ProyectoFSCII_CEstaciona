from machine import Pin, ADC, PWM
import network
import socket
import json
import time
import ubinascii

#Configuracion WiFi-
WIFI_SSID = "Casa4"
WIFI_PASSWORD = "cartago04"
SERVER_IP = "192.168.18.15"
SERVER_PORT = 5000

#Configuración de los pines

SEGMENT_PINS = [Pin(7, Pin.OUT),
                Pin(6, Pin.OUT),
                Pin(5, Pin.OUT),
                Pin(4, Pin.OUT),
                Pin(3, Pin.OUT),
                Pin(2, Pin.OUT),
                Pin(8, Pin.OUT),
                ]

COMMON_PIN = Pin(7, Pin.OUT) #Cátodo común

#Botones
BTN_ENTER = Pin(16, Pin.IN, Pin.PULL_UP)
BTN_EXIT = Pin(17, Pin.IN, Pin.PULL_UP)

#Sensores LDR
LDR1 = ADC(26)
LDR2 = ADC(27)

#LEDs
LED1 = Pin(18, Pin.OUT)
LED2 = Pin(19, Pin.OUT)

#Servomotor
SERVO = PWM(Pin(15))
SERVO.freq(50)

# Mapeo display 7 segmentos
DIGIT_MAP = {
    '0': [1, 1, 1, 1, 1, 1, 0], '1': [0, 1, 1, 0, 0, 0, 0],
    '2': [1, 1, 0, 1, 1, 0, 1], '3': [1, 1, 1, 1, 0, 0, 1],
    '4': [0, 1, 1, 0, 0, 1, 1], '5': [1, 0, 1, 1, 0, 1, 1],
    '6': [1, 0, 1, 1, 1, 1, 1], '7': [1, 1, 1, 0, 0, 0, 0],
    '8': [1, 1, 1, 1, 1, 1, 1], '9': [1, 1, 1, 1, 0, 1, 1]
}

class ParkingHardwareWiFi:
    def __init__(self, parking_id=1):
        self.parking_id = parking_id
        self.ldr_threshold = 30000
        self.servo_closed = 1500
        self.servo_open = 2500
        self.last_btn_enter = True
        self.last_btn_exit = True
        self.display_mode = "spaces"
        self.display_value = "2"
        self.socket = None
        self.connected = False
        
        #Obtener MAC address única
        self.mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
        print(f"MAC Address: {self.mac}")
        
        self.setup_servo()
        self.initialize_display()
        self.connect_to_wifi()
        
    def connect_to_wifi(self):
        """Conectar a la red WiFi y luego al servidor"""
        print(f"Conectando a WiFi {WIFI_SSID}...")
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            
            # Esperar conexión (máximo 10 segundos)
            for i in range(20):
                if wlan.isconnected():
                    break
                time.sleep(0.5)
        
        if wlan.isconnected():
            print(f"WiFi conectado! IP: {wlan.ifconfig()[0]}")
            self.connect_to_server()
        else:
            print("Error: No se pudo conectar a WiFi")
            
    def connect_to_server(self):
        """Conectar al servidor TCP en la PC"""
        print(f"Conectando al servidor {SERVER_IP}:{SERVER_PORT + self.parking_id}...")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.socket = socket.socket()
                self.socket.connect((SERVER_IP, SERVER_PORT + self.parking_id))
                self.connected = True
                print(f"Conexión establecida con el servidor (Intento {attempt+1})")
                
                # Enviar mensaje de identificación
                self.send_data({
                    'type': 'connection',
                    'parking_id': self.parking_id,
                    'status': 'connected',
                    'mac': self.mac
                })
                return
                
            except Exception as e:
                print(f"Error de conexión (intento {attempt+1}): {e}")
                time.sleep(2)
        
        print("Error: No se pudo conectar al servidor después de varios intentos")
        self.connected = False
    
    def initialize_display(self):
        for pin in SEGMENT_PINS:
            pin.value(0)
        COMMON_PIN.value(0)
        
    def setup_servo(self):
        self.set_servo_position(self.servo_closed)
        
    def set_servo_position(self, us):
        duty = int(us * 65535 / 20000)
        SERVO.duty_u16(duty)
        
    
    def send_data(self, data):
        if not self.connected:
            return False
        
        try:
            data['parking_id'] = self.parking_id
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode())
            return True
        except Exception as e:
            print(f"Error enviando datos: {e}")
            self.connected = False
            
            self.connect_to_server()
            return False
        
    def receive_data(self):
        if not self.connected:
            return None
        
        try:
            self.socket.setblocking(False)
            try:
                data = self.socket.recv(1024)
                if data:
                    return json.loads(data.decode().strip())
            except:
                pass
            finally:
                self.socket.setblocking(True)
        except Exception as e:
            print(f"Error recibiendo datos: {e}")
        
        return None
    
    def update_display(self, value, mode="spaces"):
        try:
            self.display_value = str(value)
            self.display_mode = mode
            
            if self.display_value in DIGIT_MAP:
                segments = DIGIT_MAP[self.display_value]
            else:
                segments = DIGIT_MAP.get('0', [0, 0, 0, 0, 0, 0, 0])
                
            for i, state in enumerate(segments):
                SEGMENT_PINS[i].value(state)
                
        except Exception as e:
            print(f"Error actualizando display: {e}")
            
    def read_ldrs(self):
        #Leer sensores LDR
        ldr1_value = LDR1.read_u16()
        ldr2_value = LDR2.read_u16()
        
        ldr1_occupied = ldr1_value > self.ldr_threshold
        ldr2_occupied = ldr2_value > self.ldr_threshold
        
        return ldr1_occupied, ldr2_occupied
    
    def update_leds(self, space1_occupied, space2_occupied):
        #Actualizar LEDs
        LED1.value(not space1_occupied) #LED ON = disponible
        LED2.value(not space2_occupied)
        
        
    def check_buttons(self):
        btn_enter_state = BTN_ENTER.value()
        btn_exit_state = BTN_EXIT.value()
        
        
        enter_pressed = not btn_enter_state and self.last_btn_enter
        exit_pressed = not btn_exit_state and self.last_btn_exit
        
        self.last_btn_enter = btn_enter_state
        self.last_btn_exit = btn_exit_state
        
        return enter_pressed, exit_pressed
    
    def control_barrier(self, state):
        if state == "open":
            self.set_servo_position(self.servo_open)
        else:
            self.set_servo_position(self.servo_closed)
            
    def handle_command(self, command):
        """Procesar comandos recibidos del servidor"""
        cmd_type = command.get('type')
        
        if cmd_type == 'display_update':
            value = command.get('value', '0')
            mode = command.get('mode', 'spaces')
            self.update_display(value, mode)
            
        elif cmd_type == 'barrier_control':
            state = command.get('state', 'closed')
            self.control_barrier(state)
            
        elif cmd_type == 'led_control':
            state = command.get('state')
            space = command.get('space')
            if space == 1:
                LED1.value(state)
            elif space == 2:
                LED2.value(state)
    
    def run(self):
        """Bucle principal"""
        print(f"Parqueo {self.parking_id} iniciado (WiFi)")
        
        last_ldr1 = False
        last_ldr2 = False
        last_status_check = time.time()
        
        while True:
            try:
                # Revisar conexión periódicamente
                current_time = time.time()
                if current_time - last_status_check > 5:  # Cada 5 segundos
                    if not self.connected:
                        print("Intentando reconectar...")
                        self.connect_to_wifi()
                    last_status_check = current_time
                
                # Leer sensores y botones
                ldr1_occupied, ldr2_occupied = self.read_ldrs()
                enter_pressed, exit_pressed = self.check_buttons()
                
                # Enviar actualización de sensores si hay cambio
                if ldr1_occupied != last_ldr1 or ldr2_occupied != last_ldr2:
                    self.send_data({
                        'type': 'sensor_update',
                        'space1_occupied': ldr1_occupied,
                        'space2_occupied': ldr2_occupied
                    })
                    last_ldr1 = ldr1_occupied
                    last_ldr2 = ldr2_occupied
                
                # Enviar eventos de botones
                if enter_pressed:
                    self.send_data({
                        'type': 'button_press',
                        'button': 'enter'
                    })
                
                if exit_pressed:
                    self.send_data({
                        'type': 'button_press',
                        'button': 'exit'
                    })
                
                # Actualizar LEDs
                self.update_leds(ldr1_occupied, ldr2_occupied)
                
                # Procesar comandos del servidor
                command = self.receive_data()
                if command:
                    self.handle_command(command)
                
                time.sleep(0.05)  # Pequeña pausa
                
            except KeyboardInterrupt:
                print("Interrumpido por usuario")
                break
            except Exception as e:
                print(f"Error en bucle principal: {e}")
                time.sleep(1)

# ================= CONFIGURACIÓN POR PICO =================
PARKING_ID = 1

if __name__ == "__main__":
    hardware = ParkingHardwareWiFi(parking_id=PARKING_ID)
    hardware.run()

