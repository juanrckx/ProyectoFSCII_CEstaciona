import socket
import threading
import json
import time
from parking import ParkingSystem


class WiFiCommunication:
    def __init__(self, host='0.0.0.0', base_port=5000):
        self.host = host
        self.base_port = base_port
        self.servers = {}
        self.clients = {}
        self.client_addresses = {}
        self.parking_systems = {}
        self.running = False
        self.threads = {}
        self.lock = threading.Lock()

        for i in range(1, 3):
            self.parking_systems[i] = ParkingSystem(parking_id=i)

    def start_server_for_parking(self, parking_id):
        port = self.base_port + parking_id
        
        print(f"\n🔧 INICIANDO SERVIDOR PARQUEO {parking_id}")
        print(f"   Puerto: {port}")
        print(f"   Host: {self.host}")
        print(f"   IPs disponibles de la PC:")
        
        # Mostrar todas las IPs de la PC
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        print(f"   - {addr['addr']}:{port}")
        except:
            pass
        
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # ⚠️ ESTA LÍNEA ES CRÍTICA ⚠️
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Vincular a TODAS las interfaces
            server.bind((self.host, port))
            
            # ⚠️ AUMENTAR backlog a 5 ⚠️
            server.listen(5)
            server.settimeout(5)  # Timeout mayor
            
            self.servers[parking_id] = server
            
            # Obtener dirección real del socket
            sockname = server.getsockname()
            print(f"✅ Servidor REALMENTE escuchando en:")
            print(f"   {sockname[0]}:{sockname[1]}")
            print(f"   Puerto real: {sockname[1]}")
            
            # Función para aceptar conexiones
            def handle_parking_connection():
                print(f"   🧵 Hilo aceptador INICIADO")
                
                connection_count = 0
                while self.running:
                    try:
                        print(f"   Parqueo {parking_id}: Esperando conexión #{connection_count + 1}...")
                        
                        # ⚠️ ACEPTAR con timeout
                        client, addr = server.accept()
                        connection_count += 1
                        
                        print(f"   🎉 CONEXIÓN #{connection_count} ACEPTADA de {addr}")
                        
                        # Configurar socket del cliente
                        client.settimeout(10.0)  # ⚠️ Timeout largo inicial
                        client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                        
                        with self.lock:
                            self.clients[parking_id] = client
                            self.client_addresses[parking_id] = addr
                        
                        print(f"   Cliente registrado: {addr}")
                        
                        # Enviar mensaje de bienvenida INMEDIATO
                        welcome_msg = json.dumps({
                            'type': 'welcome',
                            'parking_id': parking_id,
                            'status': 'connected',
                            'message': 'Conexión establecida'
                        }) + '\n'
                        
                        client.send(welcome_msg.encode())
                        print(f"   Mensaje de bienvenida enviado")
                        
                        # Iniciar hilo receptor
                        receiver_thread = threading.Thread(
                            target=self.receive_from_parking,
                            args=(parking_id, client),
                            daemon=True,
                            name=f"Receiver-P{parking_id}-{connection_count}"
                        )
                        receiver_thread.start()
                        
                        print(f"   Hilo receptor #{connection_count} iniciado")
                        
                    except socket.timeout:
                        # Timeout normal en accept()
                        continue
                    except Exception as e:
                        print(f"❌ Error aceptando conexión: {e}")
                        import traceback
                        traceback.print_exc()
                        time.sleep(1)
            
            # Iniciar hilo aceptador
            connection_thread = threading.Thread(
                target=handle_parking_connection,
                daemon=True,
                name=f"Acceptor-P{parking_id}"
            )
            connection_thread.start()
            self.threads[parking_id] = connection_thread
            
            print(f"✅ Hilo aceptador para Parqueo {parking_id} INICIADO")
            
        except Exception as e:
            print(f"❌ ERROR GRAVE iniciando servidor: {e}")
            import traceback
            traceback.print_exc()

    def receive_from_parking(self, parking_id, client_socket):
        """Recibir datos con manejo mejorado de errores"""
        print(f"📡 Iniciando recepción para Parqueo {parking_id}")
        
        buffer = ""
        message_count = 0
        
        try:
            while self.running:
                try:
                    # Recibir datos con timeout
                    data = client_socket.recv(1024)
                    
                    if not data:
                        print(f"🔌 Parqueo {parking_id}: Conexión cerrada por cliente")
                        break
                    
                    message_count += 1
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    print(f"📨 Parqueo {parking_id}: Recibido chunk #{message_count}, buffer: {len(buffer)} chars")
                    
                    # Procesar todas las líneas completas
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            print(f"📝 Parqueo {parking_id}: Procesando: {line[:80]}...")
                            self.process_message(parking_id, line)
                    
                    # Reducir timeout después del primer mensaje
                    if message_count == 1:
                        client_socket.settimeout(0.1)
                    
                except socket.timeout:
                    # Timeout normal para lectura no bloqueante
                    continue
                except ConnectionResetError:
                    print(f"🔌 Parqueo {parking_id}: Conexión reseteada por el cliente")
                    break
                except Exception as e:
                    print(f"⚠️  Parqueo {parking_id}: Error en recepción: {e}")
                    break
            
        except Exception as e:
            print(f"❌ Parqueo {parking_id}: Error crítico en hilo receptor: {e}")
        
        finally:
            # Limpieza
            print(f"🧹 Parqueo {parking_id}: Limpiando conexión...")
            with self.lock:
                if parking_id in self.clients and self.clients[parking_id] == client_socket:
                    try:
                        client_socket.close()
                    except:
                        pass
                    self.clients.pop(parking_id, None)
                    self.client_addresses.pop(parking_id, None)
            
            print(f"📴 Parqueo {parking_id}: Desconectado (recibió {message_count} mensajes)")
            
    def process_message(self, parking_id, message):
        try:
            #Buscar JSON en el mensaje
            start = message.find('{')
            end = message.rfind('}')

            if start != -1 and end != -1 and end > start:
                json_str = message[start:end+1]
                data = json.loads(json_str)

                #Verificar que sea para este parqueo
                if data.get('parking_id') == parking_id:
                    self.handle_parking_message(parking_id, data)

        except json.JSONDecodeError:
            print(f"Mensaje no JSON de parqueo {parking_id}: {message}")
        except Exception as e:
            print(f"Error procesando mensaje parqueo {parking_id}: {e}")
    
    def handle_parking_message(self, parking_id, message):
        msg_type = message.get('type')
        parking_system = self.parking_systems.get(parking_id)

        if not parking_system:
            return
        
        if msg_type == 'sensor_update':
            space1_occupied = message.get('space1_occupied', False)
            space2_occupied = message.get('space2_occupied', False)

            #Sincronizar estado de espacios
            if space1_occupied:
                parking_system.take_manual_space(1)
            else:
                parking_system.release_manual_space(1)

            if space2_occupied:
                parking_system.take_manual_space(2)
            else:
                parking_system.release_manual_space(2)

            #Actualizar display
            self.update_display(parking_id, parking_system.available_space, 'spaces')

        elif msg_type == 'button_press':
            button = message.get('button')
            
            if button == 'enter':
                vehicle_id, space = parking_system.enter_vehicle()
                if vehicle_id:
                    print(f"🚗 Parqueo {parking_id}: Vehículo {vehicle_id} entró al espacio {space}")
                    self.control_barrier(parking_id, 'open')
                    
                    # Actualizar display
                    self.update_display(parking_id, parking_system.available_space, 'spaces')
                    
                    # Cerrar barrera después de 3 segundos
                    threading.Timer(3.0, lambda: self.control_barrier(parking_id, 'closed')).start()
            
            elif button == 'exit':
                if parking_system.pending_payment_vehicles:
                    parking_system.confirm_exit()
                    self.control_barrier(parking_id, 'open')
                    
                    # Actualizar display
                    self.update_display(parking_id, parking_system.available_space, 'spaces')
                    
                    # Cerrar barrera después de 3 segundos
                    threading.Timer(3.0, lambda: self.control_barrier(parking_id, 'closed')).start()
                else:
                    vehicle_id, fee = parking_system.request_exit()
                    if vehicle_id:
                        print(f"💰 Parqueo {parking_id}: Costo {fee} CRC")
                        self.update_display(parking_id, fee // 1000, 'fee')
        
        elif msg_type == 'connection':
            print(f"📡 Parqueo {parking_id}: {message.get('status', 'connected')}")
            # Enviar estado actual al parqueo
            self.update_display(parking_id, parking_system.available_space, 'spaces')
    
    def send_command(self, parking_id, command):
        """Enviar comando a un parqueo específico"""
        with self.lock:
            if parking_id not in self.clients:
                return False
            
            client = self.clients.get(parking_id)
            if not client:
                return False
        
        try:
            command['parking_id'] = parking_id
            message = json.dumps(command) + '\n'
            client.send(message.encode())
            return True
        except Exception as e:
            print(f"❌ Error enviando a Parqueo {parking_id}: {e}")
            
            # Intentar limpiar conexión fallida
            with self.lock:
                if parking_id in self.clients:
                    try:
                        self.clients[parking_id].close()
                    except:
                        pass
                    del self.clients[parking_id]
            
            return False
    
    def start(self):
        """Iniciar todos los servidores"""
        print("🚀 Iniciando servidores WiFi para ambos parqueos...")
        self.running = True
        
        # Iniciar servidores para ambos parqueos
        for parking_id in [1, 2]:
            self.start_server_for_parking(parking_id)
        
        print("✅ Servidores WiFi iniciados. Esperando conexiones...")
        return True
    
    def stop(self):
        """Detener todos los servidores"""
        print("🛑 Deteniendo servidores WiFi...")
        self.running = False
        
        # Cerrar todas las conexiones
        with self.lock:
            for parking_id, client in self.clients.items():
                try:
                    client.close()
                except:
                    pass
            
            for parking_id, server in self.servers.items():
                try:
                    server.close()
                except:
                    pass
            
            self.clients.clear()
            self.servers.clear()
        
        print("✅ Servidores WiFi detenidos.")
    
    # Métodos de interfaz (iguales que en serial_com.py)
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
    
    def get_connection_status(self, parking_id):
        """Verificar estado de conexión"""
        with self.lock:
            return parking_id in self.clients and self.clients[parking_id] is not None

# Instancia global (similar a serial_com.py)
wifi_comm = WiFiCommunication()

def init_wifi_communication():
    """Inicializar comunicación WiFi"""
    return wifi_comm.start()