import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import math
import time
import pygame
from tkinter import Canvas
from PIL import Image, ImageTk
from build_tank_images import get_tank_images
import random

BACKGROUND_PATH = "Assets/Map_real.png"
SHOOT_SOUND_PATH = "Sounds/Shoot.wav"
MOVE_SOUND_PATH = "Sounds/Tank_moving.wav"
MOVE_SOUND_FADEOUT_MS = 300

TREE_IMAGE_PATHS = ["Assets/Tree_1.png", "Assets/Tree_2.png"]
TREE_TRUNK_PATH = "Assets/Tree_Trunk.png"
TREE_SCALE = 0.8
TREE_TRUNK_SIZE_RATIO = 0.5
TREE_HITBOX_SCALE = 0.85
OBSTACLE_MIN_COUNT = 7
OBSTACLE_MAX_COUNT = 15

pygame.mixer.init()
SHOOT_SOUND = pygame.mixer.Sound(SHOOT_SOUND_PATH)
MOVE_SOUND = pygame.mixer.Sound(MOVE_SOUND_PATH)

SPEED = 1.5
FPS = 60
DELAY = int(1000 / FPS)

ROTATE_COOLDOWN = 0.12

SPAWN_MARGIN = 60
MIN_PLAYER_SPAWN_DISTANCE = 200

ROTATE_RESTART_COOLDOWN = 0.15

SHOOT_COOLDOWN = 4
PROJECTILE_SPEED = 8
PROJECTILE_RADIUS = 4
BARREL_OFFSET = 20

ANGLE_STEPS = [0, 45, 90, 135, 180, 225, 270, 315]

DIRECTION_TO_ANGLE = {
    (True, False, False, False): 0,
    (True, False, False, True): 315,
    (False, False, False, True): 270,
    (False, True, False, True): 225,
    (False, True, False, False): 180,
    (False, True, True, False): 135,
    (False, False, True, False): 90,
    (True, False, True, False): 45,
}
ANGLE_TO_VECTOR = {
    0:   (0, -1),
    45:  (-1, -1),
    90:  (-1, 0),
    135: (-1, 1),
    180: (0, 1),
    225: (1, 1),
    270: (1, 0),
    315: (1, -1),
}

PLAYER_KEYS = {
    1: {"up": "w", "down": "s", "left": "a", "right": "d", "shoot": "e"},
    2: {"up": "up", "down": "down", "left": "left", "right": "right", "shoot": "Control_R"},
    3: {"up": "up", "down": "down", "left": "left", "right": "right", "shoot": "Control_L"},
}

PLAYER_COLORS = {
    1: "blue",
    2: "red",
    3: "green",
}


def clamp(value, min_value, max_value):
    """
    Macht: Begrenzt einen Wert auf einen erlaubten Bereich.
    Input: value, min_value, max_value (Zahlen)
    Output: Zahl, begrenzt auf den Bereich [min_value, max_value]
    """
    return max(min_value, min(value, max_value))


def random_spawn_position(width, height, avoid_boxes=None, half_w=0, half_h=0, max_attempts=50):
    """
    Macht: Sucht eine zufaellige Position im Spielfeld, die keine der avoid_boxes ueberlappt.
    Input: width, height (Spielfeldgroesse), avoid_boxes (Liste von Rechtecken, optional),
           half_w, half_h (halbe Groesse des zu platzierenden Objekts), max_attempts (Zahl)
    Output: (x, y) -- eine Position im Spielfeld
    """
    for _ in range(max_attempts):
        x = random.randint(SPAWN_MARGIN, width - SPAWN_MARGIN)
        y = random.randint(SPAWN_MARGIN, height - SPAWN_MARGIN)
        if not avoid_boxes:
            return x, y
        candidate_box = (x - half_w, y - half_h, x + half_w, y + half_h)
        if not any(rects_overlap(candidate_box, box) for box in avoid_boxes):
            return x, y
    return x, y


def load_tree_photo(path):
    """
    Macht: Laedt ein Baumbild und skaliert es um den Faktor TREE_SCALE.
    Input: path (Dateipfad zu einem Baumbild)
    Output: ImageTk.PhotoImage
    """
    img = Image.open(path)
    new_size = (round(img.width * TREE_SCALE), round(img.height * TREE_SCALE))
    return ImageTk.PhotoImage(img.resize(new_size))


