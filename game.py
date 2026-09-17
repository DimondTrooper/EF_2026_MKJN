import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import math
import random
import time

import pygame
from tkinter import Button, Canvas
from PIL import Image, ImageTk

from build_tank_images import HULL_PX, get_destroyed_tank_images, get_muzzle_flash_frames, get_tank_images
from scoreboard import get_leaderboard, record_win, register_players
from utils import resource_path
from winner_screen import show_winner_screen

# --- Bilder ---
BACKGROUND_PATH = resource_path("Assets/Map_Hintergrund.png")
TREE_IMAGE_PATHS = [resource_path("Assets/Tree_1.png"), resource_path("Assets/Tree_2.png")]
TREE_TRUNK_PATH = resource_path("Assets/Tree_Trunk.png")
MINE_IMAGE_PATH = resource_path("Assets/Mine.png")
EXPLOSION_FRAME_DIR = resource_path("Assets/Tank_Explosion_Defeat")

# --- Sounds ---
SHOOT_SOUND_PATH = resource_path("Sounds/Shoot.wav")
MOVE_SOUND_PATH = resource_path("Sounds/Tank_moving.wav")
IDLE_TANK_SOUND_PATH = resource_path("Sounds/idle_Tank.wav")
BREEZE_SOUND_PATH = resource_path("Sounds/Ambient_Sounds/breeze-tree.wav")
DISTANT_EXPLOSION_SOUND_PATH = resource_path("Sounds/Ambient_Sounds/distant-explosions.wav")
PLANE_SOUND_PATH = resource_path("Sounds/Ambient_Sounds/propeller-planewav.wav")

MOVE_SOUND_VOLUME = 0.25
IDLE_TANK_SOUND_VOLUME = 0.18
BREEZE_SOUND_VOLUME = 0.28
AMBIENT_SOUND_VOLUME = 0.12
MOVE_SOUND_FADEOUT_MS = 300
AMBIENT_SOUND_FADEOUT_MS = 800
DISTANT_EXPLOSION_MIN_DELAY = 6
DISTANT_EXPLOSION_MAX_DELAY = 12
PLANE_MIN_DELAY = 35
PLANE_MAX_DELAY = 60

# --- Spielfeld ---
TREE_SCALE = 0.8
TREE_TRUNK_SIZE_RATIO = 0.5
TREE_HITBOX_SCALE = 0.85
OBSTACLE_MIN_COUNT = 7
OBSTACLE_MAX_COUNT = 15

MINE_COUNT = 6
MINE_DISPLAY_SIZE = 30
MINE_HITBOX_SCALE = 0.8

SPAWN_MARGIN = 60
SPAWN_ATTEMPTS = 50
MIN_PLAYER_SPAWN_DISTANCE = 200

# Panzer und Wracks bekommen eine runde Hitbox (ein gedrehter Panzer ist eher
# rautenfoermig als rechteckig). Bezug ist die echte Rumpfbreite HULL_PX und
# nicht die Bildflaeche -- die enthaelt je nach Bild unterschiedlich viel
# leeren Rand bzw. beim Wrack eine grosse Rauchwolke.
HITBOX_SCALE = 1.15
TANK_HITBOX_RADIUS = HULL_PX / 2 * HITBOX_SCALE

# --- Animationen ---
SHOOT_ANIMATION_FRAME_MS = 60
EXPLOSION_FRAME_COUNT = 4
EXPLOSION_FRAME_MS = 80
EXPLOSION_DISPLAY_SIZE = 110
WIN_SCREEN_DELAY_MS = 3000  # Pause nach Explosion/Wrack, bevor das Leaderboard erscheint

# --- Steuerung ---
SPEED = 1
FPS = 60
DELAY = int(1000 / FPS)
ROTATE_COOLDOWN = 0.35  # Zeit (Sekunden) pro 45-Grad-Drehschritt, solange Drehen gehalten wird

SHOOT_COOLDOWN = 4
PROJECTILE_SPEED = 8
PROJECTILE_RADIUS = 4
BARREL_OFFSET = 20
RELOAD_RING_RADIUS = 6  # kleiner Nachlade-Ring neben dem Namensschild
RELOAD_RING_GAP = 6  # Abstand zwischen Namenstext und Ring
NAME_TAG_GAP = 12  # Abstand zwischen Panzerbild und Namensschild

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

PLAYER_NUMBERS_BY_MODE = {
    "1 vs 1": [1, 2],
    "1 vs 1 vs 1": [1, 2, 3],
}


def load_sound(path, volume=None):
    """
    Macht: Laedt einen Sound und stellt optional seine Lautstaerke ein.
    Input: path (Dateipfad), volume (0.0 bis 1.0, optional)
    Output: pygame.mixer.Sound
    """
    sound = pygame.mixer.Sound(path)
    if volume is not None:
        sound.set_volume(volume)
    return sound


