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


    def enter_vehicle(self):
        if self.available_space > 0:
            #Genera ID unico
            vehicle_id = f"V{int(time.time())}"

            #Asigna espacio
            space = 1 if self.occupied_spaces == 0 else 2

            #Registro del vehiculo
            self.parked_vehicles[vehicle_id] = {"entry_time": time.time(), "space": space,
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


        self.pending_payment_vehicles = list(self.parked_vehicles.keys())[0]
        dataset = self.parked_vehicles[self.pending_payment_vehicles]

    def confirm_exit(self):

    def calculate_fee(self, time):

    def control_boom_barrier(self, state):

    def take_manual_space(self, space):

    def release_manual_space(self, space):

    def get_stats(self):

    def update(self):

    def save_data(self):

    def load_data(self):
