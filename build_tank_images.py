import math

from PIL import Image, ImageTk

TANK_BASE_PATHS = {
    "blue": ("Assets/Tank_Blue_Straight.png", "Assets/Tank_Blue_Diagonal.png"),
    "red": ("Assets/Tank_Red_Straight.png", "Assets/Tank_Red_Diagonal.png"),
    "green": ("Assets/Tank_Green_Straight.png", "Assets/Tank_Green_Diagonal.png"),
}

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


def get_tank_images(color="blue"):
    """
    Macht: Erzeugt alle 8 Drehwinkel-Bilder eines Panzers in der gewuenschten Farbe.
    Input: color (Panzerfarbe, z.B. "blue", "red", "green")
    Output: Dict {winkel: ImageTk.PhotoImage}
    """
    base_straight, base_diagonal = TANK_BASE_PATHS[color]
    straight = _load_scaled(base_straight, rotated_45=False)
    diagonal = _load_scaled(base_diagonal, rotated_45=True)

    size = max(straight.width, straight.height, diagonal.width, diagonal.height) + 4
    straight = _center_on_square(straight, size)
    diagonal = _center_on_square(diagonal, size)

    tank_images = {}

    for step in (0, 90, 180, 270):
        rotated = straight.rotate(step, expand=True)
        tank_images[step] = ImageTk.PhotoImage(rotated)

    for step in (0, 90, 180, 270):
        rotated = diagonal.rotate(step, expand=True)
        tank_images[(315 + step) % 360] = ImageTk.PhotoImage(rotated)

    return tank_images


if __name__ == "__main__":
    import tkinter as tk

    root = tk.Tk()
    images = get_tank_images()
    for angle in sorted(images):
        print(angle, "Grad ->", images[angle].width(), "x", images[angle].height())
    root.destroy()