pygame.mixer.init()
pygame.mixer.set_num_channels(16)
SHOOT_SOUND = load_sound(SHOOT_SOUND_PATH)
MOVE_SOUND = load_sound(MOVE_SOUND_PATH, MOVE_SOUND_VOLUME)
IDLE_TANK_SOUND = load_sound(IDLE_TANK_SOUND_PATH, IDLE_TANK_SOUND_VOLUME)
BREEZE_SOUND = load_sound(BREEZE_SOUND_PATH, BREEZE_SOUND_VOLUME)
DISTANT_EXPLOSION_SOUND = load_sound(DISTANT_EXPLOSION_SOUND_PATH, AMBIENT_SOUND_VOLUME)
PLANE_SOUND = load_sound(PLANE_SOUND_PATH, AMBIENT_SOUND_VOLUME)


# ============================================================================
# Hilfsfunktionen: Mathematik und Kollision
# ============================================================================

def clamp(value, min_value, max_value):
    """
    Macht: Begrenzt einen Wert auf einen erlaubten Bereich.
    Input: value, min_value, max_value (Zahlen)
    Output: Zahl, begrenzt auf den Bereich [min_value, max_value]
    """
    return max(min_value, min(value, max_value))


def rects_overlap(a, b):
    """
    Macht: Prueft, ob sich zwei Rechtecke ueberschneiden.
    Input: a, b (Rechtecke als x1, y1, x2, y2)
    Output: True oder False
    """
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)


def circle_rect_overlap(cx, cy, radius, rect):
    """
    Macht: Prueft, ob sich ein Kreis und ein Rechteck ueberschneiden.
    Input: cx, cy, radius (Kreis), rect (Rechteck als x1, y1, x2, y2)
    Output: True oder False
    """
    rx1, ry1, rx2, ry2 = rect
    dx = cx - clamp(cx, rx1, rx2)
    dy = cy - clamp(cy, ry1, ry2)
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


def circle_bounding_box(obj):
    """
    Macht: Liefert das umschliessende Rechteck eines runden Objekts.
    Input: obj (Dict mit "cx", "cy", "radius")
    Output: (x1, y1, x2, y2)
    """
    return (obj["cx"] - obj["radius"], obj["cy"] - obj["radius"],
            obj["cx"] + obj["radius"], obj["cy"] + obj["radius"])


def first_circle_hit(cx, cy, radius, objects):
    """
    Macht: Sucht das erste runde Objekt, das einen gegebenen Kreis beruehrt.
    Input: cx, cy, radius (Kreis), objects (Liste von Dicts mit "cx", "cy", "radius")
    Output: das getroffene Objekt oder None
    """
    return next(
        (obj for obj in objects if circles_overlap(cx, cy, radius, obj["cx"], obj["cy"], obj["radius"])),
        None,
    )


def first_rect_hit(rect, objects):
    """
    Macht: Sucht das erste runde Objekt, das ein Rechteck (z.B. ein Projektil) beruehrt.
    Input: rect (x1, y1, x2, y2), objects (Liste von Dicts mit "cx", "cy", "radius")
    Output: das getroffene Objekt oder None
    """
    return next(
        (obj for obj in objects if circle_rect_overlap(obj["cx"], obj["cy"], obj["radius"], rect)),
        None,
    )


def random_spawn_position(width, height, avoid_boxes=None, half_w=0, half_h=0):
    """
    Macht: Sucht eine zufaellige Position im Spielfeld, die keine der avoid_boxes ueberlappt.
    Input: width, height (Spielfeldgroesse), avoid_boxes (Liste von Rechtecken, optional),
           half_w, half_h (halbe Groesse des zu platzierenden Objekts)
    Output: (x, y) -- eine Position im Spielfeld
    """
    for _ in range(SPAWN_ATTEMPTS):
        x = random.randint(SPAWN_MARGIN, width - SPAWN_MARGIN)
        y = random.randint(SPAWN_MARGIN, height - SPAWN_MARGIN)
        candidate_box = (x - half_w, y - half_h, x + half_w, y + half_h)
        if not avoid_boxes or not any(rects_overlap(candidate_box, box) for box in avoid_boxes):
            return x, y
    return x, y


def pick_tank_spawns(count, width, height, avoid_boxes, half_size):
    """
    Macht: Sucht Startpositionen fuer die Panzer -- frei von Baeumen/Minen und
           moeglichst mit Mindestabstand zueinander.
    Input: count (Anzahl Panzer), width, height (Spielfeldgroesse),
           avoid_boxes (Rechtecke, die gemieden werden), half_size (halbe Panzergroesse)
    Output: Liste von (x, y)
    """
    spawns = []
    for _ in range(count):
        for _ in range(SPAWN_ATTEMPTS):
            x, y = random_spawn_position(width, height, avoid_boxes, half_size, half_size)
            if all(math.hypot(x - px, y - py) >= MIN_PLAYER_SPAWN_DISTANCE for px, py in spawns):
                break
        spawns.append((x, y))
    return spawns