def load_image_scaled_to(path, target_size):
    """
    Macht: Laedt ein Bild und skaliert es so, dass seine groessere Seite target_size misst.
    Input: path (Dateipfad zu einem Bild), target_size (Zielgroesse in Pixeln)
    Output: ImageTk.PhotoImage
    """
    img = Image.open(path)
    scale = target_size / max(img.width, img.height)
    new_size = (round(img.width * scale), round(img.height * scale))
    return ImageTk.PhotoImage(img.resize(new_size))


def circle_rect_overlap(cx, cy, radius, rect):
    """
    Macht: Prueft, ob sich ein Kreis und ein Rechteck ueberschneiden.
    Input: cx, cy, radius (Kreis), rect (Rechteck als x1, y1, x2, y2)
    Output: True oder False
    """
    rx1, ry1, rx2, ry2 = rect
    closest_x = clamp(cx, rx1, rx2)
    closest_y = clamp(cy, ry1, ry2)
    dx = cx - closest_x
    dy = cy - closest_y
    return (dx * dx + dy * dy) <= radius * radius


def spawn_obstacles(canvas, width, height, tree_photos):
    """
    Macht: Platziert eine zufaellige Anzahl Baeume im Spielfeld.
    Input: canvas, width, height (Spielfeldgroesse), tree_photos (Liste von Baumbildern)
    Output: Liste von Baum-Dicts {"id", "cx", "cy", "radius"}
    """
    count = random.randint(OBSTACLE_MIN_COUNT, OBSTACLE_MAX_COUNT)
    obstacles = []
    for _ in range(count):
        x, y = random_spawn_position(width, height)
        photo = random.choice(tree_photos)
        tree_id = canvas.create_image(x, y, image=photo)
        box = canvas.bbox(tree_id)
        radius = min(box[2] - box[0], box[3] - box[1]) / 2 * TREE_HITBOX_SCALE
        obstacles.append({"id": tree_id, "cx": x, "cy": y, "radius": radius})
    return obstacles


def next_step_towards(current, target):
    """
    Macht: Ermittelt den naechsten Drehschritt auf dem kuerzesten Weg zum Zielwinkel.
    Input: current, target (Winkel aus ANGLE_STEPS)
    Output: naechster Winkel aus ANGLE_STEPS
    """
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
    """
    Macht: Prueft, ob sich zwei Rechtecke ueberschneiden.
    Input: a, b (Rechtecke als x1, y1, x2, y2)
    Output: True oder False
    """
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)


def create_player(root, canvas, name, keys, tank_images, start_x, start_y):
    """
    Macht: Erstellt einen neuen Spieler samt Panzer-Bild und Schuss-Tastenbindung.
    Input: root (Tk-Fenster), canvas, name (Spielername), keys (Tastenbelegung),
           tank_images (Dict mit Panzerbildern), start_x, start_y (Startposition)
    Output: player (Dict mit allen Spielerdaten)
    """

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
        """
        Macht: Feuert einen Schuss ab, falls der Spieler lebt und der Cooldown abgelaufen ist.
        Input: event (Tkinter-Tastenereignis)
        Output: kein Rueckgabewert
        """
        if not player["alive"]:
            return
        state = player["state"]
        now = time.time()
        if now - state["last_shot_time"] < SHOOT_COOLDOWN:
            return
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


def read_movement_keys(keys, keys_pressed):
    """
    Macht: Liest die Bewegungstasten eines Spielers aus und berechnet das Bewegungsdelta.
    Input: keys (Tastenbelegung eines Spielers), keys_pressed (Menge aktuell gedrueckter Tasten)
    Output: (up, down, left, right, dx, dy)
    """
    up = keys["up"] in keys_pressed
    down = keys["down"] in keys_pressed
    left = keys["left"] in keys_pressed
    right = keys["right"] in keys_pressed

    dx = dy = 0
    if up:
        dy -= SPEED
    if down:
        dy += SPEED
    if left:
        dx -= SPEED
    if right:
        dx += SPEED

    return up, down, left, right, dx, dy


