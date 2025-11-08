import sys
from parking import *
from gui import *
from utils import *



def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CEstaciona - Sistema de Parqueo Inteligente")

    parking_system = ParkingSystem()
    gui = ParkingGUI(WIDTH, HEIGHT)

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                gui.handle_click(event.pos, parking_system)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        parking_system.update()

        screen.fill(GRAY)
        gui.draw(screen, parking_system)

        pygame.display.update()
        clock.tick(FPS)

    parking_system.save_data()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()