import pygame
import sys
import time
from gui import ParkingGUI
from utils import *
from serial_com import *

def main():
    # Inicializar PyGame primero
    pygame.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CEstaciona - Sistema de Parqueo Inteligente")
    
    # Inicializar comunicación serial EN UN HILO SEPARADO
    ports = ['COM7', 'COM8']
    print("🔗 Iniciando comunicación serial...")
    
    # Inicializar pero no bloquear si hay error
    try:
        if not init_serial_communication(ports):
            print("⚠️ No se pudo conectar al hardware, continuando en modo simulación")
    except Exception as e:
        print(f"⚠️ Error de conexión: {e}. Continuando sin hardware")
    
    gui = ParkingGUI(WIDTH, HEIGHT)
    clock = pygame.time.Clock()
    
    # Variables para control de actualización
    last_display_update = 0
    display_update_interval = 0.5  # Actualizar displays cada 0.5 segundos (no cada frame!)
    
    running = True
    while running:
        current_time = time.time()
        
        # 1. Procesar eventos de PyGame (CRÍTICO: esto debe ser rápido)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                gui.handle_click(event.pos, serial_comm)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:  # Tecla R para reconectar
                    print("🔄 Reconectando...")
                    serial_comm.disconnect()
                    time.sleep(1)
                    init_serial_communication(ports)
        
        # 2. Actualizar displays SOLO periódicamente (no en cada frame)
        if current_time - last_display_update > display_update_interval:
            for parking_id in [1, 2]:
                parking_system = serial_comm.get_parking_system(parking_id)
                if parking_system and parking_id in serial_comm.serial_conns:
                    try:
                        serial_comm.update_display(parking_id, 
                                                 parking_system.display_value,
                                                 parking_system.display_mode)
                    except Exception as e:
                        print(f"⚠️ Error actualizando display {parking_id}: {e}")
            last_display_update = current_time
        
        # 3. Dibujar interfaz
        screen.fill(GRAY)
        gui.draw(screen, serial_comm)
        
        # 4. Mostrar estado de conexión
        font = pygame.font.SysFont("dejavusans", 18)
        status_y = HEIGHT - 60
        
        for parking_id in [1, 2]:
            status = "✅ Conectado" if parking_id in serial_comm.serial_conns else "❌ Desconectado"
            text = font.render(f"Parqueo {parking_id}: {status}", True, BLACK)
            screen.blit(text, (10, status_y))
            status_y += 30
        
        pygame.display.update()
        clock.tick(FPS)  # Limitar a 60 FPS
    
    # Guardar datos al salir
    print("💾 Guardando datos...")
    for parking_id in [1, 2]:
        parking_system = serial_comm.get_parking_system(parking_id)
        if parking_system:
            try:
                parking_system.save_data()
            except Exception as e:
                print(f"Error guardando datos parqueo {parking_id}: {e}")
    
    serial_comm.disconnect()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()