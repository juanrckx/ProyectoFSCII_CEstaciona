import pygame
from components import *
from serial_com import *

class ParkingGUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("dejavusans", 24)
        self.title_font = pygame.font.SysFont("dejavusans", 32, bold=True)

        self.create_components()

    def create_components(self):
        #Display 7 segmentos
        self.display1 = Display7Segment(50, 50, 80)
        self.display2 = Display7Segment(200, 50, 80)

        #Botones
        self.buttons = {
            'enter1': Button(50, 200, 150, 50, "Entrar Parqueo 1"),
            'enter2': Button(200, 200, 150, 50, "Entrar Parqueo 2"),
            'exit1': Button(50, 270, 150, 50, "Pagar/Salir 1"),
            'exit2': Button(200, 270, 150, 50, "Pagar/Salir 2"),
            'open_boom_barrier': Button(50, 340, 150, 50, "Abrir aguja"),
            'close_boom_barrier': Button(50, 410, 150, 50, "Cerrar aguja"),
            'update_exchange': Button(50, 520, 150, 50, "Actualizar TC"),
        }
        #Espacios de parqueo
        self.space1_p1 = ParkingSite(300, 100, "P1-E1")
        self.space2_p1 = ParkingSite(300, 250, "P1-E2")
        self.space1_p2 = ParkingSite(600, 100, "P2-E1")
        self.space2_p2 = ParkingSite(600, 250, "P2-E2")

        #Panel de estadisticas
        self.stats_panel_rect = pygame.Rect(600, 100, 500, 350)

    def draw(self, screen, serial_comm):
        #Actualizar componentes
        self.update_state(serial_comm)

        #Dibujar titulo
        title = self.title_font.render("CEstaciona - Parqueo Inteligente", True, BLACK)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 20))

        #Dibujar display
        self.display1.draw(screen)
        self.display2.draw(screen)

        #Dibujar botones
        for button in self.buttons.values():
            button.draw(screen)

        #Definir estado de las agujas
        parking1 = serial_comm.get_parking_system(1)
        parking2 = serial_comm.get_parking_system(2)

        #Dibujar estado de la aguja
        barrier_text1 = "Aguja 1 " + ("Abierta" if parking1 and parking1.boom_barrier_state == "open" else "Cerrada")
        barrier_text2 = "Aguja 2 " + ("Abierta" if parking2 and parking2.boom_barrier_state == "open" else "Cerrada")

        barrier_surface1 = self.font.render(f"Estado aguja: {barrier_text1}", True, BLACK)
        barrier_surface2 = self.font.render(f"Estado aguja: {barrier_text2}", True, BLACK)
        screen.blit(barrier_surface1, (50, 480))
        screen.blit(barrier_surface2, (200, 480))

        #Usar tipo de cambio del primer parqueo
        exchange_rate = parking1.exchange_rate
        exchange_text = self.font.render(f"Tipo de cambio: 1CRC = ${1/exchange_rate:.4f}", True, BLACK)
        screen.blit(exchange_text, (50, 570))

        #Dibujar espacios de parqueo
        self.space1_p1.draw(screen)
        self.space2_p1.draw(screen)
        
        self.space1_p2.draw(screen)
        self.space2_p2.draw(screen)

        #Dibujar panel de estadisticas combinadas
        self.draw_stats(screen, serial_comm)


    def update_state(self, serial_comm):
        #Actualizar displays con datos de cada parqueo
        parking1 = serial_comm.get_parking_system(1)
        parking2 = serial_comm.get_parking_system(2)

        if parking1:
            self.display1.update(parking1.display_value, parking1.display_mode)
            self.space1_p1.occupied = parking1.occupied_spaces >= 1
            self.space2_p1.occupied = parking1.occupied_spaces >= 2

        if parking2:
            self.display1.update(parking2.display_value, parking2.display_mode)
            self.space1_p2.occupied = parking2.occupied_spaces >= 1
            self.space2_p2.occupied = parking2.occupied_spaces >= 2


        #Actualizar botones (hover)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons.values():
            button.update(mouse_pos)

    def draw_stats(self, screen, serial_comm):
        #Fondo del panel
        pygame.draw.rect(screen, LIGHT_GRAY, self.stats_panel_rect, border_radius=10)
        pygame.draw.rect(screen, GRAY, self.stats_panel_rect, 2, border_radius=10)

        #Titulo del panel
        stats_title = self.title_font.render("Estadisticas", True, BLACK)
        screen.blit(stats_title, (self.stats_panel_rect.centerx - stats_title.get_width() // 2, self.stats_panel_rect.y + 10))

        #Obtener estadísticas de ambos parqueos
        parking1 = serial_comm.get_parking_system(1)
        parking2 = serial_comm.get_parking_system(2)

        if not parking1 or not parking2:
            return

        #Obtener estadisticas
        stats1 = parking1.get_stats()
        stats2 = parking2.get_stats()

        #Calcular totales combinados
        total_vehicles = stats1['total_vehicles'] + stats2['total_vehicles']
        total_profits_colons = stats1['profits_colons'] + stats2['profits_colons']
        total_profits_dollars = stats1['profits_dollars'] + stats2['profits_dollars']

        #Calcular promedio combinado (ponderado)
        if total_vehicles > 0:
            avg_stance = (stats1['average_stance'] * stats1['total_vehicles'] + 
                          stats2['average_stance'] * stats2['total_vehicles']) / total_vehicles
        else:
            avg_stance = 0

        #Dibujar estadísticas
        y_pos = self.stats_panel_rect.y + 60

        stats_text = [
            f"Vehículos totales: {total_vehicles}",
            f"Estancia promedio: {avg_stance: .1f} seg",
            f"Ganancias totales: {total_profits_colons:,} CRC",
            f"Ganancias totales: {total_profits_dollars: .2f} USD"
        ]
        for text in stats_text:
            surf_text = self.font.render(text, True, BLACK)
            screen.blit(surf_text, (self.stats_panel_rect.x + 20, y_pos))
            y_pos += 40


    def handle_click(self, mouse_pos, serial_comm):
        #Verificar botones de control
        parking1 = serial_comm.get_parking_system(1)
        parking2 = serial_comm.get_parking_system(2)

        if not parking1 or not parking2:
            return

        if self.buttons['enter1'].check_click(mouse_pos, True):
            vehicle_id, space = parking1.enter_vehicle()
            if vehicle_id:
                print(f"Parqueo 1: Vehiculo {vehicle_id} entró al espacio {space}")
                serial_comm.control_barrier(1, "open")

        elif self.buttons['exit1'].check_click(mouse_pos, True):
            if parking1.pending_payment_vehicles:
                if parking1.confirm_exit():
                    print("Parqueo 1: Vehículo salió")
                    serial_comm.control_barrier(1, "open")
            else:
                vehicle_id, fee = parking1.request_exit()
                if vehicle_id:
                    print(f"Parqueo 1: Vehículo {vehicle_id} - Costo: {fee}CRC")

        elif self.buttons['enter2'].check_click(mouse_pos, True):
            vehicle_id, space = parking2.enter_vehicle()
            if vehicle_id:
                print(f"Parqueo 2: Vehiculo {vehicle_id} entró al espacio {space}")
                serial_comm.control_barrier(2, "open")

        elif self.buttons['exit2'].check_click(mouse_pos, True):
            if parking2.pending_payment_vehicles:
                if parking2.confirm_exit():
                    print("Parqueo 2: Vehículo salió")
                    serial_comm.control_barrier(2, "open")
            
            else:
                vehicle_id, fee = parking2.request_exit()
                if vehicle_id:
                    print(f"Parqueo 2: Vehículo {vehicle_id} - Costo {fee} CRC")
        
        elif self.buttons['close_boom_barrier'].check_click(mouse_pos, True):
            serial_comm.control_barrier(1, "closed")
            serial_comm.control_barrier(2, "closed")

        elif self.buttons['update_exchange'].check_click(mouse_pos, True):
            parking1.update_exchange_rate()
            parking2.exchange_rate = parking1.exchange_rate #Sincronizar
            parking2.last_exchange_update = parking1.last_exchange_update
            print("Tipo de cambio actualizado para ambos parqueos")

        #Verificar controles manuales de espacios para parqueo 1
        space1_action = self.space1_p1.check_click(mouse_pos)
        if space1_action == "occupy":
            parking1.take_manual_space(1)
            serial_comm.control_led(1, 1, False) #LED apagado = ocupado
        elif space1_action == "release":
            parking1.release_manual_space(1)
            serial_comm.control_led(1, 1, True) #LED encendido = disponible

        space2_action = self.space2_p1.check_click(mouse_pos)
        if space2_action == "occupy":
            parking1.take_manual_space(2)
            serial_comm.control_led(1, 2, False)
        elif space2_action == "release":
            parking1.release_manunal_space(2)
            serial_comm.control_led(1, 2, True)


        #Verificar controles manuales de espacios para parqueo 2
        space1_action_p2 = self.space1_p2.check_click(mouse_pos)
        if space1_action == "occupy":
            parking2.take_manual_space(1)
            serial_comm.control_led(2, 1, False) #LED apagado = ocupado
        elif space1_action_p2 == "release":
            parking2.release_manual_space(1)
            serial_comm.control_led(2, 1, True) #LED encendido = disponible

        space2_action_p2 = self.space2_p2.check_click(mouse_pos)
        if space2_action == "occupy":
            parking2.take_manual_space(2)
            serial_comm.control_led(2, 2, False)
        elif space2_action == "release":
            parking2.release_manunal_space(2)
            serial_comm.control_led(2, 2, True)
#aasdasda