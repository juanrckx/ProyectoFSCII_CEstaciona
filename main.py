import pygame
import sys
from parking import ParkingSystem
from gui import ParkingGUI
from utils import *
from serial_com import *
<<<<<<< HEAD

<<<<<<< HEAD
=======

=======
>>>>>>> origin/main

>>>>>>> Juan_MAC
def main():
    #Inicializar comunicación serial
    ports = ['COM8', 'COM7']
    if not init_serial_communication(ports):
        print("No se pudo conectar al hardware")
        return
<<<<<<< HEAD

=======
<<<<<<< HEAD
    
=======

>>>>>>> origin/main
>>>>>>> Juan_MAC
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CEstaciona - Sistema de Parqueo Inteligente")

    gui = ParkingGUI(WIDTH, HEIGHT)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                gui.handle_click(event.pos, serial_comm)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

<<<<<<< HEAD
        # Actualizar displays de ambos parqueos
=======
<<<<<<< HEAD
>>>>>>> Juan_MAC
        for parking_id in [1, 2]:
            if parking_system:
            parking_system = serial_comm.get_parking_system(parking_id)
                serial_comm.update_display(parking_id, 
                                         parking_system.display_value,
                                         parking_system.display_mode)

=======
        # Actualizar displays de ambos parqueos
        for parking_id in [1, 2]:
            parking_system = serial_comm.get_parking_system(parking_id)
            if parking_system:
                serial_comm.update_display(parking_id, 
                                         parking_system.display_value,
                                         parking_system.display_mode)
>>>>>>> origin/main

        screen.fill(GRAY)
        gui.draw(screen, serial_comm)

        pygame.display.update()
        clock.tick(FPS)

<<<<<<< HEAD
    # Guardar datos de ambos parqueos
=======
<<<<<<< HEAD
    #Guardar datos de ambos parqueos
=======
    # Guardar datos de ambos parqueos
>>>>>>> origin/main
>>>>>>> Juan_MAC
    for parking_id in [1, 2]:
        parking_system = serial_comm.get_parking_system(parking_id)
            parking_system.save_data()
<<<<<<< HEAD
        if parking_system:
            
=======
<<<<<<< HEAD

=======
            
>>>>>>> origin/main
>>>>>>> Juan_MAC
    serial_comm.disconnect()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()