def update_rotation(canvas, player, up, down, left, right):
    """
    Macht: Aktualisiert Zielwinkel und tatsaechlichen Drehwinkel des Panzers.
    Input: canvas, player (Spieler-Dict), up, down, left, right (Bool, Bewegungstasten)
    Output: kein Rueckgabewert
    """
    state = player["state"]
    key = (up, down, left, right)
    now = time.time()

    if (
        key in DIRECTION_TO_ANGLE
        and state["angle"] == state["target_angle"]
        and now >= state["rotation_ready_time"]
    ):
        state["target_angle"] = DIRECTION_TO_ANGLE[key]

    if state["angle"] == state["target_angle"]:
        return
    if now - state["last_rotate_time"] < ROTATE_COOLDOWN:
        return

    state["last_rotate_time"] = now
    state["angle"] = next_step_towards(state["angle"], state["target_angle"])
    canvas.itemconfig(player["tank"], image=player["tank_images"][state["angle"]])
    player["tank_width"] = player["tank_images"][state["angle"]].width()
    player["tank_height"] = player["tank_images"][state["angle"]].height()
    if state["angle"] == state["target_angle"]:
        state["rotation_ready_time"] = now + ROTATE_RESTART_COOLDOWN


def move_tank(canvas, player, dx, dy, width, height, obstacles):
    """
    Macht: Bewegt den Panzer, sofern die Zielposition frei von Baeumen ist.
    Input: canvas, player, dx, dy (Bewegungsdelta), width, height (Spielfeldgroesse),
           obstacles (Liste von Baeumen)
    Output: kein Rueckgabewert
    """
    wants_to_move = dx != 0 or dy != 0
    player["moving"] = False
    if not wants_to_move:
        return

    x, y = canvas.coords(player["tank"])
    half_w = player["tank_width"] // 2
    half_h = player["tank_height"] // 2
    new_x = clamp(x + dx, half_w, width - half_w)
    new_y = clamp(y + dy, half_h, height - half_h)
    new_box = (new_x - half_w, new_y - half_h, new_x + half_w, new_y + half_h)

    blocked = any(circle_rect_overlap(tree["cx"], tree["cy"], tree["radius"], new_box) for tree in obstacles)
    if blocked:
        return

    canvas.move(player["tank"], new_x - x, new_y - y)
    player["moving"] = True


def update_projectiles(canvas, player, obstacles, trunk_photo, width, height):
    """
    Macht: Bewegt die Projektile eines Spielers weiter und entfernt sie bei
           Baum-Treffer oder beim Verlassen des Spielfelds.
    Input: canvas, player, obstacles (Baeume), trunk_photo (Stumpf-Bild),
           width, height (Spielfeldgroesse)
    Output: kein Rueckgabewert
    """
    for p in player["projectiles"][:]:
        canvas.move(p["id"], p["dx"] * PROJECTILE_SPEED, p["dy"] * PROJECTILE_SPEED)
        bullet_box = canvas.coords(p["id"])
        x1, y1, x2, y2 = bullet_box

        hit_tree = next(
            (tree for tree in obstacles if circle_rect_overlap(tree["cx"], tree["cy"], tree["radius"], bullet_box)),
            None,
        )
        if hit_tree is not None:
            canvas.itemconfig(hit_tree["id"], image=trunk_photo)
            obstacles.remove(hit_tree)

        left_field = x2 < 0 or x1 > width or y2 < 0 or y1 > height
        if left_field or hit_tree is not None:
            canvas.delete(p["id"])
            player["projectiles"].remove(p)


def update_player(canvas, player, keys_pressed, width, height, obstacles, trunk_photo):
    """
    Macht: Aktualisiert einen Spieler fuer einen Frame (Drehung, Bewegung, Projektile).
    Input: canvas, player, keys_pressed, width, height (Spielfeldgroesse),
           obstacles (Baeume), trunk_photo (Stumpf-Bild)
    Output: kein Rueckgabewert
    """
    if not player["alive"]:
        player["moving"] = False
        return

    up, down, left, right, dx, dy = read_movement_keys(player["keys"], keys_pressed)
    update_rotation(canvas, player, up, down, left, right)
    move_tank(canvas, player, dx, dy, width, height, obstacles)
    update_projectiles(canvas, player, obstacles, trunk_photo, width, height)


