import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import math
import time
import pygame
from tkinter import Canvas
from PIL import Image, ImageTk
from build_tank_images import get_muzzle_flash_frames, get_tank_images
from winner_screen import show_winner_screen
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

SHOOT_ANIMATION_FRAME_MS = 60
EXPLOSION_FRAME_DIR = "Assets/Tank_Explosion_Defeat"
EXPLOSION_FRAME_COUNT = 4
EXPLOSION_FRAME_MS = 80
EXPLOSION_DISPLAY_SIZE = 110

pygame.mixer.init()
SHOOT_SOUND = pygame.mixer.Sound(SHOOT_SOUND_PATH)
MOVE_SOUND = pygame.mixer.Sound(MOVE_SOUND_PATH)

SPEED = 1
FPS = 60
DELAY = int(1000 / FPS)

ROTATE_COOLDOWN = 0.35  # Zeit (Sekunden) pro 45-Grad-Drehschritt, solange Drehen gehalten wird

SPAWN_MARGIN = 60
MIN_PLAYER_SPAWN_DISTANCE = 200

SHOOT_COOLDOWN = 4
PROJECTILE_SPEED = 8
PROJECTILE_RADIUS = 4
BARREL_OFFSET = 20

ANGLE_STEPS = [0, 45, 90, 135, 180, 225, 270, 315]

# Normierte Richtungsvektoren (Laenge 1) -- dadurch ist die Fahrgeschwindigkeit
# in jede Blickrichtung gleich schnell, auch diagonal.
_DIAG = 0.7071067811865476  # 1/sqrt(2)
ANGLE_TO_VECTOR = {
    0:   (0, -1),
    45:  (-_DIAG, -_DIAG),
    90:  (-1, 0),
    135: (-_DIAG, _DIAG),
    180: (0, 1),
    225: (_DIAG, _DIAG),
    270: (1, 0),
    315: (_DIAG, -_DIAG),
}

