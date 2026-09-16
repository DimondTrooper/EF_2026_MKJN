import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # keine Begruessungs-Ausgabe im Terminal

import time
import pygame
from tkinter import Canvas
from PIL import Image, ImageTk
from build_tank_images import get_tank_images
import random

BACKGROUND_PATH = "Assets/Map_real.png"
SHOOT_SOUND_PATH = "Sounds/Shoot.wav"
MOVE_SOUND_PATH = "Sounds/Tank_moving.wav"
MOVE_SOUND_FADEOUT_MS = 300  # sanftes Ausklingen statt hartem Stopp

TREE_IMAGE_PATHS = ["Assets/Tree_1.png", "Assets/Tree_2.png"]
TREE_SCALE = 0.8  # 20% kleiner als die Originalgrafik
OBSTACLE_MIN_COUNT = 5
OBSTACLE_MAX_COUNT = 10

pygame.mixer.init()
SHOOT_SOUND = pygame.mixer.Sound(SHOOT_SOUND_PATH)
MOVE_SOUND = pygame.mixer.Sound(MOVE_SOUND_PATH)

SPEED = 1.5
FPS = 60
DELAY = int(1000 / FPS)

# minimale Zeit (Sekunden) zwischen zwei Drehschritten -- unabhaengig davon,
# wie oft/schnell man Tasten drueckt, kann sich der Panzer nicht schneller
# drehen als das hier erlaubt
ROTATE_COOLDOWN = 0.12

SPAWN_MARGIN = 60  # Abstand (Pixel) zum Bildschirmrand, in dem kein Panzer spawnt

# kurze Pause (Sekunden) NACH einer abgeschlossenen Drehung, bevor eine neue
# Drehung angenommen wird -- zusaetzlich zur Regel, dass die aktuelle Drehung
# erst fertig sein muss
ROTATE_RESTART_COOLDOWN = 0.15

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
    3: {"up": "up", "down": "down", "left": "left", "right": "right", "shoot": "Control_L"},
}
 
 
# -- Auf Modul-Ebene, damit unittest sie direkt importieren/testen kann.
 
def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

#Claude code to avoide spawing in trees 
def random_spawn_position(width, height, avoid_boxes=None, half_w=0, half_h=0, max_attempts=50):
    """Zufaellige Position mit Abstand zum Bildschirmrand (SPAWN_MARGIN).
    Ist avoid_boxes gesetzt, wird eine Position gesucht, an der eine Box der
    Groesse (2*half_w, 2*half_h) keine dieser Boxen ueberlappt -- damit z.B.
    Panzer nicht auf einem Baum spawnen."""
    for _ in range(max_attempts):
        x = random.randint(SPAWN_MARGIN, width - SPAWN_MARGIN)
        y = random.randint(SPAWN_MARGIN, height - SPAWN_MARGIN)
        if not avoid_boxes:
            return x, y
        candidate_box = (x - half_w, y - half_h, x + half_w, y + half_h)
        if not any(rects_overlap(candidate_box, box) for box in avoid_boxes):
            return x, y
    return x, y  # kein freier Platz gefunden -- letzte Position notgedrungen nehmen
###


def load_tree_photo(path):
    img = Image.open(path)
    new_size = (round(img.width * TREE_SCALE), round(img.height * TREE_SCALE))
    return ImageTk.PhotoImage(img.resize(new_size))


def spawn_obstacles(canvas, width, height, tree_photos):
    """Platziert die Baeume und gibt sie als Liste von {"id", "box"} zurueck
    (fuer Kollision -- ein von einem Projektil getroffener Baum wird daraus
    entfernt und von der Canvas geloescht)."""
    count = random.randint(OBSTACLE_MIN_COUNT, OBSTACLE_MAX_COUNT)
    obstacles = []
    for _ in range(count):
        x, y = random_spawn_position(width, height)
        photo = random.choice(tree_photos)
        tree_id = canvas.create_image(x, y, image=photo)
        obstacles.append({"id": tree_id, "box": canvas.bbox(tree_id)})
    return obstacles


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

