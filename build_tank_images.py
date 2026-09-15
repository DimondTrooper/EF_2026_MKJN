"""
Erzeugt aus 2 handgezeichneten Basis-Bildern (0 Grad, 45 Grad) alle 8
Richtungs-Bilder per verlustfreier 90-Grad-Drehung.
 
get_tank_images() gibt ein Dict {winkel: ImageTk.PhotoImage} zurueck,
z.B. {0: ..., 45: ..., 90: ..., ...} -- passt direkt zu ANGLE_STEPS
und tank_images aus der bisherigen game.py.
"""
 
from PIL import Image, ImageTk
 
BASE_STRAIGHT = "Assets/Tank_Blue_Straight.png"  # 0 Grad, zeigt "oben"
BASE_DIAGONAL = "Assets/Tank_Blue_Diagonal.png"  # 45 Grad, zeigt "oben-rechts"
 
SIZE = (50, 50)
 
 
def get_tank_images():
    straight = Image.open(BASE_STRAIGHT)
    straight.thumbnail(SIZE)
 
    diagonal = Image.open(BASE_DIAGONAL)
    diagonal.thumbnail(SIZE)
 
    tank_images = {}
 
    # aus dem geraden Basis-Bild: 0, 90, 180, 270
    for step in (0, 90, 180, 270):
        rotated = straight.rotate(-step, expand=True)
        tank_images[step] = ImageTk.PhotoImage(rotated)
 
    # aus dem diagonalen Basis-Bild: 45, 135, 225, 315
    for step in (0, 90, 180, 270):
        rotated = diagonal.rotate(-step, expand=True)
        tank_images[45 + step] = ImageTk.PhotoImage(rotated)
 
    return tank_images
 
 
if __name__ == "__main__":
    # Testlauf: nur zum Pruefen, ob alle 8 Bilder ohne Fehler entstehen
    import tkinter as tk
 
    root = tk.Tk()
    images = get_tank_images()
    for angle in sorted(images):
        print(angle, "Grad ->", images[angle].width(), "x", images[angle].height())
    root.destroy()