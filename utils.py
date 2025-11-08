WIDTH, HEIGHT = 1200, 800
FPS = 60
BLACK,BLUE, HOVER_COLOR, DARK, WHITE, RED, GREEN, GRAY, LIGHT_GRAY = (0, 0, 0), (70, 130, 180), (100, 160, 210), (50, 50, 50), (255, 255, 255), (255, 0, 0), (100, 255, 100), (240, 240, 240), (200, 200, 200)

def reset_time(seg):
    minutes = int(seg // 60)
    segs = int(seg % 60)
    return f"{minutes:02d}:{segs:02d}"

def reset_change(fee):
    return f"₡{fee:,.0f}"