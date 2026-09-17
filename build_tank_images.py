import math

from PIL import Image, ImageTk

from utils import resource_path

TANK_BASE_PATHS = {
    "blue": (resource_path("Assets/Tank_Blue_Straight.png"), resource_path("Assets/Tank_Blue_Diagonal.png")),
    "red": (resource_path("Assets/Tank_Red_Straight.png"), resource_path("Assets/Tank_Red_Diagonal.png")),
    "green": (resource_path("Assets/Tank_Green_Straight.png"), resource_path("Assets/Tank_Green_Diagonal.png")),
}

MUZZLE_FLASH_DIR = resource_path("Assets/Tank_Shoot_animation")
MUZZLE_FLASH_FRAME_COUNT = 3

HULL_PX = 44  #einheitliche Rumpfbreite aller Panzerbilder im Spiel
HULL_ROW_THRESHOLD = 0.6  #ab welchem Anteil der breitesten Zeile eine Zeile als Rumpf zaehlt

#Aus einem geraden (0 Grad) und einem diagonalen (315 Grad) Basisbild entstehen
#durch Drehen um 90-Grad-Schritte alle 8 Blickwinkel.
QUARTER_TURNS = (0, 90, 180, 270)
DIAGONAL_BASE_ANGLE = 315


def _row_spans(img):
    """
    Macht: Misst fuer jede Bildzeile, wie breit der undurchsichtige Bereich ist.
    Input: img (PIL-Bild)
    Output: Liste von (breite, x_links, x_rechts) pro Zeile
    """
    alpha = img.split()[-1]
    w, h = alpha.size
    spans = []
    for y in range(h):
        bbox = alpha.crop((0, y, w, y + 1)).getbbox()
        spans.append((bbox[2] - bbox[0], bbox[0], bbox[2]) if bbox else (0, 0, 0))
    return spans


def _hull_box(img):
    """
    Macht: Findet den Panzer-RUMPF in einem GERADE ausgerichteten Bild, also
           ohne Rohr und ohne Muendungsfeuer. Der Rumpf ist der laengste
           zusammenhaengende Block breiter Zeilen; Rohr und Flamme sind
           schmaler und fallen dadurch heraus.
    Input: img (PIL-Bild, Panzer zeigt nach oben)
    Output: (x_links, y_oben, x_rechts, y_unten) des Rumpfes
    """
    spans = _row_spans(img)
    max_width = max(span[0] for span in spans)
    threshold = HULL_ROW_THRESHOLD * max_width

    best = current = None
    for y, span in enumerate(spans):
        if span[0] >= threshold:
            current = (y, y) if current is None else (current[0], y)
            if best is None or current[1] - current[0] > best[1] - best[0]:
                best = current
        else:
            current = None
    top, bottom = best
    widest_y = max(range(top, bottom + 1), key=lambda y: spans[y][0])
    return (spans[widest_y][1], top, spans[widest_y][2], bottom)


def _hull_metrics(img, rotated_45):
    """
    Macht: Liefert Mittelpunkt und Breite des Panzer-Rumpfes.
           Der Mittelpunkt ist der Punkt, um den sich der Panzer beim Drehen
           drehen soll. Bei einem 45-Grad-Bild ist der Rumpf eine Raute, in
           der sich Rumpf und Rohr zeilenweise schlecht trennen lassen.
           Deshalb wird das Bild zum MESSEN kurz gerade gedreht (dort greift
           die zuverlaessige Rechteck-Erkennung) und das Ergebnis danach in
           die Koordinaten des Originalbildes zurueckgerechnet. Das
           Originalbild selbst bleibt unangetastet, wird also nicht unscharf.
    Input: img (PIL-Bild), rotated_45 (Bool, ob 45-Grad-Basisbild)
    Output: (mitte_x, mitte_y, rumpfbreite)
    """
    if not rotated_45:
        left, top, right, bottom = _hull_box(img)
        return ((left + right) / 2, (top + bottom) / 2, right - left)

    #+45 Grad richtet das Basisbild (Panzer zeigt nach rechts-oben) gerade aus
    angle = 45
    straightened = img.rotate(angle, expand=True, resample=Image.BICUBIC)
    left, top, right, bottom = _hull_box(straightened)
    dx = (left + right) / 2 - straightened.width / 2
    dy = (top + bottom) / 2 - straightened.height / 2

    #inverse Drehung: zurueck in die Koordinaten des Originalbildes
    theta = math.radians(angle)
    ox = dx * math.cos(theta) - dy * math.sin(theta)
    oy = dx * math.sin(theta) + dy * math.cos(theta)
    return (img.width / 2 + ox, img.height / 2 + oy, right - left)


def _hull_center(img, rotated_45):
    """
    Macht: Liefert nur den Rumpf-Mittelpunkt (siehe _hull_metrics).
    Input: img (PIL-Bild), rotated_45 (Bool)
    Output: (x, y)
    """
    cx, cy, _ = _hull_metrics(img, rotated_45)
    return (cx, cy)


