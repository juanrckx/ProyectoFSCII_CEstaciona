import serial
import json
import threading
import time 
from parking import ParkingSystem

class SerialCommunication:
    def __init__(self, ports=['COM8', 'COM7']):
        self.ports = ports
        self.serial_conns = {}
        self.running = False
        self.threads = {}

        #Inicializar sistemas de parqueo
        for i, port in enumerate(ports, 1):
            self.parking_systems[i] = ParkingSystem(parking_id=i)

    def connect(self):
        for i, port in enumerate(self.ports, 1):
            try:
                conn = serial.Serial(port, 115200, timeout=1)
                self.serial_conns[i] = conn
                print(f"Conectado a parqueo {i} en {port}")
            
            except Exception as e:
                print(f"Error conectando a {port}: {e}")

        return len(self.serial_conns) > 0
    
    def disconnect(self):
        self.running = False
        for conn in self.serial_conns.values():
            if conn and conn.is_open:
                conn.close()

    def send_command(self, parking_id, command):
        try:
            conn = self.serial_conns.get(parking_id)
            if conn and conn.is_open:
                command['parking_id'] = parking_id
                message = json.dumps(command) + '\n'
                conn.write(message.encode())

        except Exception as e:
            print(f"Error enviando a parqueo {parking_id}: {e}")

    def read_messages(self, parking_id):
        conn = self.serial_conns[parking_id]
        while self.running:
            try:
                if conn and conn.in_waiting:
                    line = conn.readline().decode().strip()
                    if line:
                        message = json.loads(line)
                        self.process_message(message)
            
            except Exception as e:
                print(f"Error leyendo parqueo {parking_id}: {e}")

            time.sleep(0.01)

    def process_message(self, message):
        parking_id = message.get('parking_id')
        msg_type = message.get('type')
        parking_system = self.parking_systems.get(parking_id)

        if not parking_system:
            return
        if msg_type == 'sensor_update':
            space1_occupied = message.get('space1_occupied', False)
            space2_occupied = message.get('space2_occupied', False)

            #Sincronizar estado de espacios
            current_spaces = parking_system.occupied_spaces

            if space1_occupied and current_spaces < 1:
                parking_system.take_manual_space(1)
            elif not space1_occupied and current_spaces >= 1:
                parking_system.release_manual_space(1)

            if space2_occupied and current_spaces < 2:
                parking_system.take_manual_space(2)
            elif not space2_occupied and current_spaces >= 2:
                parking_system.release_manual_space(2)

        elif msg_type == 'button_press':
            button = message.get('button')
            if button == 'enter':
                vehicle_id, space = parking_system.enter_vehicle()
                if vehicle_id:
                    print(f"Parqueo {parking_id}: Vehículo {vehicle_id} entró al espacio {space}")
                    self.send_command(parking_id, {
                        'type': 'barrier_control',
                        'state': 'open'
                    })
                    threading.Timer(3, lambda: self.send_command(parking_id, {
                        'type': 'barrier_control',
                        'state': 'closed'
                    })).start()

                elif button == 'exit':
                    if parking_system.pending_payment_vehicles:
                        parking_system.confirm_exit()
                        self.send_command(parking_id, {
                            'type': 'barrier_control',
                            'state': 'open'
                        })
                        threading.Timer(3, lambda: self.send_command(parking_id, {
                            'type': 'barrier_control',
                            'state': 'closed'
                        })).start()
                    
                    else:
                        vehicle_id, fee = parking_system.request_exit()
                        if vehicle_id:
                            self.send_command(parking_id, {
                                'type': 'display_update',
                                'value': str(fee // 1000),
                                'mode': 'fee'
                            })

    def start(self):
        if self.connect():
            self.running = True
            for parking_id in self.serial_conns.keys():
                thread = threading.Thread(target=self.read_messages, args=(parking_id,))
                thread.daemon = True
                thread.start()
                self.threads[parking_id] = thread

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
        return self.get_parking_system.get(parking_id)
    
    def get_all_parking_systems(self):
        return self.parking_systems
    
#Instancia global
serial_comm = SerialCommunication()

def init_serial_communication(ports=['COM8', 'COM7']):
    serial_comm.ports = ports
    return serial_comm.start()

#asdasdas