def check_hits(canvas, players):
    """
    Macht: Prueft fuer alle Spieler, ob ein Projektil einen gegnerischen Panzer trifft.
    Input: canvas, players (Liste aller Spieler)
    Output: kein Rueckgabewert
    """
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
    """
    Macht: Baut das Spielfeld auf (Hintergrund, Baeume, Spieler) und startet die Spiel-Loop.
    Input: root (Tk-Fenster), mode (Spielmodus-String, "1 vs 1" oder "1 vs 1 vs 1")
    Output: kein Rueckgabewert
    """
    for widget in root.winfo_children():
        widget.destroy()

    WIDTH = root.winfo_width()
    HEIGHT = root.winfo_height()

    canvas = Canvas(root, width=WIDTH, height=HEIGHT, bg="darkgreen")
    canvas.pack()

    background_image = Image.open(BACKGROUND_PATH).resize((WIDTH, HEIGHT))
    background_photo = ImageTk.PhotoImage(background_image)
    canvas.background_photo = background_photo
    canvas.create_image(0, 0, anchor="nw", image=background_photo)

    tree_photos = [load_tree_photo(path) for path in TREE_IMAGE_PATHS]
    canvas.tree_photos = tree_photos
    obstacle_boxes = spawn_obstacles(canvas, WIDTH, HEIGHT, tree_photos)

    avg_tree_size = sum(max(photo.width(), photo.height()) for photo in tree_photos) / len(tree_photos)
    trunk_photo = load_image_scaled_to(TREE_TRUNK_PATH, avg_tree_size * TREE_TRUNK_SIZE_RATIO)
    canvas.trunk_photo = trunk_photo

    player_numbers = [1, 2, 3] if mode == "1 vs 1 vs 1" else [1, 2]
    tank_images_by_player = {n: get_tank_images(PLAYER_COLORS[n]) for n in player_numbers}

    tank_half_w = tank_images_by_player[1][0].width() // 2
    tank_half_h = tank_images_by_player[1][0].height() // 2
    tree_boxes = [
        (tree["cx"] - tree["radius"], tree["cy"] - tree["radius"], tree["cx"] + tree["radius"], tree["cy"] + tree["radius"])
        for tree in obstacle_boxes
    ]

    placed_spawns = []

    def random_tank_spawn():
        """
        Macht: Findet eine Position mit Abstand zu Baeumen und zu bereits vergebenen Panzer-Spawns.
        Input: keine
        Output: (x, y) -- eine Spawnposition
        """
        for _ in range(50):
            x, y = random_spawn_position(WIDTH, HEIGHT, tree_boxes, tank_half_w, tank_half_h)
            far_enough = all(
                math.hypot(x - px, y - py) >= MIN_PLAYER_SPAWN_DISTANCE
                for px, py in placed_spawns
            )
            if far_enough:
                break
        placed_spawns.append((x, y))
        return x, y

    spawn1_x, spawn1_y = random_tank_spawn()
    spawn2_x, spawn2_y = random_tank_spawn()

    players = [
        create_player(root, canvas, "Spieler 1", PLAYER_KEYS[1], tank_images_by_player[1], spawn1_x, spawn1_y),
        create_player(root, canvas, "Spieler 2", PLAYER_KEYS[2], tank_images_by_player[2], spawn2_x, spawn2_y),
    ]
    if mode == "1 vs 1 vs 1":
        spawn3_x, spawn3_y = random_tank_spawn()
        players.append(
            create_player(root, canvas, "Spieler 3", PLAYER_KEYS[3], tank_images_by_player[3], spawn3_x, spawn3_y)
        )

    keys_pressed = set()

    def on_key_down(event):
        """
        Macht: Merkt sich eine gedrueckte Taste.
        Input: event (Tkinter-Tastenereignis)
        Output: kein Rueckgabewert
        """
        keys_pressed.add(event.keysym.lower())

    def on_key_up(event):
        """
        Macht: Entfernt eine losgelassene Taste.
        Input: event (Tkinter-Tastenereignis)
        Output: kein Rueckgabewert
        """
        keys_pressed.discard(event.keysym.lower())

    root.bind("<KeyPress>", on_key_down)
    root.bind("<KeyRelease>", on_key_up)

    move_channel = None

    def game_loop():
        """
        Macht: Fuehrt einen Frame der Spiel-Loop aus (Update, Sound, Treffer,
               Sieg-Check) und plant den naechsten Frame.
        Input: keine
        Output: kein Rueckgabewert
        """
        nonlocal move_channel

        for player in players:
            update_player(canvas, player, keys_pressed, WIDTH, HEIGHT, obstacle_boxes, trunk_photo)

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
