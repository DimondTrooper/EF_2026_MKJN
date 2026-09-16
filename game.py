import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import math
import time
import pygame
from tkinter import Canvas
from PIL import Image, ImageTk
from build_tank_images import get_tank_images
import random

BACKGROUND_PATH = "Assets/Map_Hintergrund.png"
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

# Panzer-Bilder sind quadratisch (gleiche Groesse in jeder Drehstufe), aber
# je nach Drehung ist der sichtbare Panzer rautenfoermig statt rechteckig --
# eine runde Hitbox passt sich dem viel besser an als das volle Quadrat.
TANK_HITBOX_SCALE = 0.5

MINE_IMAGE_PATH = "Assets/Mine.png"
MINE_COUNT = 6
MINE_DISPLAY_SIZE = 30
MINE_HITBOX_SCALE = 0.8

# Platzhalter-Frames -- spaeter durch die echten 3 Schuss-Animationsbilder ersetzen
SHOOT_ANIMATION_PATHS = ["Assets/Shoot_1.png", "Assets/Shoot_2.png", "Assets/Shoot_3.png"]
SHOOT_ANIMATION_SIZE = 40
SHOOT_ANIMATION_FRAME_MS = 60

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


def load_shoot_animation_frames():
    """
    Macht: Laedt die 3 Schuss-Animationsbilder und skaliert sie auf SHOOT_ANIMATION_SIZE.
    Input: keine
    Output: Liste von 3 ImageTk.PhotoImage
    """
    return [load_image_scaled_to(path, SHOOT_ANIMATION_SIZE) for path in SHOOT_ANIMATION_PATHS]


def load_mine_photo():
    """
    Macht: Laedt das Minen-Bild, schneidet es auf den sichtbaren Inhalt zu
           und skaliert es auf MINE_DISPLAY_SIZE.
    Input: keine
    Output: ImageTk.PhotoImage
    """
    img = Image.open(MINE_IMAGE_PATH).convert("RGBA")
    img = img.crop(img.getbbox())
    scale = MINE_DISPLAY_SIZE / max(img.width, img.height)
    new_size = (round(img.width * scale), round(img.height * scale))
    return ImageTk.PhotoImage(img.resize(new_size))


def spawn_mines(canvas, width, height, mine_photo, avoid_boxes):
    """
    Macht: Platziert MINE_COUNT Minen an zufaelligen Positionen, die keine
           der avoid_boxes (z.B. Baeume) ueberlappen.
    Input: canvas, width, height (Spielfeldgroesse), mine_photo (Minen-Bild),
           avoid_boxes (Liste von Rechtecken, die gemieden werden)
    Output: Liste von Minen-Dicts {"id", "cx", "cy", "radius"}
    """
    mine_half = MINE_DISPLAY_SIZE / 2
    mines = []
    for _ in range(MINE_COUNT):
        x, y = random_spawn_position(width, height, avoid_boxes, mine_half, mine_half)
        mine_id = canvas.create_image(x, y, image=mine_photo)
        mines.append({"id": mine_id, "cx": x, "cy": y, "radius": mine_half * MINE_HITBOX_SCALE})
    return mines


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


def circles_overlap(cx1, cy1, r1, cx2, cy2, r2):
    """
    Macht: Prueft, ob sich zwei Kreise ueberschneiden.
    Input: cx1, cy1, r1 (erster Kreis), cx2, cy2, r2 (zweiter Kreis)
    Output: True oder False
    """
    dx = cx1 - cx2
    dy = cy1 - cy2
    combined_radius = r1 + r2
    return (dx * dx + dy * dy) <= combined_radius * combined_radius


def tank_hit_circle(canvas, player):
    """
    Macht: Ermittelt Mittelpunkt und Radius der runden Hitbox eines Panzers.
    Input: canvas, player (Spieler-Dict)
    Output: (cx, cy, radius)
    """
    x, y = canvas.coords(player["tank"])
    radius = min(player["tank_width"], player["tank_height"]) / 2 * TANK_HITBOX_SCALE
    return x, y, radius


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


def create_player(root, canvas, name, keys, tank_images, start_x, start_y, shoot_frames):
    """
    Macht: Erstellt einen neuen Spieler samt Panzer-Bild und Schuss-Tastenbindung.
    Input: root (Tk-Fenster), canvas, name (Spielername), keys (Tastenbelegung),
           tank_images (Dict mit Panzerbildern), start_x, start_y (Startposition),
           shoot_frames (Liste der 3 Schuss-Animationsbilder)
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
        "shoot_frames": shoot_frames,
        "state": {
            "angle": 0,
            "target_angle": 0,
            "last_rotate_time": 0,
            "rotation_ready_time": 0,
            "last_shot_time": 0,
        },
        "projectiles": [],
        "shoot_animations": [],
    }

    def on_shoot(event):
        """
        Macht: Feuert einen Schuss ab, falls der Spieler lebt und der Cooldown abgelaufen ist,
               und startet die Schuss-Animation am Rohrende.
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

        anim_id = canvas.create_image(start_bx, start_by, image=shoot_frames[0])
        player["shoot_animations"].append({
            "id": anim_id,
            "frame": 0,
            "next_frame_time": now + SHOOT_ANIMATION_FRAME_MS / 1000,
        })

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