# ============================================================================
# Bilder und Sounds laden
# ============================================================================

def scale_image(img, factor):
    """
    Macht: Vergroessert/verkleinert ein PIL-Bild um einen Faktor.
    Input: img (PIL-Bild), factor (Zahl)
    Output: PIL-Bild
    """
    new_size = (max(1, round(img.width * factor)), max(1, round(img.height * factor)))
    return img.resize(new_size, Image.LANCZOS)


def longest_side_factor(img, target_size):
    """
    Macht: Berechnet den Faktor, mit dem die laengere Bildseite target_size lang wird.
    Input: img (PIL-Bild), target_size (Zielgroesse in Pixeln)
    Output: Zahl
    """
    return target_size / max(img.width, img.height)


def center_on_square(img, size):
    """
    Macht: Legt ein Bild mittig auf eine quadratische, transparente Flaeche.
    Input: img (PIL-Bild), size (Kantenlaenge)
    Output: PIL-Bild (size x size)
    """
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
    return square


def load_tree_photo(path):
    """
    Macht: Laedt ein Baumbild und skaliert es um den Faktor TREE_SCALE.
    Input: path (Dateipfad zu einem Baumbild)
    Output: ImageTk.PhotoImage
    """
    img = Image.open(path).convert("RGBA")
    return ImageTk.PhotoImage(scale_image(img, TREE_SCALE))


def load_image_scaled_to(path, target_size):
    """
    Macht: Laedt ein Bild und skaliert es so, dass seine laengere Seite target_size misst.
    Input: path (Dateipfad zu einem Bild), target_size (Zielgroesse in Pixeln)
    Output: ImageTk.PhotoImage
    """
    img = Image.open(path).convert("RGBA")
    return ImageTk.PhotoImage(scale_image(img, longest_side_factor(img, target_size)))


def load_mine_photo():
    """
    Macht: Laedt das Minen-Bild, schneidet es auf den sichtbaren Inhalt zu
           und skaliert es auf MINE_DISPLAY_SIZE.
    Input: keine
    Output: ImageTk.PhotoImage
    """
    img = Image.open(MINE_IMAGE_PATH).convert("RGBA")
    img = img.crop(img.getbbox())
    return ImageTk.PhotoImage(scale_image(img, longest_side_factor(img, MINE_DISPLAY_SIZE)))


def load_explosion_frames():
    """
    Macht: Laedt die Explosionsframes. Alle Frames werden mit demselben Faktor
           skaliert (damit die Explosion gleichmaessig waechst) und mittig auf
           eine gleich grosse Flaeche gelegt.
    Input: keine
    Output: Liste von ImageTk.PhotoImage
    """
    source_frames = [
        Image.open(f"{EXPLOSION_FRAME_DIR}/Explosion_{number}.png").convert("RGBA")
        for number in range(1, EXPLOSION_FRAME_COUNT + 1)
    ]
    factor = min(longest_side_factor(frame, EXPLOSION_DISPLAY_SIZE) for frame in source_frames)
    return [
        ImageTk.PhotoImage(center_on_square(scale_image(frame, factor), EXPLOSION_DISPLAY_SIZE))
        for frame in source_frames
    ]


def start_match_sounds():
    """
    Macht: Startet Leerlauf-Brummen und Wind als Loop und plant Flugzeug sowie
           entfernte Explosionen.
    Input: keine
    Output: Dict mit Sound-Kanaelen und naechsten Abspielzeiten
    """
    now = time.time()
    return {
        "move": None,
        "idle": IDLE_TANK_SOUND.play(loops=-1),
        "ambient": [BREEZE_SOUND.play(loops=-1)],
        "next_explosion_time": now + random.uniform(DISTANT_EXPLOSION_MIN_DELAY, DISTANT_EXPLOSION_MAX_DELAY),
        "next_plane_time": now + random.uniform(PLANE_MIN_DELAY, PLANE_MAX_DELAY),
    }


def update_ambient_sounds(sounds):
    """
    Macht: Spielt entfernte Explosionen haeufig und Flugzeuge selten ab.
    Input: sounds (Dict aus start_match_sounds)
    Output: kein Rueckgabewert
    """
    now = time.time()
    if now >= sounds["next_explosion_time"]:
        sounds["ambient"].append(DISTANT_EXPLOSION_SOUND.play())
        sounds["next_explosion_time"] = now + random.uniform(DISTANT_EXPLOSION_MIN_DELAY, DISTANT_EXPLOSION_MAX_DELAY)
    if now >= sounds["next_plane_time"]:
        sounds["ambient"].append(PLANE_SOUND.play())
        sounds["next_plane_time"] = now + random.uniform(PLANE_MIN_DELAY, PLANE_MAX_DELAY)


