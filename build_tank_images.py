"""
Erzeugt aus 2 handgezeichneten Basis-Bildern (0 Grad, 45 Grad) alle 8
Richtungs-Bilder per verlustfreier 90-Grad-Drehung.
 
get_tank_images() gibt ein Dict {winkel: ImageTk.PhotoImage} zurueck,
z.B. {0: ..., 45: ..., 90: ..., ...} -- passt direkt zu ANGLE_STEPS
und tank_images aus der bisherigen game.py.
"""
 
import math

from PIL import Image, ImageTk

BASE_STRAIGHT = "Assets/Tank_Blue_Straight.png"  # 0 Grad, zeigt "oben"
BASE_DIAGONAL = "Assets/Tank_Blue_Diagonal.png"  # 45 Grad, zeigt "oben-rechts"

# Zielbreite des Panzer-RUMPFES (ohne Rohr) in Pixeln. Die beiden Basis-Bilder
# sind nicht im selben Massstab gezeichnet -- der Rumpf im geraden Bild ist
# rund 1.6x so gross (relativ zur Bildgroesse) wie im diagonalen Bild. Nur auf
# dieselbe Bounding-Box zu skalieren (frueherer Ansatz) liess den Rumpf beim
# Drehen dadurch sichtbar schrumpfen/wachsen. Stattdessen wird die tatsaech-
# liche Rumpfbreite pro Bild gemessen und individuell so skaliert, dass der
# Rumpf am Ende ueberall gleich gross ist.
HULL_PX = 44


def _hull_reference_width(img):
    """Groesste horizontale Ausdehnung der undurchsichtigen Pixel ueber alle
    Zeilen. Bei einem gerade ausgerichteten Bild entspricht das direkt der
    Rumpfbreite, bei einem um 45 Grad gedrehten Bild der Rumpfbreite * sqrt(2)
    (Diagonale eines um 45 Grad gedrehten Quadrats)."""
    alpha = img.split()[-1]
    w, h = alpha.size
    max_width = 0
    for y in range(h):
        bbox = alpha.crop((0, y, w, y + 1)).getbbox()
        if bbox:
            max_width = max(max_width, bbox[2] - bbox[0])
    return max_width


def _load_scaled(path, rotated_45):
    img = Image.open(path).convert("RGBA")
    hull_width = _hull_reference_width(img)
    if rotated_45:
        hull_width /= math.sqrt(2)
    scale = HULL_PX / hull_width
    new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(new_size, Image.LANCZOS)


def _center_on_square(img, size):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    canvas.paste(img, offset, img)
    return canvas


def get_tank_images():
    straight = _load_scaled(BASE_STRAIGHT, rotated_45=False)
    diagonal = _load_scaled(BASE_DIAGONAL, rotated_45=True)

    # gemeinsame quadratische Leinwand, gross genug fuer beide Bilder samt
    # Rohr, damit beim Zentrieren nichts abgeschnitten wird
    size = max(straight.width, straight.height, diagonal.width, diagonal.height) + 4
    straight = _center_on_square(straight, size)
    diagonal = _center_on_square(diagonal, size)

    tank_images = {}
 
    # aus dem geraden Basis-Bild: 0, 90, 180, 270
    for step in (0, 90, 180, 270):
        rotated = straight.rotate(step, expand=True)
        tank_images[step] = ImageTk.PhotoImage(rotated)

    # aus dem diagonalen Basis-Bild (zeigt unrotiert "oben-rechts" = Winkel 315): 315, 45, 135, 225
    for step in (0, 90, 180, 270):
        rotated = diagonal.rotate(step, expand=True)
        tank_images[(315 + step) % 360] = ImageTk.PhotoImage(rotated)
 
    return tank_images
 
 
if __name__ == "__main__":
    # Testlauf: nur zum Pruefen, ob alle 8 Bilder ohne Fehler entstehen
    import tkinter as tk
 
    root = tk.Tk()
    images = get_tank_images()
    for angle in sorted(images):
        print(angle, "Grad ->", images[angle].width(), "x", images[angle].height())
    root.destroy()