def move_tank(canvas, player, dx, dy, width, height, obstacles, other_players, mines):
    """
    Macht: Bewegt den Panzer, sofern die Zielposition frei von Baeumen und
           anderen (lebenden) Panzern ist. Faehrt der Panzer auf eine Mine,
           stirbt er und die Mine wird entfernt.
    Input: canvas, player, dx, dy (Bewegungsdelta), width, height (Spielfeldgroesse),
           obstacles (Liste von Baeumen), other_players (Liste der uebrigen Spieler),
           mines (Liste der Minen)
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
    new_radius = min(player["tank_width"], player["tank_height"]) / 2 * TANK_HITBOX_SCALE

    blocked_by_tree = any(
        circles_overlap(new_x, new_y, new_radius, tree["cx"], tree["cy"], tree["radius"])
        for tree in obstacles
    )
    blocked_by_tank = any(
        circles_overlap(new_x, new_y, new_radius, *tank_hit_circle(canvas, other))
        for other in other_players
        if other["alive"]
    )
    if blocked_by_tree or blocked_by_tank:
        return

    canvas.move(player["tank"], new_x - x, new_y - y)
    player["moving"] = True

    hit_mine = next(
        (mine for mine in mines if circles_overlap(new_x, new_y, new_radius, mine["cx"], mine["cy"], mine["radius"])),
        None,
    )
    if hit_mine is not None:
        canvas.delete(hit_mine["id"])
        mines.remove(hit_mine)
        canvas.delete(player["tank"])
        player["alive"] = False
        player["moving"] = False


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


def update_shoot_animations(canvas, player):
    """
    Macht: Spielt fuer jeden aktiven Schuss die naechsten Animations-Frames ab
           und entfernt die Animation, sobald der letzte Frame gezeigt wurde.
    Input: canvas, player
    Output: kein Rueckgabewert
    """
    now = time.time()
    for anim in player["shoot_animations"][:]:
        if now < anim["next_frame_time"]:
            continue

        anim["frame"] += 1
        if anim["frame"] >= len(player["shoot_frames"]):
            canvas.delete(anim["id"])
            player["shoot_animations"].remove(anim)
            continue

        canvas.itemconfig(anim["id"], image=player["shoot_frames"][anim["frame"]])
        anim["next_frame_time"] = now + SHOOT_ANIMATION_FRAME_MS / 1000


def update_player(canvas, player, keys_pressed, width, height, obstacles, trunk_photo, other_players, mines):
    """
    Macht: Aktualisiert einen Spieler fuer einen Frame (Drehung, Bewegung, Projektile).
    Input: canvas, player, keys_pressed, width, height (Spielfeldgroesse),
           obstacles (Baeume), trunk_photo (Stumpf-Bild), other_players (uebrige Spieler),
           mines (Liste der Minen)
    Output: kein Rueckgabewert
    """
    update_shoot_animations(canvas, player)  # auch nach dem Tod zu Ende abspielen

    if not player["alive"]:
        player["moving"] = False
        return

    up, down, left, right, dx, dy = read_movement_keys(player["keys"], keys_pressed)
    update_rotation(canvas, player, up, down, left, right)
    move_tank(canvas, player, dx, dy, width, height, obstacles, other_players, mines)
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

                cx, cy, radius = tank_hit_circle(canvas, target)
                if circle_rect_overlap(cx, cy, radius, bullet_box):
                    target["alive"] = False
                    canvas.delete(target["tank"])
                    canvas.delete(p["id"])
                    shooter["projectiles"].remove(p)
                    break


def run_game(root, mode, player_names=None):
    """
    Macht: Baut das Spielfeld auf (Hintergrund, Baeume, Spieler) und startet die Spiel-Loop.
    Input: root (Tk-Fenster), mode (Spielmodus-String, "1 vs 1" oder "1 vs 1 vs 1"),
           player_names (Liste der vom Menu eingegebenen Spielernamen, optional)
    Output: kein Rueckgabewert
    """
    player_count = 3 if mode == "1 vs 1 vs 1" else 2
    if not player_names or len(player_names) < player_count:
        player_names = [f"Spieler {n}" for n in range(1, player_count + 1)]
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

    mine_photo = load_mine_photo()
    canvas.mine_photo = mine_photo
    mines = spawn_mines(canvas, WIDTH, HEIGHT, mine_photo, tree_boxes)
    mine_boxes = [
        (mine["cx"] - mine["radius"], mine["cy"] - mine["radius"], mine["cx"] + mine["radius"], mine["cy"] + mine["radius"])
        for mine in mines
    ]
    spawn_avoid_boxes = tree_boxes + mine_boxes

    shoot_frames = load_shoot_animation_frames()
    canvas.shoot_frames = shoot_frames

    placed_spawns = []

    def random_tank_spawn():
        """
        Macht: Findet eine Position mit Abstand zu Baeumen und zu bereits vergebenen Panzer-Spawns.
        Input: keine
        Output: (x, y) -- eine Spawnposition
        """
        for _ in range(50):
            x, y = random_spawn_position(WIDTH, HEIGHT, spawn_avoid_boxes, tank_half_w, tank_half_h)
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
        create_player(root, canvas, player_names[0], PLAYER_KEYS[1], tank_images_by_player[1], spawn1_x, spawn1_y, shoot_frames),
        create_player(root, canvas, player_names[1], PLAYER_KEYS[2], tank_images_by_player[2], spawn2_x, spawn2_y, shoot_frames),
    ]
    if mode == "1 vs 1 vs 1":
        spawn3_x, spawn3_y = random_tank_spawn()
        players.append(
            create_player(root, canvas, player_names[2], PLAYER_KEYS[3], tank_images_by_player[3], spawn3_x, spawn3_y, shoot_frames)
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
            other_players = [p for p in players if p is not player]
            update_player(canvas, player, keys_pressed, WIDTH, HEIGHT, obstacle_boxes, trunk_photo, other_players, mines)

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
