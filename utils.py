import os
import sys
### Claude code für weichgezeichneten Hintergrund auf allen Seiten
from functools import lru_cache

from PIL import Image, ImageFilter, ImageTk
### Claude code für weichgezeichneten Hintergrund auf allen Seiten


def resource_path(relative_path):
    """
    Macht: Liefert den vollstaendigen Pfad zu einer Datei aus Assets/ oder Sounds/.
           Als exe (PyInstaller) liegen diese Dateien im temporaeren Entpack-Ordner
           sys._MEIPASS -- diese Variable existiert nur in der gepackten exe.
           Als normales .py-Skript wird der Projektordner genommen (der Ordner
           dieser Datei), damit es auch klappt, wenn das Spiel aus einem anderen
           Ordner gestartet wird.
    Input: relative_path (z.B. "Sounds/Shoot.wav")
    Output: absoluter Pfad als String
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


### Claude code für weichgezeichneten Hintergrund auf allen Seiten
CITY_BACKGROUND_PATH = resource_path("Assets/Map_Street_BG.png")
CITY_BLUR_RADIUS = 9  # Staerke der Weichzeichnung
CITY_DARKEN_AMOUNT = 0.35  # 0 = Originalfarben, 1 = schwarz; dunkler = Text besser lesbar


@lru_cache(maxsize=None)
def blurred_city_image(width, height):
    """
    Macht: Laedt die City-Karte, skaliert sie auf die Fenstergroesse,
           zeichnet sie weich und dunkelt sie leicht ab, damit Titel und
           Buttons darueber gut lesbar bleiben. Das Ergebnis wird
           zwischengespeichert, damit der Seitenwechsel schnell bleibt.
    Input: width, height (Zielgroesse in Pixeln)
    Output: PIL-Bild (darf nicht veraendert werden)
    """
    img = Image.open(CITY_BACKGROUND_PATH).convert("RGB")
    img = img.resize((max(1, width), max(1, height)))
    img = img.filter(ImageFilter.GaussianBlur(CITY_BLUR_RADIUS))
    return Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), CITY_DARKEN_AMOUNT)


def add_blurred_background(canvas, width, height):
    """
    Macht: Legt den weichgezeichneten City-Hintergrund ganz unten auf einen
           Canvas. Das Bild wird am Canvas gespeichert, damit Tkinter es
           nicht wieder loescht.
    Input: canvas (Tk-Canvas), width, height (Groesse in Pixeln)
    Output: kein Rueckgabewert
    """
    canvas.background_img = ImageTk.PhotoImage(blurred_city_image(width, height))
    canvas.create_image(0, 0, anchor="nw", image=canvas.background_img)
### Claude code für weichgezeichneten Hintergrund auf allen Seiten
