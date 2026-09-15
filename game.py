import time
from tkinter import Canvas
from build_tank_images import get_tank_images
 
SPEED = 1.5
FPS = 60
DELAY = int(1000 / FPS)
 
# alle wie viele Frames ein ANGLE_STEP weitergedreht wird
ROTATE_STEP_EVERY = 4
 
SHOOT_COOLDOWN = 4     # Sekunden zwischen Schuessen
PROJECTILE_SPEED = 8
PROJECTILE_RADIUS = 4
BARREL_OFFSET = 20     # Kugel startet so viele Pixel vor dem Panzer-Zentrum
 
# ANGLE_STEPS muss der Reihenfolge im Kreis entsprechen (fuer next_step_towards)
ANGLE_STEPS = [0, 45, 90, 135, 180, 225, 270, 315]
 
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
ANGLE_TO_VECTOR = {
    0:   (0, -1),   # oben
    45:  (-1, -1),  # oben-links
    90:  (-1, 0),   # links
    135: (-1, 1),   # unten-links
    180: (0, 1),    # unten
    225: (1, 1),    # unten-rechts
    270: (1, 0),    # rechts
    315: (1, -1),   # oben-rechts
}
 
# Tastenbelegung pro Spieler -- muss zu controls_screen() in menu.py passen
PLAYER_KEYS = {
    1: {"up": "w", "down": "s", "left": "a", "right": "d", "shoot": "e"},
    2: {"up": "up", "down": "down", "left": "left", "right": "right", "shoot": "Control_R"},
}
 
 
# -- Auf Modul-Ebene, damit unittest sie direkt importieren/testen kann.
 
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
 
 
def create_player(root, canvas, keys, tank_images, start_x, start_y):

    tank = canvas.create_image(start_x, start_y, image=tank_images[0])
 
    player = {
        "tank": tank,
        "tank_images": tank_images,
        "tank_width": tank_images[0].width(),
        "tank_height": tank_images[0].height(),
        "keys": keys,
        "state": {
            "angle": 0,
            "target_angle": 0,
            "frame_counter": 0,
            "last_shot_time": 0,
        },
        "projectiles": [],
    }
 
    def on_shoot(event):
        state = player["state"]
        now = time.time()
        if now - state["last_shot_time"] < SHOOT_COOLDOWN:
            return  # noch in Abklingzeit
        state["last_shot_time"] = now
 
        x, y = canvas.coords(tank)
        dx, dy = ANGLE_TO_VECTOR[state["angle"]]
        start_bx = x + dx * BARREL_OFFSET
        start_by = y + dy * BARREL_OFFSET
        bullet = canvas.create_oval(
            start_bx - PROJECTILE_RADIUS, start_by - PROJECTILE_RADIUS,
            start_bx + PROJECTILE_RADIUS, start_by + PROJECTILE_RADIUS,
            fill="black",
        )
        player["projectiles"].append({"id": bullet, "dx": dx, "dy": dy})
 
    root.bind(f"<KeyPress-{keys['shoot']}>", on_shoot)
 
    return player
 
 
def update_player(canvas, player, keys_pressed, width, height):
    """Ein Frame Logik fuer GENAU EINEN Spieler: Drehen, Bewegen, Projektile."""
    keys = player["keys"]
    state = player["state"]
 
    # 1. Tasten dieses Spielers auslesen
    up = keys["up"] in keys_pressed
    down = keys["down"] in keys_pressed
    left = keys["left"] in keys_pressed
    right = keys["right"] in keys_pressed
 
    # 2. Bewegung berechnen
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
            canvas.itemconfig(player["tank"], image=player["tank_images"][state["angle"]])
            player["tank_width"] = player["tank_images"][state["angle"]].width()
            player["tank_height"] = player["tank_images"][state["angle"]].height()
 
    if dx != 0 or dy != 0:
        x, y = canvas.coords(player["tank"])
        half_w = player["tank_width"] // 2
        half_h = player["tank_height"] // 2
        new_x = clamp(x + dx, half_w, width - half_w)
        new_y = clamp(y + dy, half_h, height - half_h)
        canvas.move(player["tank"], new_x - x, new_y - y)
 
    for p in player["projectiles"][:]:
        canvas.move(p["id"], p["dx"] * PROJECTILE_SPEED, p["dy"] * PROJECTILE_SPEED)
        x1, y1, x2, y2 = canvas.coords(p["id"])
        if x2 < 0 or x1 > width or y2 < 0 or y1 > height:
            canvas.delete(p["id"])
            player["projectiles"].remove(p)
 
 
def run_game(root, mode):
    # altes Frame (Controls-Screen) weg
    for widget in root.winfo_children():
        widget.destroy()
 
    WIDTH = root.winfo_width()
    HEIGHT = root.winfo_height()
 
    canvas = Canvas(root, width=WIDTH, height=HEIGHT, bg="darkgreen")
    canvas.pack()

    tank_images = get_tank_images()
 
    players = [
        create_player(root, canvas, PLAYER_KEYS[1], tank_images, WIDTH // 3, HEIGHT // 2),
        create_player(root, canvas, PLAYER_KEYS[2], tank_images, WIDTH * 2 // 3, HEIGHT // 2),
    ]
    if mode == "1 vs 1 vs 1":
        players.append(
            create_player(root, canvas, PLAYER_KEYS[3], tank_images, WIDTH // 2, HEIGHT // 4)
        )
 
    keys_pressed = set()
 
    def on_key_down(event):
        keys_pressed.add(event.keysym.lower())
 
    def on_key_up(event):
        keys_pressed.discard(event.keysym.lower())
 
    root.bind("<KeyPress>", on_key_down)
    root.bind("<KeyRelease>", on_key_up)
 
    def game_loop():
        for player in players:
            update_player(canvas, player, keys_pressed, WIDTH, HEIGHT)
 
        root.after(DELAY, game_loop)
 
    game_loop()
 