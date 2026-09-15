import tkinter as tk
 
WIDTH = 800
HEIGHT = 600
TANK_SIZE = 40
SPEED = 5          # Pixel pro Frame
FPS = 60
DELAY = int(1000 / FPS)
 
root = tk.Tk()
root.title("Panzer Bewegung - Demo")
 
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="darkgreen")
canvas.pack()
 
# Panzer als einfaches blaues Rechteck (Platzhalter, bis echte Assets eingebaut sind)
tank = canvas.create_rectangle(
    WIDTH // 2 - TANK_SIZE // 2,
    HEIGHT // 2 - TANK_SIZE // 2,
    WIDTH // 2 + TANK_SIZE // 2,
    HEIGHT // 2 + TANK_SIZE // 2,
    fill="blue",
)
 
# Menge aller aktuell gedrueckten Tasten
keys_pressed = set()
 
 
def on_key_down(event):
    keys_pressed.add(event.keysym.lower())
 
 
def on_key_up(event):
    keys_pressed.discard(event.keysym.lower())
 
 
root.bind("<KeyPress>", on_key_down)
root.bind("<KeyRelease>", on_key_up)
 
 
def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))
 
 
def game_loop():
    dx = 0
    dy = 0
    if "w" in keys_pressed:
        dy -= SPEED
    if "s" in keys_pressed:
        dy += SPEED
    if "a" in keys_pressed:
        dx -= SPEED
    if "d" in keys_pressed:
        dx += SPEED
 
    if dx != 0 or dy != 0:
        x1, y1, x2, y2 = canvas.coords(tank)
 
        # Bildschirmgrenzen: Panzer darf nicht rausfahren
        new_x1 = clamp(x1 + dx, 0, WIDTH - TANK_SIZE)
        new_y1 = clamp(y1 + dy, 0, HEIGHT - TANK_SIZE)
 
        actual_dx = new_x1 - x1
        actual_dy = new_y1 - y1
        canvas.move(tank, actual_dx, actual_dy)
 
    root.after(DELAY, game_loop)
 
 
game_loop()
root.mainloop()