import pygame
from components import *

class ParkingGUI:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)

        self.create_components()

    def create_components(self):
        #Display 7 segmentos
        self.display = Display7Segment(50, 50, 80)

        #Botones
        self.buttons = {
            'enter': Button(50, 200, 150, 50, "Entrar Vehiculo"),
            'exit': Button(50, 270, 150, 50, "Pagar/Salir"),
            'open_boom_barrier': Button(50, 340, 150, 50, "Abrir aguja"),
            'close_boom_barrier': Button(50, 410, 150, 50, "Cerrar aguja")
        }
        #Espacios de parqueo
        self.space1 = ParkingSite(300, 100, 1)
        self.space2 = ParkingSite(300, 250, 2)

        #Panel de estadisticas
        self.stats_panel_rect = pygame.Rect(600, 100, 500, 300)

    def draw(self, screen, system):
        #Actualizar componentes
        self.update_state(system)

        #Dibujar titulo
        title = self.title_font.render("CEstaciona - Parqueo Inteligente", True, BLACK)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 20))

        #Dibujar display
        self.display.draw(screen)

        #Dibujar botones
        for button in self.buttons.values():
            button.draw(screen)

        #Dibujar estado de la aguja
        if system.boom_barrier_state == "closed":
            barrier_text = "Aguja cerrada"
        else:
            barrier_text = "Aguja abierta"

        barrier_surface = self.font.render(f"Estado aguja: {barrier_text}", True, BLACK)
        screen.blit(barrier_surface, (50, 480))

        #Dibujar espacios de parqueo
        self.space1.draw(screen)
        self.space2.draw(screen)

        #Dibujar panel de estadisticas
        self.draw_stats(screen, system)

        #Dibujar informacion de vehiculos
        self.draw_actual_vehicles(screen, system)


    def update_state(self, system):
        #Actualizar display
        self.display.update(system.display_value, system.display_mode)

        #Actualizar estados de espacios
        self.space1.occupied = system.occupied_spaces >= 1
        self.space2.occupied = system.occupied_spaces >= 2

        #Actualizar botones (hover)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons.values():
            button.update(mouse_pos)

    def draw_stats(self, screen, system):
        #Fondo del panel
        pygame.draw.rect(screen, LIGHT_GRAY, self.stats_panel_rect, border_radius=10)
        pygame.draw.rect(screen, GRAY, self.stats_panel_rect, 2, border_radius=10)

        #Titulo del panel
        stats_title = self.title_font.render("Estadisticas", True, BLACK)
        screen.blit(stats_title, (self.stats_panel_rect.centerx - stats_title.get_width() // 2, self.stats_panel_rect.y + 10))

        #Obtener estadisticas
        stats = system.get_stats()

        #Dibujar estadisticas
        y_pos = self.stats_panel_rect.y + 60
        for key, value in stats.items():
            if key == 'total_vehicles':
                text = f"Vehiculos totales: {int(value)}"
            elif key == 'average_stance':
                text = f"Estancia promedio: {value:.1f} seg"
            elif key == 'profits_colons':
                text = f"Ganancias: ₡{int(value):,}"
            elif key == 'profits_dollars':
                text = f"Ganancias: ${value:.2f} USD"
            else:
                continue

            surf_text = self.font.render(text, True, BLACK)
            screen.blit(surf_text, (self.stats_panel_rect.x + 20, y_pos))
            y_pos += 40

    def draw_actual_vehicles(self, screen, system):
        #Panel de vehiculos actuales
        vehicles_rect = pygame.Rect(600, 400, 500, 200)
        pygame.draw.rect(screen, LIGHT_GRAY, vehicles_rect, border_radius=10)
        pygame.draw.rect(screen, GRAY, vehicles_rect, 2, border_radius=10)

        #Titulo
        title = self.font.render("Vehiculos Estacionados", True, BLACK)
        screen.blit(title, (vehicles_rect.centerx - title.get_width() // 2 - 150, self.stats_panel_rect.y - 35))

        #Lista de vehiculos
        if system.parked_vehicles:
            y_pos = vehicles_rect.y + 50
            for veh_id, data in system.parked_vehicles.items():
                actual_time = pygame.time.get_ticks() // 1000
                veh_text = f"{veh_id} - Espacio {data['space']} - Entrada: {data['entry_time_str']}"

                surf_text = self.font.render(veh_text, True, BLACK)
                screen.blit(surf_text, (self.stats_panel_rect.x + 20, y_pos))
                y_pos += 30
        else:
            empty_text = self.font.render("No hay vehiculos estacionados", True, GRAY)
            screen.blit(empty_text, (vehicles_rect.centerx - empty_text.get_width() // 2, vehicles_rect.centery - empty_text.get_height() // 2))


    def handle_click(self, mouse_pos, system):
        #Verificar botones de control
        if self.buttons['enter'].check_click(mouse_pos, True):
            vehicle_id, space = system.enter_vehicle()
            if vehicle_id:
                print(f"Vehiculo {vehicle_id} entro al espacio {space}")

        elif self.buttons['exit'].check_click(mouse_pos, True):
            if system.pending_payment_vehicles:
                #Segunda pulsacion: confirmar salida
                if system.confirm_exit():
                    print("Vehiculo salio del parqueo")

            else:
                #Primera pulsacion: mostrar costo
                vehicle_id, fee = system.request_exit()
                if vehicle_id:
                    print(f"Vehiculo {vehicle_id} - Costo: ₡{fee}")

        elif self.buttons['open_boom_barrier'].check_click(mouse_pos, True):
            system.control_boom_barrier("Aguja abierta")

        elif self.buttons['close_boom_barrier'].check_click(mouse_pos, True):
            system.control_boom_barrier("Aguja cerrada")

        #Verificar controles manuales de espacios
        space1_action = self.space1.check_click(mouse_pos)
        if space1_action == "occupy":
            system.take_manual_space(1)
        elif space1_action == "release":
            system.release_manual_space(1)

        space2_action = self.space2.check_click(mouse_pos)
        if space2_action == "occupy":
            system.take_manual_space(2)
        elif space2_action == "release":
            system.release_manual_space(2)