def _load_scaled(path, rotated_45):
    """
    Macht: Laedt ein Basisbild und skaliert es auf eine einheitliche Rumpfgroesse.
           Gemessen wird nur der Rumpf, damit ein Muendungsfeuer das Bild nicht
           faelschlich kleiner skaliert.
    Input: path (Dateipfad zu einem Basisbild), rotated_45 (Bool, ob 45-Grad-Basisbild)
    Output: PIL-Bild
    """
    img = Image.open(path).convert("RGBA")
    _, _, hull_width = _hull_metrics(img, rotated_45)
    scale = HULL_PX / hull_width
    new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(new_size, Image.LANCZOS)


def _square_size_for(images):
    """
    Macht: Berechnet die noetige quadratische Bildgroesse, damit nach dem
           Zentrieren auf den Rumpf nichts abgeschnitten wird.
    Input: images (Liste von (PIL-Bild, rotated_45))
    Output: Kantenlaenge in Pixeln
    """
    half = 0
    for img, rotated_45 in images:
        cx, cy = _hull_center(img, rotated_45)
        bbox = img.split()[-1].getbbox()
        half = max(half, cx - bbox[0], bbox[2] - cx, cy - bbox[1], bbox[3] - cy)
    return int(math.ceil(half)) * 2 + 4


def _center_hull_on_square(img, size, rotated_45):
    """
    Macht: Legt das Bild so auf eine quadratische Flaeche, dass der RUMPF-
           Mittelpunkt genau in der Bildmitte liegt. Dadurch dreht sich der
           Panzer beim Wechsel der Drehstufen auf der Stelle, statt um einen
           Punkt vor dem Rumpf zu kreisen.
    Input: img (PIL-Bild), size (Kantenlaenge), rotated_45 (Bool)
    Output: PIL-Bild (quadratisch, size x size)
    """
    cx, cy = _hull_center(img, rotated_45)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(img, (round(size / 2 - cx), round(size / 2 - cy)), img)
    return canvas


def _all_angles(straight, diagonal):
    """
    Macht: Dreht ein fertig zentriertes gerades und diagonales Bild in alle
           8 Blickwinkel.
    Input: straight, diagonal (quadratische PIL-Bilder)
    Output: Dict {winkel: ImageTk.PhotoImage}
    """
    images = {}
    for step in QUARTER_TURNS:
        images[step] = ImageTk.PhotoImage(straight.rotate(step, expand=True))
        images[(DIAGONAL_BASE_ANGLE + step) % 360] = ImageTk.PhotoImage(diagonal.rotate(step, expand=True))
    return images


def get_tank_images(color="blue"):
    """
    Macht: Erzeugt alle 8 Drehwinkel-Bilder eines Panzers in der gewuenschten Farbe.
    Input: color (Panzerfarbe, z.B. "blue", "red", "green")
    Output: Dict {winkel: ImageTk.PhotoImage}
    """
    base_straight, base_diagonal = TANK_BASE_PATHS[color]
    straight = _load_scaled(base_straight, rotated_45=False)
    diagonal = _load_scaled(base_diagonal, rotated_45=True)

    size = _square_size_for([(straight, False), (diagonal, True)])
    return _all_angles(
        _center_hull_on_square(straight, size, rotated_45=False),
        _center_hull_on_square(diagonal, size, rotated_45=True),
    )


DESTROYED_DIR = resource_path("Assets/Tank_Destroyed_animation")
DESTROYED_FRAME = 1  #die Wrack-Animation ist abgeschaltet; es wird nur dieses Bild benutzt

#Fuer das brennende Wrack gibt es zu jedem der 8 Blickwinkel eine eigene
#Zeichnung (der Rauch steigt immer nach oben und laesst sich deshalb nicht
#einfach mitdrehen). Die Namen entsprechen der Winkel-Konvention aus game.py:
#0 = nach oben, 45 = nach links-oben, 90 = nach links usw.
DESTROYED_ANGLE_NAMES = {
    0: "Straight", 45: "Diagonalleft", 90: "Left", 135: "Downleft",
    180: "Down", 225: "Downright", 270: "Right", 315: "Diagonal",
}

#Der dicke Rauch macht die uebliche Rumpferkennung unbrauchbar -- er ist voll
#deckend und ueberlappt den Rumpf. Stattdessen
#dient das FEUER als Ankerpunkt: es ist farblich eindeutig (warme Toene, die
#im Rauch nicht vorkommen) und in allen Richtungen an derselben
#Stelle des Panzers gezeichnet.
#Beide Werte wurden an den Originaldateien ausgemessen (Richtungen, in denen
#der Rauch den Rumpf nicht ueberdeckt: Downleft/Down/Downright):
DESTROYED_SOURCE_HULL_PX = 200  #Rumpfbreite in den Originaldateien
DESTROYED_FIRE_TO_HULL_PX = 90  #das Feuer sitzt am Heck; so weit liegt die Rumpfmitte davor
FIRE_SAMPLE_STEP = 3  #nur jedes n-te Pixel pruefen -- schnell genug und genau genug


