import math
import os

from PIL import Image, ImageTk

TANK_BASE_PATHS = {
    "blue": ("Assets/Tank_Blue_Straight.png", "Assets/Tank_Blue_Diagonal.png"),
    "red": ("Assets/Tank_Red_Straight.png", "Assets/Tank_Red_Diagonal.png"),
    "green": ("Assets/Tank_Green_Straight.png", "Assets/Tank_Green_Diagonal.png"),
}

MUZZLE_FLASH_DIR = "Assets/Tank_Shoot_animation"
MUZZLE_FLASH_FRAME_COUNT = 3

HULL_PX = 44


def _hull_reference_width(img):
    """
    Macht: Ermittelt die Referenzbreite des Panzer-Rumpfes im Bild.
    Input: img (PIL-Bild)
    Output: Zahl (Pixel-Breite)
    """
    alpha = img.split()[-1]
    w, h = alpha.size
    max_width = 0
    for y in range(h):
        bbox = alpha.crop((0, y, w, y + 1)).getbbox()
        if bbox:
            max_width = max(max_width, bbox[2] - bbox[0])
    return max_width


def _load_scaled(path, rotated_45):
    """
    Macht: Laedt ein Basisbild und skaliert es auf eine einheitliche Rumpfgroesse.
    Input: path (Dateipfad zu einem Basisbild), rotated_45 (Bool, ob 45-Grad-Basisbild)
    Output: PIL-Bild
    """
    img = Image.open(path).convert("RGBA")
    hull_width = _hull_reference_width(img)
    if rotated_45:
        hull_width /= math.sqrt(2)
    scale = HULL_PX / hull_width
    new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(new_size, Image.LANCZOS)