PLAYER_KEYS = {
    1: {"up": "w", "down": "s", "left": "a", "right": "d", "shoot": "e"},
    2: {"up": "up", "down": "down", "left": "left", "right": "right", "shoot": "Control_R"},
    3: {"up": "z", "down": "h", "left": "g", "right": "j", "shoot": "u"},
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


def load_explosion_frames():
    """
    Macht: Laedt die Explosionsframes und zentriert sie auf einer gleich grossen Bildflaeche.
    Input: keine
    Output: Liste von ImageTk.PhotoImage
    """
    source_frames = [
        Image.open(f"{EXPLOSION_FRAME_DIR}/Explosion_{number}.png").convert("RGBA")
        for number in range(1, EXPLOSION_FRAME_COUNT + 1)
    ]
    scale = EXPLOSION_DISPLAY_SIZE / max(max(frame.width, frame.height) for frame in source_frames)
    frames = []
    for frame in source_frames:
        resized = frame.resize((round(frame.width * scale), round(frame.height * scale)), Image.LANCZOS)
        centered = Image.new("RGBA", (EXPLOSION_DISPLAY_SIZE, EXPLOSION_DISPLAY_SIZE), (0, 0, 0, 0))
        offset = ((EXPLOSION_DISPLAY_SIZE - resized.width) // 2, (EXPLOSION_DISPLAY_SIZE - resized.height) // 2)
        centered.paste(resized, offset, resized)
        frames.append(ImageTk.PhotoImage(centered))
    return frames


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


def rects_overlap(a, b):
    """
    Macht: Prueft, ob sich zwei Rechtecke ueberschneiden.
    Input: a, b (Rechtecke als x1, y1, x2, y2)
    Output: True oder False
    """
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)


def create_player(root, canvas, name, keys, tank_images, muzzle_flash_frames, start_x, start_y):
    """
    Macht: Erstellt einen neuen Spieler samt Panzer-Bild und Schuss-Tastenbindung.
    Input: root (Tk-Fenster), canvas, name (Spielername), keys (Tastenbelegung),
           tank_images (Dict mit Panzerbildern), muzzle_flash_frames (Dict mit Schussbildern),
           start_x, start_y (Startposition)
    Output: player (Dict mit allen Spielerdaten)
    """

    tank = canvas.create_image(start_x, start_y, image=tank_images[0])
    name_tag = canvas.create_text(
        start_x,
        start_y - tank_images[0].height() // 2 - 12,
        text=name,
        fill="white",
        font=("Calibri", 12, "bold"),
    )

    player = {
        "tank": tank,
        "name_tag": name_tag,
        "name": name,
        "alive": True,
        "moving": False,
        "tank_images": tank_images,
        "tank_width": tank_images[0].width(),
        "tank_height": tank_images[0].height(),
        "keys": keys,
        "muzzle_flash_frames": muzzle_flash_frames,
        "state": {
            "angle": 0,
            "last_rotate_time": 0,
            "last_shot_time": 0,
        },
        "projectiles": [],
        "shoot_animation": None,
        "explosion": None,
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

        player["shoot_animation"] = {
            "frame": 0,
            "next_frame_time": now + SHOOT_ANIMATION_FRAME_MS / 1000,
        }
        show_tank_image(canvas, player)

    root.bind(f"<KeyPress-{keys['shoot']}>", on_shoot)

    return player


def show_tank_image(canvas, player):
    """
    Macht: Zeigt das normale Panzerbild oder den aktuellen Schuss-Animationsframe.
    Input: canvas, player (Spieler-Dict)
    Output: kein Rueckgabewert
    """
    angle = player["state"]["angle"]
    animation = player["shoot_animation"]
    if animation is None:
        image = player["tank_images"][angle]
    else:
        image = player["muzzle_flash_frames"][angle][animation["frame"]]
    canvas.itemconfig(player["tank"], image=image)


def destroy_player(canvas, player, explosion_frames):
    """
    Macht: Entfernt einen Panzer und startet seine Explosionsanimation an derselben Position.
    Input: canvas, player (Spieler-Dict), explosion_frames (Liste von Explosionsbildern)
    Output: kein Rueckgabewert
    """
    if not player["alive"]:
        return
    x, y = canvas.coords(player["tank"])
    canvas.delete(player["tank"])
    canvas.delete(player["name_tag"])
    explosion_id = canvas.create_image(x, y, image=explosion_frames[0])
    player["alive"] = False
    player["moving"] = False
    player["shoot_animation"] = None
    player["explosion"] = {
        "id": explosion_id,
        "frame": 0,
        "next_frame_time": time.time() + EXPLOSION_FRAME_MS / 1000,
    }


def read_movement_keys(keys, keys_pressed):
    """
    Macht: Liest die Panzersteuerung eines Spielers aus (vor/zurueck + drehen).
    Input: keys (Tastenbelegung eines Spielers), keys_pressed (Menge aktuell gedrueckter Tasten)
    Output: (forward, backward, turn_left, turn_right) -- alles Bool
    """
    forward = keys["up"] in keys_pressed
    backward = keys["down"] in keys_pressed
    turn_left = keys["left"] in keys_pressed
    turn_right = keys["right"] in keys_pressed
    return forward, backward, turn_left, turn_right


def update_rotation(canvas, player, turn_left, turn_right):
    """
    Macht: Dreht den Panzer schrittweise (45 Grad pro ROTATE_COOLDOWN), solange
           genau eine der beiden Drehtasten gehalten wird.
    Input: canvas, player (Spieler-Dict), turn_left, turn_right (Bool)
    Output: kein Rueckgabewert
    """
    if turn_left == turn_right:
        return  # keine oder beide Tasten gedrueckt -> keine Drehung

    state = player["state"]
    now = time.time()
    if now - state["last_rotate_time"] < ROTATE_COOLDOWN:
        return

    state["last_rotate_time"] = now
    i_current = ANGLE_STEPS.index(state["angle"])
    step = 1 if turn_left else -1
    state["angle"] = ANGLE_STEPS[(i_current + step) % len(ANGLE_STEPS)]
    show_tank_image(canvas, player)
    player["tank_width"] = player["tank_images"][state["angle"]].width()
    player["tank_height"] = player["tank_images"][state["angle"]].height()


def move_tank(canvas, player, forward, backward, width, height, obstacles, other_players, mines, explosion_frames):
    """
    Macht: Bewegt den Panzer in (bei Rueckwaertsfahrt: entgegen) seiner
           aktuellen Blickrichtung, sofern die Zielposition frei von Baeumen
           und anderen (lebenden) Panzern ist. Faehrt der Panzer auf eine
           Mine, stirbt er und die Mine wird entfernt.
    Input: canvas, player, forward, backward (Bool), width, height (Spielfeldgroesse),
           obstacles (Liste von Baeumen), other_players (Liste der uebrigen Spieler),
           mines (Liste der Minen), explosion_frames (Liste von Explosionsbildern)
    Output: kein Rueckgabewert
    """
    player["moving"] = False
    if forward == backward:
        return  # keine oder beide Tasten gedrueckt -> keine Bewegung

    vx, vy = ANGLE_TO_VECTOR[player["state"]["angle"]]
    direction = 1 if forward else -1
    dx = vx * SPEED * direction
    dy = vy * SPEED * direction

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
    canvas.move(player["name_tag"], new_x - x, new_y - y)
    player["moving"] = True

    hit_mine = next(
        (mine for mine in mines if circles_overlap(new_x, new_y, new_radius, mine["cx"], mine["cy"], mine["radius"])),
        None,
    )
    if hit_mine is not None:
        canvas.delete(hit_mine["id"])
        mines.remove(hit_mine)
        destroy_player(canvas, player, explosion_frames)


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
    Macht: Spielt die Schuss-Animation eines Spielers ab und stellt danach das normale Panzerbild wieder her.
    Input: canvas, player
    Output: kein Rueckgabewert
    """
    animation = player["shoot_animation"]
    if animation is None or time.time() < animation["next_frame_time"]:
        return

    animation["frame"] += 1
    if animation["frame"] >= len(player["muzzle_flash_frames"][player["state"]["angle"]]):
        player["shoot_animation"] = None
    else:
        animation["next_frame_time"] = time.time() + SHOOT_ANIMATION_FRAME_MS / 1000
    show_tank_image(canvas, player)


def update_explosion(canvas, player, explosion_frames):
    """
    Macht: Zeigt den naechsten Explosionsframe und entfernt die Explosion nach dem letzten Frame.
    Input: canvas, player (Spieler-Dict), explosion_frames (Liste von Explosionsbildern)
    Output: kein Rueckgabewert
    """
    explosion = player["explosion"]
    if explosion is None or time.time() < explosion["next_frame_time"]:
        return
    explosion["frame"] += 1
    if explosion["frame"] >= len(explosion_frames):
        canvas.delete(explosion["id"])
        player["explosion"] = None
        return
    canvas.itemconfig(explosion["id"], image=explosion_frames[explosion["frame"]])
    explosion["next_frame_time"] = time.time() + EXPLOSION_FRAME_MS / 1000


def update_player(canvas, player, keys_pressed, width, height, obstacles, trunk_photo, other_players, mines, explosion_frames):
    """
    Macht: Aktualisiert einen Spieler fuer einen Frame (Drehung, Bewegung, Projektile).
    Input: canvas, player, keys_pressed, width, height (Spielfeldgroesse),
           obstacles (Baeume), trunk_photo (Stumpf-Bild), other_players (uebrige Spieler),
           mines (Liste der Minen), explosion_frames (Liste von Explosionsbildern)
    Output: kein Rueckgabewert
    """
    update_shoot_animations(canvas, player)
    update_explosion(canvas, player, explosion_frames)

    if not player["alive"]:
        player["moving"] = False
        return

    forward, backward, turn_left, turn_right = read_movement_keys(player["keys"], keys_pressed)
    update_rotation(canvas, player, turn_left, turn_right)
    move_tank(canvas, player, forward, backward, width, height, obstacles, other_players, mines, explosion_frames)
    update_projectiles(canvas, player, obstacles, trunk_photo, width, height)


def check_hits(canvas, players, explosion_frames):
    """
    Macht: Prueft fuer alle Spieler, ob ein Projektil einen gegnerischen Panzer trifft.
    Input: canvas, players (Liste aller Spieler), explosion_frames (Liste von Explosionsbildern)
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
                    destroy_player(canvas, target, explosion_frames)
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
    muzzle_flash_frames_by_player = {
        n: get_muzzle_flash_frames(PLAYER_COLORS[n]) for n in player_numbers
    }
    explosion_frames = load_explosion_frames()
    canvas.explosion_frames = explosion_frames

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
        create_player(root, canvas, player_names[0], PLAYER_KEYS[1], tank_images_by_player[1], muzzle_flash_frames_by_player[1], spawn1_x, spawn1_y),
        create_player(root, canvas, player_names[1], PLAYER_KEYS[2], tank_images_by_player[2], muzzle_flash_frames_by_player[2], spawn2_x, spawn2_y),
    ]
    if mode == "1 vs 1 vs 1":
        spawn3_x, spawn3_y = random_tank_spawn()
        players.append(
            create_player(root, canvas, player_names[2], PLAYER_KEYS[3], tank_images_by_player[3], muzzle_flash_frames_by_player[3], spawn3_x, spawn3_y)
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
            update_player(
                canvas, player, keys_pressed, WIDTH, HEIGHT, obstacle_boxes,
                trunk_photo, other_players, mines, explosion_frames,
            )

        any_moving = any(p["moving"] for p in players)
        if any_moving and move_channel is None:
            move_channel = MOVE_SOUND.play(loops=-1)
        elif not any_moving and move_channel is not None:
            move_channel.fadeout(MOVE_SOUND_FADEOUT_MS)
            move_channel = None

        check_hits(canvas, players, explosion_frames)

        alive_players = [p for p in players if p["alive"]]
        if len(alive_players) <= 1:
            if any(player["explosion"] is not None for player in players):
                root.after(DELAY, game_loop)
                return
            if move_channel is not None:
                move_channel.fadeout(MOVE_SOUND_FADEOUT_MS)
            winner_text = f"{alive_players[0]['name']} gewinnt!" if alive_players else "Unentschieden!"
            for player_keys in PLAYER_KEYS.values():
                root.unbind(f"<KeyPress-{player_keys['shoot']}>")
            root.unbind("<KeyPress>")
            root.unbind("<KeyRelease>")
            show_winner_screen(
                root,
                winner_text,
                lambda: run_game(root, mode, player_names),
            )
            return

        root.after(DELAY, game_loop)

    game_loop()