def update_move_sound(sounds, players):
    """
    Macht: Spielt das Fahrgeraeusch, solange sich mindestens ein Panzer bewegt.
    Input: sounds (Dict aus start_match_sounds), players (Liste aller Spieler)
    Output: kein Rueckgabewert
    """
    any_moving = any(player["moving"] for player in players)
    if any_moving and sounds["move"] is None:
        sounds["move"] = MOVE_SOUND.play(loops=-1)
    elif not any_moving and sounds["move"] is not None:
        sounds["move"].fadeout(MOVE_SOUND_FADEOUT_MS)
        sounds["move"] = None


def stop_match_sounds(sounds):
    """
    Macht: Blendet alle Sounds der Partie aus.
    Input: sounds (Dict aus start_match_sounds)
    Output: kein Rueckgabewert
    """
    for channel in (sounds["move"], sounds["idle"]):
        if channel is not None:
            channel.fadeout(MOVE_SOUND_FADEOUT_MS)
    for channel in sounds["ambient"]:
        if channel is not None:
            channel.fadeout(AMBIENT_SOUND_FADEOUT_MS)


# ============================================================================
# Spielfeld aufbauen
# ============================================================================

def create_background(root, width, height):
    """
    Macht: Erstellt die Zeichenflaeche des Spiels mit dem Kartenbild.
    Input: root (Tk-Fenster), width, height (Spielfeldgroesse)
    Output: Canvas
    """
    canvas = Canvas(root, width=width, height=height, bg="darkgreen")
    canvas.pack()
    canvas.background_photo = ImageTk.PhotoImage(Image.open(BACKGROUND_PATH).resize((width, height)))
    canvas.create_image(0, 0, anchor="nw", image=canvas.background_photo)
    return canvas


def spawn_trees(canvas, width, height, tree_photos):
    """
    Macht: Platziert eine zufaellige Anzahl Baeume im Spielfeld.
    Input: canvas, width, height (Spielfeldgroesse), tree_photos (Liste von Baumbildern)
    Output: Liste von Baum-Dicts {"id", "cx", "cy", "radius"}
    """
    trees = []
    for _ in range(random.randint(OBSTACLE_MIN_COUNT, OBSTACLE_MAX_COUNT)):
        x, y = random_spawn_position(width, height)
        tree_id = canvas.create_image(x, y, image=random.choice(tree_photos))
        box = canvas.bbox(tree_id)
        radius = min(box[2] - box[0], box[3] - box[1]) / 2 * TREE_HITBOX_SCALE
        trees.append({"id": tree_id, "cx": x, "cy": y, "radius": radius})
    return trees


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


def build_world(root):
    """
    Macht: Baut das Spielfeld auf (Karte, Baeume, Minen) und laedt alle Bilder,
           die waehrend der Partie gebraucht werden. Die Bilder werden am
           Canvas bzw. im Dict gespeichert, damit Tkinter sie nicht loescht.
    Input: root (Tk-Fenster)
    Output: world (Dict mit allem, was zum Spielfeld gehoert)
    """
    width = root.winfo_width()
    height = root.winfo_height()
    canvas = create_background(root, width, height)

    tree_photos = [load_tree_photo(path) for path in TREE_IMAGE_PATHS]
    trees = spawn_trees(canvas, width, height, tree_photos)
    avg_tree_size = sum(max(photo.width(), photo.height()) for photo in tree_photos) / len(tree_photos)
    mine_photo = load_mine_photo()
    mines = spawn_mines(canvas, width, height, mine_photo, [circle_bounding_box(tree) for tree in trees])

    return {
        "canvas": canvas,
        "width": width,
        "height": height,
        "tree_photos": tree_photos,
        "trunk_photo": load_image_scaled_to(TREE_TRUNK_PATH, avg_tree_size * TREE_TRUNK_SIZE_RATIO),
        "mine_photo": mine_photo,
        "explosion_frames": load_explosion_frames(),
        "wreck_images": get_destroyed_tank_images(),
        "trees": trees,
        "mines": mines,
        "wrecks": [],
    }


# ============================================================================
# Spieler
# ============================================================================

def reload_ring_box(canvas, name_tag):
    """
    Macht: Berechnet die Position des Nachlade-Rings rechts neben dem Namensschild.
    Input: canvas, name_tag (Canvas-Id des Namensschilds)
    Output: (x1, y1, x2, y2) des Rings
    """
    _, top, right, bottom = canvas.bbox(name_tag)
    center_x = right + RELOAD_RING_GAP + RELOAD_RING_RADIUS
    center_y = (top + bottom) / 2
    return (center_x - RELOAD_RING_RADIUS, center_y - RELOAD_RING_RADIUS,
            center_x + RELOAD_RING_RADIUS, center_y + RELOAD_RING_RADIUS)


