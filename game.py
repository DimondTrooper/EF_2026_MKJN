from tkinter import Canvas
from PIL import Image, ImageTk
from build_tank_images import get_tank_images
 
SPEED = 3
FPS = 60
DELAY = int(1000 / FPS)

tank_images = get_tank_images()
 
def run_game(root, mode):
    # altes Frame (Controls-Screen) weg
    for widget in root.winfo_children():
        widget.destroy()
 
    WIDTH = root.winfo_width()
    HEIGHT = root.winfo_height()
 
    canvas = Canvas(root, width=WIDTH, height=HEIGHT, bg="darkgreen")
    canvas.pack()
 
    original_pil_img = Image.open("Assets/Tank_Red_Forward.png")
    original_pil_img.thumbnail((50, 50))
    original_pil_img = Image.open("Assets/Tank_Red_Forward.png")
    original_pil_img.thumbnail((50, 50))
 
    rotated_cache = {}
 
    def get_rotated_image(angle):
        if angle not in rotated_cache:
            rotated = original_pil_img.rotate(angle, expand=True)
            rotated_cache[angle] = ImageTk.PhotoImage(rotated)
        return rotated_cache[angle]
 
    state = {
        "angle": 0,
        "tank_img": get_rotated_image(0),
    }
 
    tank = canvas.create_image(WIDTH // 2, HEIGHT // 2, image=state["tank_img"])
    tank_width = state["tank_img"].width()
    tank_height = state["tank_img"].height()
 
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
        nonlocal tank_width, tank_height
 
        dx = dy = 0
        new_angle = state["angle"]
        if "w" in keys_pressed:
            dy -= SPEED
            new_angle = 0
        if "s" in keys_pressed:
            dy += SPEED
            new_angle = 180
        if "a" in keys_pressed:
            dx -= SPEED
            new_angle = 90
        if "d" in keys_pressed:
            dx += SPEED
            new_angle = 270
 
        if dx != 0 or dy != 0:
            x, y = canvas.coords(tank)
            half_w = tank_width // 2
            half_h = tank_height // 2
            new_x = clamp(x + dx, half_w, WIDTH - half_w)
            new_y = clamp(y + dy, half_h, HEIGHT - half_h)
            canvas.move(tank, new_x - x, new_y - y)
 
        root.after(DELAY, game_loop)
 
    game_loop()
 