def rects_overlap(a, b):
    """a, b je (x1, y1, x2, y2). True, wenn sich die beiden Rechtecke ueberschneiden."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)
  
def create_player(root, canvas, name, keys, tank_images, start_x, start_y):

    tank = canvas.create_image(start_x, start_y, image=tank_images[0])
 
    player = {
        "tank": tank,
        "name": name,
        "alive": True,
        "moving": False,
        "tank_images": tank_images,
        "tank_width": tank_images[0].width(),
        "tank_height": tank_images[0].height(),
        "keys": keys,
        "state": {
            "angle": 0,
            "target_angle": 0,
            "last_rotate_time": 0,
            "rotation_ready_time": 0,
            "last_shot_time": 0,
        },
        "projectiles": [],
    }
 
    def on_shoot(event):
        if not player["alive"]:
            return # Spieler tot -> keine Schuesse mehr
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
        SHOOT_SOUND.play()

    root.bind(f"<KeyPress-{keys['shoot']}>", on_shoot)
 
    return player
 
 
def update_player(canvas, player, keys_pressed, width, height, obstacles):
    if not player["alive"]:
        player["moving"] = False
        return  # Spieler tot -> keine Updates mehr
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
    now = time.time()
    # neues Ziel nur uebernehmen, wenn die vorherige Drehung fertig ist UND
    # der kurze Cooldown danach abgelaufen ist -- sonst kann man durch
    # schnelles Tastenwechseln Drehungen aneinanderreihen und den Panzer
    # beliebig lange weiterdrehen lassen
    if (
        key in DIRECTION_TO_ANGLE
        and state["angle"] == state["target_angle"]
        and now >= state["rotation_ready_time"]
    ):
        state["target_angle"] = DIRECTION_TO_ANGLE[key]

    if state["angle"] != state["target_angle"]:
        if now - state["last_rotate_time"] >= ROTATE_COOLDOWN:
            state["last_rotate_time"] = now
            state["angle"] = next_step_towards(state["angle"], state["target_angle"])
            canvas.itemconfig(player["tank"], image=player["tank_images"][state["angle"]])
            player["tank_width"] = player["tank_images"][state["angle"]].width()
            player["tank_height"] = player["tank_images"][state["angle"]].height()
            if state["angle"] == state["target_angle"]:
                state["rotation_ready_time"] = now + ROTATE_RESTART_COOLDOWN

    wants_to_move = dx != 0 or dy != 0
    player["moving"] = False

    if wants_to_move:
        x, y = canvas.coords(player["tank"])
        half_w = player["tank_width"] // 2
        half_h = player["tank_height"] // 2
        new_x = clamp(x + dx, half_w, width - half_w)
        new_y = clamp(y + dy, half_h, height - half_h)
        new_box = (new_x - half_w, new_y - half_h, new_x + half_w, new_y + half_h)
        blocked = any(rects_overlap(new_box, tree["box"]) for tree in obstacles)
        if not blocked:
            canvas.move(player["tank"], new_x - x, new_y - y)
            player["moving"] = True

    for p in player["projectiles"][:]:
        canvas.move(p["id"], p["dx"] * PROJECTILE_SPEED, p["dy"] * PROJECTILE_SPEED)
        bullet_box = canvas.coords(p["id"])
        x1, y1, x2, y2 = bullet_box
        hit_tree = next((tree for tree in obstacles if rects_overlap(bullet_box, tree["box"])), None)
        if hit_tree is not None:
            canvas.delete(hit_tree["id"])
            obstacles.remove(hit_tree)
        if x2 < 0 or x1 > width or y2 < 0 or y1 > height or hit_tree is not None:
            canvas.delete(p["id"])
            player["projectiles"].remove(p)


def check_hits(canvas, players):
    """Prueft fuer alle Spieler, ob eines ihrer Projektile einen anderen (lebenden) Panzer trifft."""
    for shooter in players:
        for p in shooter["projectiles"][:]:
            bullet_box = canvas.coords(p["id"])

            for target in players:
                if target is shooter or not target["alive"]:
                    continue

                tank_box = canvas.bbox(target["tank"])
                if tank_box and rects_overlap(bullet_box, tank_box):
                    target["alive"] = False
                    canvas.delete(target["tank"])
                    canvas.delete(p["id"])
                    shooter["projectiles"].remove(p)
                    break


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

    tree_photos = [load_tree_photo(path) for path in TREE_IMAGE_PATHS]
    canvas.tree_photos = tree_photos  # Referenz halten, sonst Garbage Collection
    obstacle_boxes = spawn_obstacles(canvas, WIDTH, HEIGHT, tree_photos)

    tank_images = get_tank_images()

    tree_boxes = [tree["box"] for tree in obstacle_boxes]
    tank_half_w = tank_images[0].width() // 2
    tank_half_h = tank_images[0].height() // 2

    def random_tank_spawn():
        return random_spawn_position(WIDTH, HEIGHT, tree_boxes, tank_half_w, tank_half_h)

    spawn1_x, spawn1_y = random_tank_spawn()
    spawn2_x, spawn2_y = random_tank_spawn()

    players = [
        create_player(root, canvas, "Spieler 1", PLAYER_KEYS[1], tank_images, spawn1_x, spawn1_y),
        create_player(root, canvas, "Spieler 2", PLAYER_KEYS[2], tank_images, spawn2_x, spawn2_y),
    ]
    if mode == "1 vs 1 vs 1":
        spawn3_x, spawn3_y = random_tank_spawn()
        players.append(
            create_player(root, canvas, "Spieler 3", PLAYER_KEYS[3], tank_images, spawn3_x, spawn3_y)
        )
 
    keys_pressed = set()
 
    def on_key_down(event):
        keys_pressed.add(event.keysym.lower())
 
    def on_key_up(event):
        keys_pressed.discard(event.keysym.lower())
 
    root.bind("<KeyPress>", on_key_down)
    root.bind("<KeyRelease>", on_key_up)

    move_channel = None

    def game_loop():
        nonlocal move_channel

        for player in players:
            update_player(canvas, player, keys_pressed, WIDTH, HEIGHT, obstacle_boxes)

        any_moving = any(p["moving"] for p in players)
        if any_moving and move_channel is None:
            move_channel = MOVE_SOUND.play(loops=-1)
        elif not any_moving and move_channel is not None:
            move_channel.fadeout(MOVE_SOUND_FADEOUT_MS)
            move_channel = None

        check_hits(canvas, players)

        alive_players = [p for p in players if p["alive"]]
        if len(alive_players) <= 1:
            if move_channel is not None:
                move_channel.fadeout(MOVE_SOUND_FADEOUT_MS)
            winner_text = f"{alive_players[0]['name']} gewinnt!" if alive_players else "Unentschieden!"
            canvas.create_text(
                WIDTH // 2, HEIGHT // 2,
                text=winner_text, fill="white", font=("Calibri", 32, "bold"),
            )
            return

        root.after(DELAY, game_loop)

    game_loop()
 