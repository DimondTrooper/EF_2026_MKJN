from tkinter import Canvas
from PIL import Image, ImageTk
from build_tank_images import get_tank_images

BACKGROUND_PATH = "Assets/Map_Hintergrund.png"

SPEED = 1
FPS = 60
DELAY = int(1000 / FPS)
# ANGLE_STEPS muss der Reihenfolge im Kreis entsprechen (fuer next_step_towards)
ROTATE_STEP_EVERY = 10
 
# ANGLE_STEPS muss der Reihenfolge im Kreis entsprechen (fuer next_step_towards)
ANGLE_STEPS = [0, 45, 90, 135, 180, 225, 270, 315]

state = {
    "angle": 0,
    "target_angle": 0,
    "frame_counter": 0,
}
 
DIRECTION_TO_ANGLE = {
    (True, False, False, False): 0,    # nur oben
    (True, False, False, True): 315,   # oben + rechts
    (False, False, False, True): 270,  # nur rechts
    (False, True, False, True): 225,   # unten + rechts
    (False, True, False, False): 180,  # nur unten
    (False, True, True, False): 135,   # unten + links
    (False, False, True, False): 90,   # nur links
    (True, False, True, False): 45,    # oben + links
}
 
 
# -- Auf Modul-Ebene, damit unittest sie direkt importieren/testen kann,
#    ohne ein ganzes Tk-Fenster + Canvas + Game-Loop aufzuziehen.
 
def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))
 
 
def next_step_towards(current, target):
    """Naechster Winkel aus ANGLE_STEPS auf dem kuerzesten Weg zu target."""
    if current == target:
        return current
    i_current = ANGLE_STEPS.index(current)
    i_target = ANGLE_STEPS.index(target)
    n = len(ANGLE_STEPS)
    forward_dist = (i_target - i_current) % n
    backward_dist = (i_current - i_target) % n
    if forward_dist <= backward_dist:
        return ANGLE_STEPS[(i_current + 1) % n]
    return ANGLE_STEPS[(i_current - 1) % n]
 
 
def run_game(root, mode):
    # altes Frame (Controls-Screen) weg
    for widget in root.winfo_children():
        widget.destroy()
 
    WIDTH = root.winfo_width()
    HEIGHT = root.winfo_height()
 
    canvas = Canvas(root, width=WIDTH, height=HEIGHT, bg="darkgreen")
    canvas.pack()

    background_image = Image.open(BACKGROUND_PATH).resize((WIDTH, HEIGHT))
    background_photo = ImageTk.PhotoImage(background_image)
    canvas.background_photo = background_photo  # Referenz halten, sonst Garbage Collection
    canvas.create_image(0, 0, anchor="nw", image=background_photo)

    tank_images = get_tank_images()

    tank = canvas.create_image(WIDTH // 2, HEIGHT // 2, image=tank_images[0])
    tank_width = tank_images[0].width()
    tank_height = tank_images[0].height()
 
    state = {
        "angle": 0,
        "target_angle": 0,
        "frame_counter": 0,
    }
 
    keys_pressed = set()
 
    def on_key_down(event):
        keys_pressed.add(event.keysym.lower())
 
    def on_key_up(event):
        keys_pressed.discard(event.keysym.lower())
 
    root.bind("<KeyPress>", on_key_down)
    root.bind("<KeyRelease>", on_key_up)
 
    def game_loop():
        nonlocal tank_width, tank_height

        up = "w" in keys_pressed
        down = "s" in keys_pressed
        left = "a" in keys_pressed
        right = "d" in keys_pressed
 
     
        dx = dy = 0
        if up:
            dy -= SPEED
        if down:
            dy += SPEED
        if left:
            dx -= SPEED
        if right:
            dx += SPEED
 
        key = (up, down, left, right)
        if key in DIRECTION_TO_ANGLE:
            state["target_angle"] = DIRECTION_TO_ANGLE[key]

        if state["angle"] != state["target_angle"]:
                state["frame_counter"] += 1
                if state["frame_counter"] >= ROTATE_STEP_EVERY:
                    state["frame_counter"] = 0
                    state["angle"] = next_step_towards(state["angle"], state["target_angle"])
                    canvas.itemconfig(tank, image=tank_images[state["angle"]])
                    tank_width = tank_images[state["angle"]].width()
                    tank_height = tank_images[state["angle"]].height()
 
        if dx != 0 or dy != 0:
            x, y = canvas.coords(tank)
            half_w = tank_width // 2
            half_h = tank_height // 2
            new_x = clamp(x + dx, half_w, WIDTH - half_w)
            new_y = clamp(y + dy, half_h, HEIGHT - half_h)
            canvas.move(tank, new_x - x, new_y - y)
 
        root.after(DELAY, game_loop)
 
    game_loop()