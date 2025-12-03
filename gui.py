import pygame
from components import *
from wifi_server import *  # Cambiado de serial_com a wifi_server

class ParkingGUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("dejavusans", 24)
        self.title_font = pygame.font.SysFont("dejavusans", 32, bold=True)
        self.small_font = pygame.font.SysFont("dejavusans", 18)

        self.create_components()

    def create_components(self):
        # Display 7 segmentos
        self.display1 = Display7Segment(50, 50, 80)
        self.display2 = Display7Segment(200, 50, 80)

        # Botones
        self.buttons = {
            'enter1': Button(50, 200, 150, 50, "Entrar Parqueo 1"),
            'enter2': Button(200, 200, 150, 50, "Entrar Parqueo 2"),
            'exit1': Button(50, 270, 150, 50, "Pagar/Salir 1"),
            'exit2': Button(200, 270, 150, 50, "Pagar/Salir 2"),
            'open_boom_barrier': Button(50, 340, 150, 50, "Abrir aguja"),
            'close_boom_barrier': Button(50, 410, 150, 50, "Cerrar aguja"),
            'update_exchange': Button(50, 520, 150, 50, "Actualizar TC"),
            'reconnect_wifi': Button(200, 520, 150, 50, "Reconectar WiFi"),  # Nuevo botón
        }
        
        # Espacios de parqueo
        self.space1_p1 = ParkingSite(300, 100, "P1-E1")
        self.space2_p1 = ParkingSite(300, 250, "P1-E2")
        self.space1_p2 = ParkingSite(600, 100, "P2-E1")
        self.space2_p2 = ParkingSite(600, 250, "P2-E2")

        # Panel de estadísticas
        self.stats_panel_rect = pygame.Rect(700, 400, 400, 350)

    def draw(self, screen, wifi_comm):  # Cambiado de serial_comm a wifi_comm
        # Actualizar componentes
        self.update_state(wifi_comm)  # Cambiado

        # Dibujar título
        title = self.title_font.render("CEstaciona - Parqueo Inteligente (WiFi)", True, BLACK)  # Modificado
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 20))

        # Dibujar display
        self.display1.draw(screen)
        self.display2.draw(screen)

        # Dibujar botones
        for button in self.buttons.values():
            button.draw(screen)

        # Obtener sistemas de parqueo
        parking1 = wifi_comm.get_parking_system(1)  # Cambiado
        parking2 = wifi_comm.get_parking_system(2)  # Cambiado

        # Dibujar estado de la aguja
        barrier_text1 = "Aguja 1 " + ("Abierta" if parking1 and parking1.boom_barrier_state == "open" else "Cerrada")
        barrier_text2 = "Aguja 2 " + ("Abierta" if parking2 and parking2.boom_barrier_state == "open" else "Cerrada")

        barrier_surface1 = self.font.render(f"Estado aguja: {barrier_text1}", True, BLACK)
        barrier_surface2 = self.font.render(f"Estado aguja: {barrier_text2}", True, BLACK)
        screen.blit(barrier_surface1, (50, 480))
        screen.blit(barrier_surface2, (325, 480))

        # Tipo de cambio
        if parking1:
            exchange_rate = parking1.exchange_rate
            exchange_text = self.font.render(f"Tipo de cambio: 1CRC = ${1/exchange_rate:.4f}", True, BLACK)
            screen.blit(exchange_text, (50, 570))

        # Dibujar espacios de parqueo
        self.space1_p1.draw(screen)
        self.space2_p1.draw(screen)
        self.space1_p2.draw(screen)
        self.space2_p2.draw(screen)

        # Dibujar panel de estadísticas
        self.draw_stats(screen, wifi_comm)  # Cambiado

    def update_state(self, wifi_comm):  # Cambiado
        # Actualizar displays con datos de cada parqueo
        parking1 = wifi_comm.get_parking_system(1)  # Cambiado
        parking2 = wifi_comm.get_parking_system(2)  # Cambiado

        if parking1:
            self.display1.update(parking1.display_value, parking1.display_mode)
            self.space1_p1.occupied = parking1.occupied_spaces >= 1
            self.space2_p1.occupied = parking1.occupied_spaces >= 2

        if parking2:
            self.display2.update(parking2.display_value, parking2.display_mode)
            self.space1_p2.occupied = parking2.occupied_spaces >= 1
            self.space2_p2.occupied = parking2.occupied_spaces >= 2

        # Actualizar botones (hover)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons.values():
            button.update(mouse_pos)

    def draw_stats(self, screen, wifi_comm):  # Cambiado
        # Fondo del panel
        pygame.draw.rect(screen, LIGHT_GRAY, self.stats_panel_rect, border_radius=10)
        pygame.draw.rect(screen, GRAY, self.stats_panel_rect, 2, border_radius=10)

        # Título del panel
        stats_title = self.title_font.render("Estadísticas", True, BLACK)
        screen.blit(stats_title, (self.stats_panel_rect.centerx - stats_title.get_width() // 2, 
                                  self.stats_panel_rect.y + 10))

        # Obtener estadísticas de ambos parqueos
        parking1 = wifi_comm.get_parking_system(1)  # Cambiado
        parking2 = wifi_comm.get_parking_system(2)  # Cambiado

        if not parking1 or not parking2:
            return

        # Obtener estadísticas
        stats1 = parking1.get_stats()
        stats2 = parking2.get_stats()

        # Calcular totales combinados
        total_vehicles = stats1['total_vehicles'] + stats2['total_vehicles']
        total_profits_colons = stats1['profits_colons'] + stats2['profits_colons']
        total_profits_dollars = stats1['profits_dollars'] + stats2['profits_dollars']

        # Calcular promedio combinado (ponderado)
        if total_vehicles > 0:
            avg_stance = (stats1['average_stance'] * stats1['total_vehicles'] + 
                          stats2['average_stance'] * stats2['total_vehicles']) / total_vehicles
        else:
            avg_stance = 0

        # Dibujar estadísticas
        y_pos = self.stats_panel_rect.y + 60
        line_height = 40

        stats_text = [
            f"Vehículos totales: {total_vehicles}",
            f"Estancia promedio: {avg_stance:.1f} seg",
            f"Ganancias totales: {total_profits_colons:,} CRC",
            f"Ganancias totales: {total_profits_dollars:.2f} USD",
            f"Parqueo 1 conectado: {'Sí' if wifi_comm.get_connection_status(1) else 'No'}",
            f"Parqueo 2 conectado: {'Sí' if wifi_comm.get_connection_status(2) else 'No'}"
        ]
        
        for text in stats_text:
            surf_text = self.small_font.render(text, True, BLACK)
            screen.blit(surf_text, (self.stats_panel_rect.x + 20, y_pos))
            y_pos += line_height - 20

    def handle_click(self, mouse_pos, wifi_comm):  # Cambiado
        # Verificar botones de control
        parking1 = wifi_comm.get_parking_system(1)  # Cambiado
        parking2 = wifi_comm.get_parking_system(2)  # Cambiado

        if not parking1 or not parking2:
            return

        # Botón de entrada Parqueo 1
        if self.buttons['enter1'].check_click(mouse_pos, True):
            vehicle_id, space = parking1.enter_vehicle()
            if vehicle_id:
                print(f"Parqueo 1: Vehículo {vehicle_id} entró al espacio {space}")
                wifi_comm.control_barrier(1, "open")  # Cambiado
                wifi_comm.update_display(1, parking1.available_space, 'spaces')  # Cambiado

        # Botón de salida Parqueo 1
        elif self.buttons['exit1'].check_click(mouse_pos, True):
            if parking1.pending_payment_vehicles:
                if parking1.confirm_exit():
                    print("Parqueo 1: Vehículo salió")
                    wifi_comm.control_barrier(1, "open")  # Cambiado
                    wifi_comm.update_display(1, parking1.available_space, 'spaces')  # Cambiado
            else:
                vehicle_id, fee = parking1.request_exit()
                if vehicle_id:
                    print(f"Parqueo 1: Vehículo {vehicle_id} - Costo: {fee}CRC")
                    wifi_comm.update_display(1, fee // 1000, 'fee')  # Cambiado

        # Botón de entrada Parqueo 2
        elif self.buttons['enter2'].check_click(mouse_pos, True):
            vehicle_id, space = parking2.enter_vehicle()
            if vehicle_id:
                print(f"Parqueo 2: Vehículo {vehicle_id} entró al espacio {space}")
                wifi_comm.control_barrier(2, "open")  # Cambiado
                wifi_comm.update_display(2, parking2.available_space, 'spaces')  # Cambiado

        # Botón de salida Parqueo 2
        elif self.buttons['exit2'].check_click(mouse_pos, True):
            if parking2.pending_payment_vehicles:
                if parking2.confirm_exit():
                    print("Parqueo 2: Vehículo salió")
                    wifi_comm.control_barrier(2, "open")  # Cambiado
                    wifi_comm.update_display(2, parking2.available_space, 'spaces')  # Cambiado
            else:
                vehicle_id, fee = parking2.request_exit()
                if vehicle_id:
                    print(f"Parqueo 2: Vehículo {vehicle_id} - Costo {fee} CRC")
                    wifi_comm.update_display(2, fee // 1000, 'fee')  # Cambiado

        # Control de barreras
        elif self.buttons['close_boom_barrier'].check_click(mouse_pos, True):
            wifi_comm.control_barrier(1, "closed")  # Cambiado
            wifi_comm.control_barrier(2, "closed")  # Cambiado

        # Actualizar tipo de cambio
        elif self.buttons['update_exchange'].check_click(mouse_pos, True):
            parking1.update_exchange_rate()
            parking2.exchange_rate = parking1.exchange_rate  # Sincronizar
            parking2.last_exchange_update = parking1.last_exchange_update
            print("Tipo de cambio actualizado para ambos parqueos")

        # Reconectar WiFi
        elif self.buttons['reconnect_wifi'].check_click(mouse_pos, True):
            print("🔄 Reiniciando conexión WiFi...")
            wifi_comm.stop()
            time.sleep(1)
            init_wifi_communication()

        # Control manual de espacios Parqueo 1
        space1_action = self.space1_p1.check_click(mouse_pos)
        if space1_action == "occupy":
            parking1.take_manual_space(1)
            wifi_comm.control_led(1, 1, False)  # LED apagado = ocupado
            wifi_comm.update_display(1, parking1.available_space, 'spaces')  # Cambiado
        elif space1_action == "release":
            parking1.release_manual_space(1)
            wifi_comm.control_led(1, 1, True)  # LED encendido = disponible
            wifi_comm.update_display(1, parking1.available_space, 'spaces')  # Cambiado

        space2_action = self.space2_p1.check_click(mouse_pos)
        if space2_action == "occupy":
            parking1.take_manual_space(2)
            wifi_comm.control_led(1, 2, False)
            wifi_comm.update_display(1, parking1.available_space, 'spaces')  # Cambiado
        elif space2_action == "release":
            parking1.release_manual_space(2)
            wifi_comm.control_led(1, 2, True)
            wifi_comm.update_display(1, parking1.available_space, 'spaces')  # Cambiado

        # Control manual de espacios Parqueo 2
        space1_action_p2 = self.space1_p2.check_click(mouse_pos)
        if space1_action_p2 == "occupy":
            parking2.take_manual_space(1)
            wifi_comm.control_led(2, 1, False)
            wifi_comm.update_display(2, parking2.available_space, 'spaces')  # Cambiado
        elif space1_action_p2 == "release":
            parking2.release_manual_space(1)
            wifi_comm.control_led(2, 1, True)
            wifi_comm.update_display(2, parking2.available_space, 'spaces')  # Cambiado

        space2_action_p2 = self.space2_p2.check_click(mouse_pos)
        if space2_action_p2 == "occupy":
            parking2.take_manual_space(2)
            wifi_comm.control_led(2, 2, False)
            wifi_comm.update_display(2, parking2.available_space, 'spaces')  # Cambiado
        elif space2_action_p2 == "release":
            parking2.release_manual_space(2)
            wifi_comm.control_led(2, 2, True)
            wifi_comm.update_display(2, parking2.available_space, 'spaces')  # Cambiado