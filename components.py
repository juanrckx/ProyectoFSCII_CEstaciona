import pygame
from utils import *

class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=HOVER_COLOR):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.actual_color = color
        self.clicked = False
        self.font = pygame.font.SysFont("Arial", 20)

    def draw(self, screen):
        #Dibujar rectangulo del boton
        pygame.draw.rect(screen, self.actual_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, DARK, self.rect, 2, border_radius=8)

        #Dibujar texto
        surf_text = self.font.render(self.text, True, WHITE)
        text_rect = surf_text.get_rect(center=self.rect.center)
        screen.blit(surf_text, text_rect)

    def update(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.actual_color = self.hover_color
            return True
        else:
            self.actual_color = self.color
            return False

    def check_click(self, mouse_pos, click_event):
        if self.rect.collidepoint(mouse_pos) and click_event:
            self.clicked = True
            return True

        return False

class Display7Segment:
    def __init__(self, x, y, size=100):
        self.x = x
        self.y = y
        self.size = size
        self.value = "2"
        self.mode = "Espacios disponibles"
        self.num_font = pygame.font.SysFont("Arial", size, bold=True)
        self.mode_font = pygame.font.SysFont("Arial", 20)

    def draw(self, screen):
        #Fondo del display
        rect_display = pygame.Rect(self.x, self.y, self.size * 1.5, self.size + 40)
        pygame.draw.rect(screen, BLACK, rect_display, border_radius=10)
        pygame.draw.rect(screen, DARK, rect_display, 2, border_radius=10)

        #Dibujar numeros
        num_text = self.num_font.render(self.value, True, RED)
        num_rect = num_text.get_rect(center=(self.x + self.size * 0.75, self.y + self.size // 2))
        screen.blit(num_text, num_rect)

        #Dibujar modo
        mode_text = self.mode_font.render(self.mode, True, WHITE)
        mode_rect = mode_text.get_rect(center=(self.x + self.size * 0.75, self.y + self.size + 20))
        screen.blit(mode_text, mode_rect)

    def update(self, value, mode="spaces"):
        self.value = str(value)
        if mode == "spaces":
            self.mode = "Espacios disponibles"
        else:
            self.mode = "Costo (₡1000)"

class ParkingSite:
    def __init__(self, x, y, num):
        self.x = x
        self.y = y
        self.num = num
        self.occupied = False
        self.rect = pygame.Rect(x, y, 200, 100)
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

    def draw(self, screen):
        #Dibujar rectangulo del parking site
        color = RED if self.occupied else GREEN
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, DARK, self.rect, 2, border_radius=10)

        #Dibujar LED de estado
        pygame.draw.circle(screen, color, (self.x + 180, self.y + 20), 10)
        pygame.draw.circle(screen, DARK, (self.x + 180, self.y + 25), 10, 2)

        #Dibujar texto
        text_state = "Ocupado" if self.occupied else "Disponible"
        text_state = self.font.render(f"Espacio {self.num}: {text_state}", True, BLACK)
        screen.blit(text_state, (self.x + 10, self.y + 40))

        #Botones de control manual
        occupy_button = pygame.Rect(self.x + 10, self.y + 70, 80, 25)
        release_button = pygame.Rect(self.x + 100, self.y + 70, 80, 25)

        pygame.draw.rect(screen, LIGHT_GRAY, occupy_button, border_radius=5)
        pygame.draw.rect(screen, LIGHT_GRAY, release_button, border_radius=5)

        button_font = pygame.font.SysFont("Arial", 14)
        occupy_text = button_font.render("Ocupar", True, WHITE)
        release_text = button_font.render("Liberar", True, WHITE)

        screen.blit(occupy_text, (occupy_button.centerx - occupy_text.get_width() //
                                  2, occupy_button.centery - occupy_text.get_height() // 2))

        screen.blit(release_text, (release_button.centerx - release_text.get_width() //
                                  2, release_button.centery - release_text.get_height() // 2))

        return occupy_button, release_button

    def check_click(self, mouse_pos):
        occupy_button, release_button = pygame.Rect(self.x + 10, self.y + 70, 80, 25), pygame.Rect(self.x + 100, self.y + 70, 80, 25)

        if occupy_button.collidepoint(mouse_pos):
            return "occupy"
        elif release_button.collidepoint(mouse_pos):
            return "release"

        return None