def _forward_vector(angle):
    """
    Macht: Liefert die Blickrichtung eines Winkels als Vektor in Bildkoordinaten
           (gleiche Konvention wie ANGLE_TO_VECTOR in game.py).
    Input: angle (0, 45, ... 315)
    Output: (x, y)
    """
    rad = math.radians(angle)
    return (-math.sin(rad), -math.cos(rad))


def _fire_center(img):
    """
    Macht: Findet den Schwerpunkt der Feuer-Pixel (warme, kraeftige Farbtoene).
           Der Rauch ist neutralgrau und wird dadurch sicher ausgeschlossen.
    Input: img (PIL-Bild des Wracks)
    Output: (x, y) oder None, falls kein Feuer gefunden wurde
    """
    pixels = img.load()
    width, height = img.size
    sum_x = sum_y = count = 0
    for y in range(0, height, FIRE_SAMPLE_STEP):
        for x in range(0, width, FIRE_SAMPLE_STEP):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 200 and red > 120 and red - blue > 60 and red >= green:
                sum_x += x
                sum_y += y
                count += 1
    if not count:
        return None
    return (sum_x / count, sum_y / count)


def _destroyed_image_path(angle):
    """
    Macht: Baut den Dateipfad zum Wrack-Bild eines Blickwinkels.
    Input: angle (Blickwinkel)
    Output: Dateipfad (String)
    """
    return f"{DESTROYED_DIR}/Tank_Destroyed_{DESTROYED_ANGLE_NAMES[angle]}{DESTROYED_FRAME}.png"


def get_destroyed_tank_images():
    """
    Macht: Laedt das Bild des brennenden Wracks fuer jeden der 8 Blickwinkel.
           Die Bilder werden am Feuer ausgerichtet, damit das Wrack ungefaehr
           dort liegt, wo der Panzer zerstoert wurde.
    Input: keine
    Output: Dict {winkel: ImageTk.PhotoImage}
    """
    scale = HULL_PX / DESTROYED_SOURCE_HULL_PX
    prepared = {}
    half = 0

    for angle in DESTROYED_ANGLE_NAMES:
        forward_x, forward_y = _forward_vector(angle)
        img = Image.open(_destroyed_image_path(angle)).convert("RGBA")
        fire = _fire_center(img)
        if fire is None:  #Notfalls die Bildmitte nehmen, statt abzustuerzen
            fire = (img.width / 2, img.height / 2)
        anchor_x = (fire[0] + DESTROYED_FIRE_TO_HULL_PX * forward_x) * scale
        anchor_y = (fire[1] + DESTROYED_FIRE_TO_HULL_PX * forward_y) * scale

        scaled = img.resize(
            (max(1, round(img.width * scale)), max(1, round(img.height * scale))),
            Image.LANCZOS,
        )
        bbox = scaled.split()[-1].getbbox()
        half = max(half, anchor_x - bbox[0], bbox[2] - anchor_x,
                   anchor_y - bbox[1], bbox[3] - anchor_y)
        prepared[angle] = (scaled, anchor_x, anchor_y)

    size = int(math.ceil(half)) * 2 + 4
    images = {}
    for angle, (scaled, anchor_x, anchor_y) in prepared.items():
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.paste(scaled, (round(size / 2 - anchor_x), round(size / 2 - anchor_y)), scaled)
        images[angle] = ImageTk.PhotoImage(canvas)
    return images


def _muzzle_flash_path(color, orientation, frame_number):
    """
    Macht: Baut den Dateipfad zu einem Muendungsfeuer-Frame.
    Input: color (Panzerfarbe), orientation ("Straight"/"Diagonal"), frame_number (1..3)
    Output: Dateipfad (String)
    """
    return f"{MUZZLE_FLASH_DIR}/Tank_{color.capitalize()}_{orientation}_Mussleflash{frame_number}.png"


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
        _load_scaled(_muzzle_flash_path(color, "Straight", n), rotated_45=False)
        for n in range(1, MUZZLE_FLASH_FRAME_COUNT + 1)
    ]
    diagonal_bases = [
        _load_scaled(_muzzle_flash_path(color, "Diagonal", n), rotated_45=True)
        for n in range(1, MUZZLE_FLASH_FRAME_COUNT + 1)
    ]

    normal_straight = _load_scaled(base_straight, rotated_45=False)
    normal_diagonal = _load_scaled(base_diagonal, rotated_45=True)
    #auch hier wird auf den Rumpf zentriert -- dadurch sitzt der Rumpf in
    #jedem Frame an derselben Stelle wie im normalen Panzerbild und der
    #Panzer springt beim Schuss nicht.
    size = _square_size_for(
        [(normal_straight, False), (normal_diagonal, True)]
        + [(frame, False) for frame in straight_bases]
        + [(frame, True) for frame in diagonal_bases]
    )
    frames = [
        _all_angles(
            _center_hull_on_square(straight, size, rotated_45=False),
            _center_hull_on_square(diagonal, size, rotated_45=True),
        )
        for straight, diagonal in zip(straight_bases, diagonal_bases)
    ]
    return {angle: [frame[angle] for frame in frames] for angle in frames[0]}
