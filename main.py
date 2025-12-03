import pygame
import sys
import time
from wifi_server import *
from gui import ParkingGUI
from utils import *

def main():
    # Inicializar PyGame primero
    pygame.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CEstaciona - Sistema de Parqueo Inteligente")
    
    # Inicializar comunicación serial EN UN HILO SEPARADO
    print("Iniciando comunicación serial...")
    
    # Inicializar pero no bloquear si hay error
    try:
        if not init_wifi_communication():
            print("No se pudo conectar al hardware, continuando en modo simulación")
    except Exception as e:
        print(f"Error de conexión: {e}. Continuando sin hardware")
    
    gui = ParkingGUI(WIDTH, HEIGHT)
    clock = pygame.time.Clock()
    
    # Variables para control de actualización
    last_display_update = 0
    display_update_interval = 1/30

    #Variable para mostrar estado de conexión
    last_connection_check = 0
    connection_check_interval = 2
    
    running = True
    while running:
        current_time = time.time()
        
        # 1. Procesar eventos de PyGame (CRÍTICO: esto debe ser rápido)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                gui.handle_click(event.pos, wifi_comm)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:  # Tecla R para reconectar
                    print("Reconectando...")
                    wifi_comm.stop()
                    time.sleep(1)
                    init_wifi_communication()
        
        # 2. Actualizar displays SOLO periódicamente (no en cada frame)
        if current_time - last_display_update > display_update_interval:
            for parking_id in [1, 2]:
                parking_system = wifi_comm.get_parking_system(parking_id)
                if parking_system and wifi_comm.get_connection_status(parking_id):
                    try:
                        wifi_comm.update_display(parking_id, 
                                                 parking_system.display_value,
                                                 parking_system.display_mode)
                    except Exception as e:
                        print(f"Error actualizando display {parking_id}: {e}")
            last_display_update = current_time
        
        #3. Verificar estado de conexión periódicamente
        if current_time - last_connection_check > connection_check_interval:
            for parking_id in [1, 2]:
                status = "Conectado" if wifi_comm.get_connection_status(parking_id) else "Desconectado"
                print(f"Parqueo {parking_id}: {status}")
            last_connection_check = current_time

        # 4. Dibujar interfaz
        screen.fill(GRAY)
        gui.draw(screen, wifi_comm)
        
        # 5. Mostrar estado de conexión
        font = pygame.font.SysFont("dejavusans", 18)
        status_y = HEIGHT - 60
        
        # Instrucciones
        help_text = font.render("Presiona R para reiniciar conexión, ESC para salir", True, BLACK)
        screen.blit(help_text, (10, HEIGHT - 20))
        
        pygame.display.update()
        clock.tick(FPS)
    
    # Guardar datos al salir
    print("Guardando datos...")
    for parking_id in [1, 2]:
        parking_system = wifi_comm.get_parking_system(parking_id)
        if parking_system:
            try:
                parking_system.save_data()
            except Exception as e:
                print(f"Error guardando datos parqueo {parking_id}: {e}")
    
    # Detener servidores WiFi
    wifi_comm.stop()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()