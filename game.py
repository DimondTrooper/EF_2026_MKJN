from tkinter import*
from PIL import Image, ImageTk

root = Tk()
root.state('zoomed')     
root.update_idletasks() 
WIDTH = root.winfo_width()     
HEIGHT = root.winfo_height() 
SPEED = 5          # Pixel pro Frame
FPS = 60
DELAY = int(1000 / FPS)
root.title("Panzer Bewegung - Demo")

canvas = Canvas(root, width=WIDTH, height=HEIGHT, bg="darkgreen")
canvas.pack()

pil_img = Image.open("Assets/Tank_Red_Forward.png") 
pil_img.thumbnail((50,50)) 
tank_img = ImageTk.PhotoImage(pil_img) 
TANK_WIDTH = tank_img.width()
TANK_HEIGHT = tank_img.height()

tank = canvas.create_image(
    WIDTH // 2,
    HEIGHT // 2,
    image=tank_img,
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
        x, y = canvas.coords(tank)

        half_w = TANK_WIDTH // 2
        half_h = TANK_HEIGHT // 2
        new_x = clamp(x + dx, half_w, WIDTH - half_w)
        new_y = clamp(y + dy, half_h, HEIGHT - half_h)
        actual_dx = new_x - x
        actual_dy = new_y - y
        canvas.move(tank, actual_dx, actual_dy)

    root.after(DELAY, game_loop)


game_loop()
root.mainloop()