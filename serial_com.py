import serial
import json
import threading
import time 
from parking import ParkingSystem

class SerialCommunication:
    def __init__(self, ports=['COM7', 'COM8']):
        self.ports = ports
        self.serial_conns = {}
        self.parking_systems = {}
        self.running = False
        self.threads = {}
        self.write_lock = threading.Lock()  # Lock para escritura thread-safe

        # Inicializar sistemas de parqueo
        for i in range(1, 3):  # Siempre crear 2 sistemas
            self.parking_systems[i] = ParkingSystem(parking_id=i)

    def connect(self):
        success_count = 0
        for i, port in enumerate(self.ports, 1):
            max_attempts = 2
            for attempt in range(max_attempts):
                try:
                    print(f"🔄 Conectando a {port} (Intento {attempt+1}/{max_attempts})...")
                    
                    # Configurar conexión con timeout adecuado
                    conn = serial.Serial(
                        port=port,
                        baudrate=115200,
                        timeout=0.1,           # Timeout corto para lectura
                        write_timeout=0.5,     # Timeout para escritura
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE
                    )
                    
                    # Esperar estabilización
                    time.sleep(2)
                    conn.reset_input_buffer()
                    conn.reset_output_buffer()
                    
                    self.serial_conns[i] = conn
                    success_count += 1
                    print(f"✅ Conectado a Parqueo {i} en {port}")
                    break
                    
                except serial.SerialException as e:
                    print(f"❌ Error en {port}: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(1)
                    else:
                        print(f"⚠️ Saltando puerto {port} después de {max_attempts} intentos")
                        
                except Exception as e:
                    print(f"❌ Error inesperado en {port}: {e}")
                    break
        
        return success_count > 0
    
    def disconnect(self):
        self.running = False
        # Esperar a que los hilos terminen
        for thread in self.threads.values():
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Cerrar conexiones
        for parking_id, conn in self.serial_conns.items():
            if conn and conn.is_open:
                try:
                    conn.close()
                    print(f"🔌 Parqueo {parking_id}: Desconectado")
                except:
                    pass
        self.serial_conns.clear()

    def send_command(self, parking_id, command):
        """Envía comando de forma NO BLOQUEANTE"""
        if parking_id not in self.serial_conns:
            return False
            
        conn = self.serial_conns.get(parking_id)
        if not conn or not conn.is_open:
            return False
        
        try:
            with self.write_lock:  # Usar lock para thread safety
                command['parking_id'] = parking_id
                message = json.dumps(command) + '\n'
                conn.write(message.encode())
                return True
        except serial.SerialTimeoutException:
            print(f"⚠️ Timeout enviando a parqueo {parking_id}")
            return False
        except Exception as e:
            print(f"❌ Error enviando a parqueo {parking_id}: {e}")
            return False

    def read_messages(self, parking_id):
        """Hilo de lectura para cada puerto"""
        if parking_id not in self.serial_conns:
            return
            
        conn = self.serial_conns[parking_id]
        buffer = ""
        
        while self.running and conn and conn.is_open:
            try:
                # Leer datos disponibles (non-blocking por el timeout)
                if conn.in_waiting:
                    raw_data = conn.read(conn.in_waiting).decode('utf-8', errors='ignore')
                    buffer += raw_data
                    
                    # Procesar líneas completas
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                        
                        # Intentar procesar como JSON
                        self.process_json_line(parking_id, line)
                
                # Pequeña pausa para no saturar CPU
                time.sleep(0.01)
                    
            except serial.SerialException:
                print(f"⚠️ Error de conexión con Parqueo {parking_id}")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error en hilo Parqueo {parking_id}: {e}")
                time.sleep(0.5)

    def process_json_line(self, parking_id, line):
        """Procesa una línea como JSON"""
        try:
            # Buscar JSON en la línea (puede tener ruido)
            start = line.find('{')
            end = line.rfind('}')
            
            if start != -1 and end != -1 and end > start:
                json_str = line[start:end+1]
                message = json.loads(json_str)
                
                # Verificar que sea para este parqueo
                if message.get('parking_id') == parking_id:
                    self.process_message(message)
                elif message.get('parking_id') is None:
                    # Si no tiene ID, asumir que es para este hilo
                    message['parking_id'] = parking_id
                    self.process_message(message)
        except json.JSONDecodeError:
            # Ignorar líneas que no son JSON válido
            pass
        except Exception as e:
            print(f"⚠️ Error procesando línea: {e}")

    def process_message(self, message):
        parking_id = message.get('parking_id')
        msg_type = message.get('type')
        parking_system = self.parking_systems.get(parking_id)

        if not parking_system:
            return
            
        if msg_type == 'sensor_update':
            space1_occupied = message.get('space1_occupied', False)
            space2_occupied = message.get('space2_occupied', False)

            # Sincronizar estado de espacios
            if space1_occupied:
                parking_system.take_manual_space(1)
            else:
                parking_system.release_manual_space(1)

            if space2_occupied:
                parking_system.take_manual_space(2)
            else:
                parking_system.release_manual_space(2)

        elif msg_type == 'button_press':
            button = message.get('button')
            
            if button == 'enter':
                vehicle_id, space = parking_system.enter_vehicle()
                if vehicle_id:
                    print(f"🚗 Parqueo {parking_id}: Vehículo {vehicle_id} entró al espacio {space}")
                    self.control_barrier(parking_id, 'open')
                    # Cerrar después de 3 segundos
                    threading.Timer(3.0, lambda: self.control_barrier(parking_id, 'closed')).start()
            
            elif button == 'exit':  # CORREGIDO: Ahora está al mismo nivel que 'enter'
                if parking_system.pending_payment_vehicles:
                    parking_system.confirm_exit()
                    self.control_barrier(parking_id, 'open')
                    threading.Timer(3.0, lambda: self.control_barrier(parking_id, 'closed')).start()
                else:
                    vehicle_id, fee = parking_system.request_exit()
                    if vehicle_id:
                        print(f"💰 Parqueo {parking_id}: Costo {fee} CRC")
                        self.update_display(parking_id, fee // 1000, 'fee')

    def start(self):
        if self.connect():
            self.running = True
            for parking_id in self.serial_conns.keys():
                thread = threading.Thread(
                    target=self.read_messages, 
                    args=(parking_id,),
                    name=f"SerialReader-P{parking_id}",
                    daemon=True  # Hilo daemon para que termine con el programa
                )
                thread.start()
                self.threads[parking_id] = thread
                print(f"📡 Parqueo {parking_id}: Hilo de lectura iniciado")
            return True
        return False
    
    def update_display(self, parking_id, value, mode="spaces"):
        self.send_command(parking_id, {
            'type': 'display_update',
            'value': str(value),
            'mode': mode
        })

    def control_barrier(self, parking_id, state):
        self.send_command(parking_id, {
            'type': 'barrier_control',
            'state': state
        })

    def control_led(self, parking_id, space, state):
        self.send_command(parking_id, {
            'type': 'led_control',
            'space': space,
            'state': state
        })

    def get_parking_system(self, parking_id):
        return self.parking_systems.get(parking_id)
    
    def get_all_parking_systems(self):
        return self.parking_systems

# Instancia global
serial_comm = SerialCommunication()

def init_serial_communication(ports=['COM7', 'COM8']):
    serial_comm.ports = ports
    return serial_comm.start()