def create_player(root, canvas, name, keys, tank_images, muzzle_flash_frames, start):
    """
    Macht: Erstellt einen neuen Spieler samt Panzer-Bild, Namensschild,
           Nachlade-Ring und Schuss-Tastenbindung.
    Input: root (Tk-Fenster), canvas, name (Spielername), keys (Tastenbelegung),
           tank_images (Dict mit Panzerbildern), muzzle_flash_frames (Dict mit Schussbildern),
           start ((x, y) Startposition)
    Output: player (Dict mit allen Spielerdaten)
    """
    start_x, start_y = start
    tank = canvas.create_image(start_x, start_y, image=tank_images[0])
    name_tag = canvas.create_text(
        start_x, start_y - tank_images[0].height() // 2 - NAME_TAG_GAP,
        text=name, fill="white", font=("Calibri", 12, "bold"),
    )
    reload_ring = canvas.create_arc(
        *reload_ring_box(canvas, name_tag),
        start=90, extent=0, style="arc", outline="gray", width=2, state="hidden",
    )

    player = {
        "tank": tank,
        "name_tag": name_tag,
        "reload_ring": reload_ring,
        "name": name,
        "alive": True,
        "moving": False,
        "tank_images": tank_images,
        "half_size": tank_images[0].width() // 2,
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
    root.bind(f"<KeyPress-{keys['shoot']}>", lambda event: fire_bullet(canvas, player))
    return player


def create_players(root, world, mode, player_names):
    """
    Macht: Laedt die Panzerbilder und erstellt alle Spieler des Spielmodus an
           freien Startpositionen.
    Input: root (Tk-Fenster), world (Spielfeld-Dict), mode (Spielmodus),
           player_names (Liste der Spielernamen)
    Output: Liste der Spieler-Dicts
    """
    numbers = PLAYER_NUMBERS_BY_MODE[mode]
    images = {n: get_tank_images(PLAYER_COLORS[n]) for n in numbers}
    half_size = images[numbers[0]][0].width() // 2
    avoid_boxes = [circle_bounding_box(obj) for obj in world["trees"] + world["mines"]]
    spawns = pick_tank_spawns(len(numbers), world["width"], world["height"], avoid_boxes, half_size)

    return [
        create_player(
            root, world["canvas"], name, PLAYER_KEYS[number], images[number],
            get_muzzle_flash_frames(PLAYER_COLORS[number]), spawn,
        )
        for number, name, spawn in zip(numbers, player_names, spawns)
    ]


def fire_bullet(canvas, player):
    """
    Macht: Feuert einen Schuss ab, falls der Spieler lebt und der Cooldown
           abgelaufen ist, und startet die Schuss-Animation am Rohrende.
    Input: canvas, player (Spieler-Dict)
    Output: kein Rueckgabewert
    """
    state = player["state"]
    now = time.time()
    if not player["alive"] or now - state["last_shot_time"] < SHOOT_COOLDOWN:
        return
    state["last_shot_time"] = now

    x, y = canvas.coords(player["tank"])
    dx, dy = ANGLE_TO_VECTOR[state["angle"]]
    bullet_x = x + dx * BARREL_OFFSET
    bullet_y = y + dy * BARREL_OFFSET
    bullet = canvas.create_oval(
        bullet_x - PROJECTILE_RADIUS, bullet_y - PROJECTILE_RADIUS,
        bullet_x + PROJECTILE_RADIUS, bullet_y + PROJECTILE_RADIUS,
        fill="black",
    )
    player["projectiles"].append({"id": bullet, "dx": dx, "dy": dy})
    SHOOT_SOUND.play()

    player["shoot_animation"] = {"frame": 0, "next_frame_time": now + SHOOT_ANIMATION_FRAME_MS / 1000}
    show_tank_image(canvas, player)


def tank_circle(canvas, player):
    """
    Macht: Liefert die runde Hitbox eines Panzers.
    Input: canvas, player (Spieler-Dict)
    Output: Dict {"cx", "cy", "radius"}
    """
    x, y = canvas.coords(player["tank"])
    return {"cx": x, "cy": y, "radius": TANK_HITBOX_RADIUS}


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


def destroy_player(world, player):
    """
    Macht: Entfernt einen Panzer und startet seine Explosionsanimation an derselben Position.
    Input: world (Spielfeld-Dict), player (Spieler-Dict)
    Output: kein Rueckgabewert
    """
    if not player["alive"]:
        return
    canvas = world["canvas"]
    x, y = canvas.coords(player["tank"])
    for item in (player["tank"], player["name_tag"], player["reload_ring"]):
        canvas.delete(item)
    player["alive"] = False
    player["moving"] = False
    player["shoot_animation"] = None
    player["explosion"] = {
        "id": canvas.create_image(x, y, image=world["explosion_frames"][0]),
        "frame": 0,
        "next_frame_time": time.time() + EXPLOSION_FRAME_MS / 1000,
    }


# ============================================================================
# Pro Frame: Spieler aktualisieren
# ============================================================================

def read_movement_keys(keys, keys_pressed):
    """
    Macht: Liest die Panzersteuerung eines Spielers aus (vor/zurueck + drehen).
    Input: keys (Tastenbelegung eines Spielers), keys_pressed (Menge aktuell gedrueckter Tasten)
    Output: (forward, backward, turn_left, turn_right) -- alles Bool
    """
    return tuple(keys[direction] in keys_pressed for direction in ("up", "down", "left", "right"))


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
    step = 1 if turn_left else -1
    state["angle"] = ANGLE_STEPS[(ANGLE_STEPS.index(state["angle"]) + step) % len(ANGLE_STEPS)]
    show_tank_image(canvas, player)


def move_tank(world, player, forward, backward, other_players):
    """
    Macht: Bewegt den Panzer in (bei Rueckwaertsfahrt: entgegen) seiner
           Blickrichtung, sofern die Zielposition frei von Baeumen, Wracks und
           anderen lebenden Panzern ist.
    Input: world (Spielfeld-Dict), player, forward, backward (Bool),
           other_players (Liste der uebrigen Spieler)
    Output: (x, y) der neuen Position oder None, falls sich nichts bewegt hat
    """
    player["moving"] = False
    if forward == backward:
        return None  # keine oder beide Tasten gedrueckt -> keine Bewegung

    canvas = world["canvas"]
    vx, vy = ANGLE_TO_VECTOR[player["state"]["angle"]]
    direction = 1 if forward else -1
    x, y = canvas.coords(player["tank"])
    half = player["half_size"]
    new_x = clamp(x + vx * SPEED * direction, half, world["width"] - half)
    new_y = clamp(y + vy * SPEED * direction, half, world["height"] - half)

    blockers = world["trees"] + world["wrecks"] + [tank_circle(canvas, other) for other in other_players if other["alive"]]
    if first_circle_hit(new_x, new_y, TANK_HITBOX_RADIUS, blockers) is not None:
        return None

    canvas.move(player["tank"], new_x - x, new_y - y)
    canvas.move(player["name_tag"], new_x - x, new_y - y)
    player["moving"] = True
    return new_x, new_y


def trigger_mine(world, player, position):
    """
    Macht: Laesst eine Mine hochgehen, wenn der Panzer auf ihr steht: die Mine
           verschwindet und der Panzer wird zerstoert.
    Input: world (Spielfeld-Dict), player (Spieler-Dict), position ((x, y) des Panzers)
    Output: kein Rueckgabewert
    """
    mine = first_circle_hit(position[0], position[1], TANK_HITBOX_RADIUS, world["mines"])
    if mine is None:
        return
    world["canvas"].delete(mine["id"])
    world["mines"].remove(mine)
    destroy_player(world, player)


def break_tree(world, tree):
    """
    Macht: Verwandelt einen getroffenen Baum in einen Baumstumpf, der nicht mehr blockiert.
    Input: world (Spielfeld-Dict), tree (Baum-Dict)
    Output: kein Rueckgabewert
    """
    world["canvas"].itemconfig(tree["id"], image=world["trunk_photo"])
    world["trees"].remove(tree)


def remove_projectile(canvas, player, projectile):
    """
    Macht: Loescht ein Projektil vom Spielfeld und aus der Liste des Spielers.
    Input: canvas, player (Spieler-Dict), projectile (Projektil-Dict)
    Output: kein Rueckgabewert
    """
    canvas.delete(projectile["id"])
    player["projectiles"].remove(projectile)


def update_projectiles(world, player):
    """
    Macht: Bewegt die Projektile eines Spielers weiter. Ein Projektil verschwindet,
           wenn es einen Baum (der dabei umfaellt), ein Wrack (Deckung) trifft
           oder das Spielfeld verlaesst.
    Input: world (Spielfeld-Dict), player (Spieler-Dict)
    Output: kein Rueckgabewert
    """
    canvas = world["canvas"]
    for projectile in player["projectiles"][:]:
        canvas.move(projectile["id"], projectile["dx"] * PROJECTILE_SPEED, projectile["dy"] * PROJECTILE_SPEED)
        box = canvas.coords(projectile["id"])

        tree = first_rect_hit(box, world["trees"])
        if tree is not None:
            break_tree(world, tree)

        left_field = box[2] < 0 or box[0] > world["width"] or box[3] < 0 or box[1] > world["height"]
        if tree is not None or left_field or first_rect_hit(box, world["wrecks"]) is not None:
            remove_projectile(canvas, player, projectile)


def update_shoot_animation(canvas, player):
    """
    Macht: Spielt die Schuss-Animation eines Spielers ab und stellt danach das normale Panzerbild wieder her.
    Input: canvas, player (Spieler-Dict)
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


def update_reload_indicator(canvas, player):
    """
    Macht: Zeigt einen kleinen grauen Ladering neben dem Namensschild, der
           sich fuellt, waehrend der Schuss-Cooldown laeuft, und verschwindet,
           sobald wieder geschossen werden kann.
    Input: canvas, player (Spieler-Dict)
    Output: kein Rueckgabewert
    """
    progress = (time.time() - player["state"]["last_shot_time"]) / SHOOT_COOLDOWN
    if progress >= 1.0:
        canvas.itemconfig(player["reload_ring"], state="hidden")
        return
    canvas.coords(player["reload_ring"], *reload_ring_box(canvas, player["name_tag"]))
    canvas.itemconfig(player["reload_ring"], state="normal", extent=-360 * progress)


def create_wreck(world, position, angle):
    """
    Macht: Legt an der Stelle eines zerstoerten Panzers ein brennendes Wrack ab,
           das ab sofort als Deckung wirkt (blockiert Panzer und Projektile).
    Input: world (Spielfeld-Dict), position ((x, y)), angle (Blickwinkel des Panzers)
    Output: kein Rueckgabewert
    """
    world["wrecks"].append({
        "id": world["canvas"].create_image(*position, image=world["wreck_images"][angle]),
        "cx": position[0],
        "cy": position[1],
        "radius": TANK_HITBOX_RADIUS,
    })


def update_explosion(world, player):
    """
    Macht: Zeigt den naechsten Explosionsframe. Nach dem letzten Frame wird die
           Explosion durch ein Wrack ersetzt.
    Input: world (Spielfeld-Dict), player (Spieler-Dict)
    Output: kein Rueckgabewert
    """
    explosion = player["explosion"]
    if explosion is None or time.time() < explosion["next_frame_time"]:
        return

    canvas = world["canvas"]
    explosion["frame"] += 1
    if explosion["frame"] < len(world["explosion_frames"]):
        canvas.itemconfig(explosion["id"], image=world["explosion_frames"][explosion["frame"]])
        explosion["next_frame_time"] = time.time() + EXPLOSION_FRAME_MS / 1000
        return

    position = canvas.coords(explosion["id"])
    canvas.delete(explosion["id"])
    player["explosion"] = None
    create_wreck(world, position, player["state"]["angle"])


def update_player(world, player, keys_pressed, other_players):
    """
    Macht: Aktualisiert einen Spieler fuer einen Frame: Animationen, Nachlade-Ring,
           Drehung, Bewegung (inkl. Minen) und Projektile.
    Input: world (Spielfeld-Dict), player, keys_pressed (gedrueckte Tasten),
           other_players (uebrige Spieler)
    Output: kein Rueckgabewert
    """
    canvas = world["canvas"]
    update_shoot_animation(canvas, player)
    update_explosion(world, player)
    if not player["alive"]:
        player["moving"] = False
        return

    update_reload_indicator(canvas, player)
    forward, backward, turn_left, turn_right = read_movement_keys(player["keys"], keys_pressed)
    update_rotation(canvas, player, turn_left, turn_right)
    new_position = move_tank(world, player, forward, backward, other_players)
    if new_position is not None:
        trigger_mine(world, player, new_position)
    update_projectiles(world, player)


def check_hits(world, players):
    """
    Macht: Prueft fuer alle Spieler, ob ein Projektil einen gegnerischen Panzer trifft.
    Input: world (Spielfeld-Dict), players (Liste aller Spieler)
    Output: kein Rueckgabewert
    """
    canvas = world["canvas"]
    for shooter in players:
        for projectile in shooter["projectiles"][:]:
            box = canvas.coords(projectile["id"])
            targets = [p for p in players if p is not shooter and p["alive"]]
            target = next((p for p in targets if first_rect_hit(box, [tank_circle(canvas, p)])), None)
            if target is not None:
                destroy_player(world, target)
                remove_projectile(canvas, shooter, projectile)


# ============================================================================
# Ablauf einer Partie
# ============================================================================

def bind_key_tracking(root, keys_pressed):
    """
    Macht: Merkt sich laufend, welche Tasten gerade gedrueckt sind.
    Input: root (Tk-Fenster), keys_pressed (Menge, die aktuell gehalten wird)
    Output: kein Rueckgabewert
    """
    root.bind("<KeyPress>", lambda event: keys_pressed.add(event.keysym.lower()))
    root.bind("<KeyRelease>", lambda event: keys_pressed.discard(event.keysym.lower()))


def stop_match(match):
    """
    Macht: Beendet Eingaben und Sounds einer Partie (gemeinsam fuer Sieg und Leave).
    Input: match (Partie-Dict)
    Output: kein Rueckgabewert
    """
    root = match["root"]
    stop_match_sounds(match["sounds"])
    for player_keys in PLAYER_KEYS.values():
        root.unbind(f"<KeyPress-{player_keys['shoot']}>")
    root.unbind("<KeyPress>")
    root.unbind("<KeyRelease>")


def return_to_menu():
    """
    Macht: Kehrt zur Spielmodus-Auswahl des Menues zurueck.
    Input: keine
    Output: kein Rueckgabewert
    """
    import menu
    menu.mode_menu()


def leave_game(match):
    """
    Macht: Bricht die laufende Partie sofort ab und kehrt ins Menue zurueck.
    Input: match (Partie-Dict)
    Output: kein Rueckgabewert
    """
    if not match["active"]:
        return
    match["active"] = False
    stop_match(match)
    return_to_menu()


def show_result_screen(match, winner_text):
    """
    Macht: Zeigt nach der Pause das Leaderboard/Gewinner-Fenster an.
    Input: match (Partie-Dict), winner_text (Text fuer den Gewinner)
    Output: kein Rueckgabewert
    """
    if not match["active"]:
        return  # Spieler hat die Partie inzwischen ueber Leave verlassen
    root = match["root"]
    show_winner_screen(
        root,
        winner_text,
        get_leaderboard(),
        lambda: run_game(root, match["mode"], match["player_names"]),
        return_to_menu,
    )


def end_match(match, alive_players):
    """
    Macht: Wertet das Spielende aus (Sieg eintragen, Eingaben/Sounds stoppen)
           und zeigt nach einer kurzen Pause das Leaderboard.
    Input: match (Partie-Dict), alive_players (Liste der ueberlebenden Spieler)
    Output: kein Rueckgabewert
    """
    stop_match(match)
    if alive_players:
        winner_text = f"{alive_players[0]['name']} gewinnt!"
        record_win(alive_players[0]["name"])
    else:
        winner_text = "Unentschieden!"
    match["root"].after(WIN_SCREEN_DELAY_MS, show_result_screen, match, winner_text)


def game_loop(match):
    """
    Macht: Fuehrt einen Frame der Partie aus und plant den naechsten Frame.
           Die Partie endet, sobald hoechstens ein Panzer uebrig ist und keine
           Explosion mehr laeuft.
    Input: match (Partie-Dict)
    Output: kein Rueckgabewert
    """
    if not match["active"]:
        return  # Partie wurde ueber den Leave-Button abgebrochen

    world, players = match["world"], match["players"]
    update_ambient_sounds(match["sounds"])
    for player in players:
        update_player(world, player, match["keys_pressed"], [p for p in players if p is not player])
    update_move_sound(match["sounds"], players)
    check_hits(world, players)

    alive_players = [p for p in players if p["alive"]]
    explosions_running = any(p["explosion"] is not None for p in players)
    if len(alive_players) <= 1 and not explosions_running:
        end_match(match, alive_players)
        return
    match["root"].after(DELAY, game_loop, match)


def run_game(root, mode, player_names=None):
    """
    Macht: Startet eine neue Partie: Spielfeld und Spieler aufbauen, Tasten
           und Sounds einrichten und die Spiel-Loop starten.
    Input: root (Tk-Fenster), mode (Spielmodus-String, "1 vs 1" oder "1 vs 1 vs 1"),
           player_names (Liste der vom Menu eingegebenen Spielernamen, optional)
    Output: kein Rueckgabewert
    """
    player_count = len(PLAYER_NUMBERS_BY_MODE[mode])
    if not player_names or len(player_names) < player_count:
        player_names = [f"Spieler {n}" for n in range(1, player_count + 1)]
    register_players(player_names)
    for widget in root.winfo_children():
        widget.destroy()

    world = build_world(root)
    match = {
        "root": root,
        "mode": mode,
        "player_names": player_names,
        "world": world,
        "players": create_players(root, world, mode, player_names),
        "keys_pressed": set(),
        "sounds": start_match_sounds(),
        "active": True,
    }
    bind_key_tracking(root, match["keys_pressed"])

    leave_button = Button(root, text="Leave", bg="lightgray", command=lambda: leave_game(match))
    leave_button.place(relx=0.005, rely=0.01, relwidth=0.1, relheight=0.1)

    game_loop(match)
