import time
import json
from datetime import datetime

class ParkingSystem:
    def __init__(self):
        self.total_space = 2
        self.available_space = 2
        self.occupied_spaces = 0
        self.boom_barrier_state = "closed"
        self.parked_vehicles = {} # {vehicle_id: {hora de entrada y espacio}}
        self.parked_vehicles_historial = []
        self.base_fee = 1000 #1000 colones por 10 segundos
        self.display_mode = "spaces" #espacios o tarifa
        self.display_value = 2
        self.pending_payment_vehicles = None

        #Cargar datos al iniciar
        self.load_data()


    def enter_vehicle(self):
        if self.available_space > 0:
            #Genera ID unico
            vehicle_id = f"V{int(time.time())}"

            #Asigna espacio
            space = 1 if self.occupied_spaces == 0 else 2

            #Registro del vehiculo
            self.parked_vehicles[vehicle_id] = {"entry_time": time.time(),
                                                "space": space,
                                                'entry_time_str': datetime.now().strftime("%H:%M:%S")}

            #Actualiza contadores
            self.available_space -= 1
            self.occupied_spaces += 1

            #Actualizar display
            self.display_mode = "spaces"
            self.display_value = self.available_space

            #Abrir aguja
            self.boom_barrier_state = "open"

            return vehicle_id, space

        return None, None

    def request_exit(self):
        if not self.parked_vehicles:
            return None, 0

        #Toma el primer vehiculo
        self.pending_payment_vehicles = list(self.parked_vehicles.keys())[0]
        dataset = self.parked_vehicles[self.pending_payment_vehicles]

        #Calcula el costo
        parked_time = time.time() - dataset["entry_time"]
        fee = self.calculate_fee(parked_time)

        #Mostrar en display
        self.display_mode = "fee"
        self.display_value = fee // 1000

        return self.pending_payment_vehicles, fee

    def confirm_exit(self):
        if not self.pending_payment_vehicles:
            return False

        vehicle_id = self.pending_payment_vehicles
        dataset = self.parked_vehicles[vehicle_id]

        #Calcula tiempo y costo final
        parked_time = time.time() - dataset["entry_time"]
        fee = self.calculate_fee(parked_time)

        #Registrar en el historial
        self.parked_vehicles_historial.append({
            "vehicle_id": vehicle_id,
            "entry_time": dataset["entry_time_str"],
            "exit_time": time.time(),
            "parked_time": parked_time,
            "fee": fee,
            "entry_time_str": dataset["entry_time_str"],
            "exit_time_str": datetime.now().strftime("%H:%M:%S")
        })

        #Liberar espacios
        del self.parked_vehicles[vehicle_id]
        self.available_space += 1
        self.occupied_spaces -= 1
        self.pending_payment_vehicles = None

        #Actualizar display
        self.display_mode = "spaces"
        self.display_value = self.available_space

        #Abrir aguja
        self.boom_barrier_state = "open"

        return True

    def calculate_fee(self, time_seconds):
        stations = max(1, int(time_seconds) // 10)
        return stations * self.base_fee

    def control_boom_barrier(self, state):
        if "abierta" in state.lower():
            self.boom_barrier_state = "open"
        else:
            self.boom_barrier_state = "closed"

    def take_manual_space(self, space):
        if space == 1 and self.occupied_spaces == 0:
            self.available_space -= 1
            self.occupied_spaces += 1
            self.display_value = self.available_space
        elif space == 2 and self.occupied_spaces <= 1:
            self.available_space -= 1
            self.occupied_spaces += 1
            self.display_value = self.available_space

    def release_manual_space(self, space):
        if space == 1 and self.occupied_spaces >= 1:
            self.available_space += 1
            self.occupied_spaces -= 1
            self.display_value = self.available_space
        elif space == 2 and self.occupied_spaces == 2:
            self.available_space += 1
            self.occupied_spaces -= 1
            self.display_value = self.available_space

    def get_stats(self):
        total_vehicles = len(self.parked_vehicles_historial)

        if total_vehicles == 0:
            return {
                'total_vehicles': 0,
                'average_stance': 0,
                'profits_colons': 0,
                'profits_dollars': 0
            }

        #Calcular promedio de estancia
        total_time = sum(v['parked_time'] for v in self.parked_vehicles_historial)
        average_stance = total_time / total_vehicles

        #Calcular ganancias
        profits_colons = sum(v['fee'] for v in self.parked_vehicles_historial)

        #Simular tipo de cambio 500 por ahora
        profits_dollars = profits_colons / 500

        return {
            'total_vehicles': total_vehicles,
            'average_stance': average_stance,
            'profits_colons': profits_colons,
            'profits_dollars': profits_dollars
        }

    def update(self):
        pass

    def save_data(self):
        #Guarda los datos en un archivo json
        data = {
            'vehicle_historial': self.parked_vehicles_historial,
            'config': {'base_fee': self.base_fee,
                       'total_space': self.total_space,
                       }
        }
        try:
            with open('data.json', 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def load_data(self):
        #Carga los datos desde un archivo json
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
                self.parked_vehicles_historial = data.get('vehicle_historial', [])
        except:
            pass