def _center_on_square(img, size):
    """
    Macht: Zentriert ein Bild auf einer quadratischen, transparenten Flaeche.
    Input: img (PIL-Bild), size (Zielgroesse in Pixeln)
    Output: PIL-Bild (quadratisch, size x size)
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    canvas.paste(img, offset, img)
    return canvas


def _build_angle_set(base_straight_path, base_diagonal_path, target_size=None):
    """
    Macht: Baut aus einem geraden und einem 45-Grad-Basisbild alle 8 Drehwinkel.
    Input: base_straight_path, base_diagonal_path (Dateipfade zu den Basisbildern),
           target_size (optional: erzwungene quadratische Endgroesse in Pixeln,
           z.B. damit ein Wrack gleich gross wie die vorangehende Explosion wirkt)
    Output: Dict {winkel: ImageTk.PhotoImage}
    """
    straight = _load_scaled(base_straight_path, rotated_45=False)
    diagonal = _load_scaled(base_diagonal_path, rotated_45=True)

    size = max(straight.width, straight.height, diagonal.width, diagonal.height) + 4
    straight = _center_on_square(straight, size)
    diagonal = _center_on_square(diagonal, size)

    if target_size is not None and target_size != size:
        straight = straight.resize((target_size, target_size), Image.LANCZOS)
        diagonal = diagonal.resize((target_size, target_size), Image.LANCZOS)

    images = {}
    for step in (0, 90, 180, 270):
        images[step] = ImageTk.PhotoImage(straight.rotate(step, expand=True))
    for step in (0, 90, 180, 270):
        images[(315 + step) % 360] = ImageTk.PhotoImage(diagonal.rotate(step, expand=True))
    return images


def get_tank_images(color="blue"):
    """
    Macht: Erzeugt alle 8 Drehwinkel-Bilder eines Panzers in der gewuenschten Farbe.
    Input: color (Panzerfarbe, z.B. "blue", "red", "green")
    Output: Dict {winkel: ImageTk.PhotoImage}
    """
    base_straight, base_diagonal = TANK_BASE_PATHS[color]
    return _build_angle_set(base_straight, base_diagonal)


DESTROYED_TANK_BASE_PATHS = (
    "Assets/Tank_Destroyed_animation/Tank_Destroyed_Straight.png",
    "Assets/Tank_Destroyed_animation/Tank_Destroyed_Diagonal.png",
)


def get_destroyed_tank_images(target_size=None):
    """
    Macht: Erzeugt alle 8 Drehwinkel-Bilder des liegenbleibenden Panzer-Wracks
           (dasselbe Wrack-Bild fuer alle Farben).
    Input: target_size (optional: erzwungene quadratische Endgroesse in Pixeln,
           damit das Wrack beim Erscheinen gleich gross wirkt wie die
           vorangehende Explosion und nicht ploetzlich kleiner wird)
    Output: Dict {winkel: ImageTk.PhotoImage}
    """
    base_straight, base_diagonal = DESTROYED_TANK_BASE_PATHS
    return _build_angle_set(base_straight, base_diagonal, target_size=target_size)


def _muzzle_flash_path(color, orientation, frame_number):
    return f"{MUZZLE_FLASH_DIR}/Tank_{color.capitalize()}_{orientation}_Mussleflash{frame_number}.png"


def _resolve_muzzle_flash_path(color, orientation, frame_number):
    """
    Macht: Findet den Pfad zu einem Muendungsfeuer-Frame; fehlt genau dieser
           Frame (z.B. Tank_Red_Diagonal_Mussleflash2.png), wird ersatzweise
           der naechstliegende vorhandene Frame verwendet.
    Input: color, orientation ("Straight"/"Diagonal"), frame_number (1..3)
    Output: Dateipfad (String)
    """
    path = _muzzle_flash_path(color, orientation, frame_number)
    if os.path.exists(path):
        return path
    for fallback_number in (2, 1, 3):
        fallback_path = _muzzle_flash_path(color, orientation, fallback_number)
        if os.path.exists(fallback_path):
            return fallback_path
    raise FileNotFoundError(f"Kein Muendungsfeuer-Bild fuer {color}/{orientation} gefunden")


def get_muzzle_flash_frames(color="blue"):
    """
    Macht: Erzeugt fuer jeden der 8 Drehwinkel die 3 Muendungsfeuer-Frames
           (kompletter Panzer inkl. Feuer am Rohr), im selben Massstab wie
           die normalen Panzerbilder von get_tank_images().
    Input: color (Panzerfarbe, z.B. "blue", "red", "green")
    Output: Dict {winkel: Liste von MUZZLE_FLASH_FRAME_COUNT ImageTk.PhotoImage}
    """
    base_straight, base_diagonal = TANK_BASE_PATHS[color]
    straight_bases = [
        _load_scaled(_resolve_muzzle_flash_path(color, "Straight", n), rotated_45=False)
        for n in range(1, MUZZLE_FLASH_FRAME_COUNT + 1)
    ]
    diagonal_bases = [
        _load_scaled(_resolve_muzzle_flash_path(color, "Diagonal", n), rotated_45=True)
        for n in range(1, MUZZLE_FLASH_FRAME_COUNT + 1)
    ]

    normal_straight = _load_scaled(base_straight, rotated_45=False)
    normal_diagonal = _load_scaled(base_diagonal, rotated_45=True)
    size = max(
        normal_straight.width, normal_straight.height,
        normal_diagonal.width, normal_diagonal.height,
        *(max(frame.width, frame.height) for frame in straight_bases + diagonal_bases),
    ) + 4
    straight_bases = [_center_on_square(frame, size) for frame in straight_bases]
    diagonal_bases = [_center_on_square(frame, size) for frame in diagonal_bases]

    frames_by_angle = {}
    for step in (0, 90, 180, 270):
        frames_by_angle[step] = [
            ImageTk.PhotoImage(base.rotate(step, expand=True)) for base in straight_bases
        ]
    for step in (0, 90, 180, 270):
        frames_by_angle[(315 + step) % 360] = [
            ImageTk.PhotoImage(base.rotate(step, expand=True)) for base in diagonal_bases
        ]

    return frames_by_angle


if __name__ == "__main__":
    import tkinter as tk

    root = tk.Tk()
    images = get_tank_images()
    for angle in sorted(images):
        print(angle, "Grad ->", images[angle].width(), "x", images[angle].height())
    root.destroy()
