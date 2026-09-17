### Claude code für problem bei rückgehen von menu nach spiel
import sys
sys.modules.setdefault('menu', sys.modules[__name__])
### Claude code für problem bei rückgehen von menu nach spiel

from tkinter import *
import game
import ctypes
from utils import resource_path
### Claude code für weichgezeichneten Hintergrund auf allen Seiten
from utils import add_blurred_background

TITLE_FONT = ('Calibri', 20, 'bold')
### Claude code für weichgezeichneten Hintergrund auf allen Seiten

### Claude code für neue Homescreen-Panzer
from PIL import Image, ImageTk

#Beide Panzer sind im gleichen Massstab gezeichnet (gleich lange Ketten); das
#blaue Bild ist nur wegen Rohr und Muendungsfeuer groesser. Darum werden beide
#mit DEMSELBEN Faktor skaliert -- so sind die Panzer selbst gleich gross.
HOMESCREEN_TANK_MAX_WIDTH = 0.36  #das breiteste Bild wird hoechstens so breit (Anteil der Fensterbreite)
HOMESCREEN_TANK_MAX_HEIGHT = 0.31  #das hoechste Bild wird hoechstens so hoch (Anteil der Fensterhoehe)
HOMESCREEN_TANK_MARGIN = 0.02  #Abstand zum linken bzw. rechten Fensterrand (Anteil der Breite)
HOMESCREEN_GROUND_Y = 0.68  #Hoehe, auf der beide Panzer "stehen" (Anteil der Fensterhoehe)


def load_images_same_scale(paths, max_width, max_height):
    """
    Macht: Laedt mehrere Bilder und skaliert alle weich mit demselben Faktor,
           sodass das breiteste hoechstens max_width und das hoechste
           hoechstens max_height misst. Die Groessenverhaeltnisse zwischen
           den Bildern bleiben dadurch erhalten.
    Input: paths (Liste von Dateipfaden), max_width, max_height (in Pixeln)
    Output: Liste von ImageTk.PhotoImage (gleiche Reihenfolge wie paths)
    """
    images = [Image.open(path).convert('RGBA') for path in paths]
    scale = min(max_width / max(img.width for img in images),
                max_height / max(img.height for img in images))
    return [
        ImageTk.PhotoImage(img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS))
        for img in images
    ]
### Claude code für neue Homescreen-Panzer

### Claude code für weichgezeichneten Hintergrund auf allen Seiten


def create_background_canvas(frame):
    """
    Macht: Legt einen Canvas mit dem weichgezeichneten City-Hintergrund
           ueber die ganze Seite. Alles, was danach im Frame platziert wird,
           liegt darueber.
    Input: frame (Frame) - Das Frame der aktuellen Seite
    Output: (Canvas, Breite, Hoehe)
    """
    #update_idletasks() ist noetig, weil root.winfo_width()/height() direkt
    #nach dem Setzen von -fullscreen sonst noch die alte Fenstergroesse liefert
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    bg_canvas = Canvas(frame, width=width, height=height, highlightthickness=0, bd=0, bg='#3f5c3f')
    bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
    add_blurred_background(bg_canvas, width, height)
    return bg_canvas, width, height
### Claude code für weichgezeichneten Hintergrund auf allen Seiten

def mode_menu():
    """
    Macht: Zeigt das Hauptmenü an, auf dem der Spieler den Spielmodus (1 vs 1 
           oder 1 vs 1 vs 1) auswählen kann, inklusive Hintergrund und Menü-Buttons.
    Input: Keine
    Output: Keine (aktualisiert das Tkinter-Fenster)
    """
    #clear old widgets->feels like switching
    for widget in root.winfo_children():
        widget.destroy()

    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

    ### Claude code für weichgezeichneten City-Hintergrund im Menu
    bg_canvas, width, height = create_background_canvas(frame)

    #title,desc
    bg_canvas.create_text(width * 0.5, height * 0.225, text='TNK-XTREME',
                          fill='white', font=('Calibri', 28, 'bold'))
    bg_canvas.create_text(width * 0.5, height * 0.4, text='Choose battle mode to play:',
                          fill='white', font=('Calibri', 14))

    #-DECORATIVE SIDE TANKS-
    ### Claude code für neue Homescreen-Panzer
    #blau links schiesst nach rechts, rot rechts schaut nach links -> sie stehen sich gegenueber
    global tank_left_img, tank_right_img
    tank_left_img, tank_right_img = load_images_same_scale(
        [resource_path('Assets/Tank_Blue_Homescreen.png'), resource_path('Assets/Tank_Red_Homescreen.png')],
        width * HOMESCREEN_TANK_MAX_WIDTH, height * HOMESCREEN_TANK_MAX_HEIGHT,
    )
    #an den unteren Ecken ausrichten: beide Ketten stehen auf derselben Linie
    ground_y = height * HOMESCREEN_GROUND_Y
    bg_canvas.create_image(width * HOMESCREEN_TANK_MARGIN, ground_y, image=tank_left_img, anchor='sw')
    bg_canvas.create_image(width * (1 - HOMESCREEN_TANK_MARGIN), ground_y, image=tank_right_img, anchor='se')
    ### Claude code für neue Homescreen-Panzer
    ### Claude code für weichgezeichneten City-Hintergrund im Menu
 
    #button for mode1(string->controls screen)
    btn_1=Button(frame, text='1 VS 1 Mode', bg='lightgreen', command=lambda: controls_screen('1 vs 1'))
    btn_1.place(relx=0.4, rely=0.5, relwidth=0.2, relheight=0.1)
 
    #btn for mode2
    btn_2=Button(frame, text='1 VS 1 VS 1 Mode', bg='lightblue', command=lambda: controls_screen('1 vs 1 vs 1'))
    btn_2.place(relx=0.4, rely=0.65, relwidth=0.2, relheight=0.1)

def player_box(frame, x_pos, title_text, controls_text, tank_img=None):
    """
    Macht: Erstellt eine UI-Box für die Steuerungserklärung eines einzelnen Spielers,
           inklusive Titel, Tastenbelegung und zugehörigem Panzerbild.
    Input: frame (Frame) - Das übergeordnete Fenster-Frame
           x_pos (float) - Die horizontale Position (relx) der Box
           title_text (str) - Der Titel der Box (z.B. 'Controls Player 1')
           controls_text (str) - Der Text mit der Tastenbelegung
           tank_img (PhotoImage) - Das Bild des jeweiligen Panzers
    Output: Keine (platziert die Box auf dem Frame)
    """
    box=Frame(frame, bd=2, relief=GROOVE)
    box.place(relx=x_pos, rely=0.18, relwidth=0.23, relheight=0.45)
    lbl_title=Label(box, text=title_text, font=('Calibri', 14, 'bold'))
    lbl_title.pack(pady=10)
    lbl_body=Label(box, text=controls_text, font=('Calibri', 11), justify=LEFT)
    lbl_body.pack(padx=10, anchor='w')
    if tank_img:
        Label(box, image=tank_img).pack(pady=(25, 0))
 
def controls_screen(mode):
    """
    Macht: Baut den Steuerungsbildschirm auf, zeigt die Tastenbelegungen für 
           alle Spieler an und lädt die entsprechenden Tank-Grafiken.
    Input: mode (str) - Der ausgewählte Spielmodus ('1 vs 1' oder '1 vs 1 vs 1')
    Output: Keine (aktualisiert das Tkinter-Fenster)
    """
    #d previous frame
    for widget in root.winfo_children():
        widget.destroy()

    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten
    bg_canvas, width, height = create_background_canvas(frame)
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten

    #check selected mode(->change text header)
    if mode == '1 vs 1':
        text_mode='1 vs 1 Controls'
    else:
        text_mode='1 vs 1 vs 1 Controls'
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten
    #Titel direkt auf den Hintergrund schreiben (ein Label haette einen grauen Kasten)
    bg_canvas.create_text(width * 0.5, height * 0.1, text=text_mode, fill='white', font=TITLE_FONT)
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten
    #go-back-to-menu btn
    btn_back=Button(frame, text='← Return', bg='lightgray', command=mode_menu)
    btn_back.place(relx=0.005, rely=0.01, relwidth=0.1, relheight=0.1)

    #load player tank images
    global tank_p1_img, tank_p2_img, tank_p3_img
    tank_p1_img = PhotoImage(file=resource_path('Assets/Tank_Blue_Right.png')).subsample(4, 4)
    tank_p2_img = PhotoImage(file=resource_path('Assets/Red_Tank_Right.png')).subsample(4, 4)
    tank_p3_img = PhotoImage(file=resource_path('Assets/Tank_Green_Right.png')).subsample(4, 4)
 
    #texts-based on prototyp design
    p1_text=(
        "Move Forward                                                   W\n"
        "Move Backward                                                 S\n\n"
        "Turn Right                                                            D\n"
        "Turn Left                                                               A\n"
        "Shoot                                                                     E")
    p3_text=(
        "Move Forward                                                   Z\n"
        "Move Backward                                                H\n\n"
        "Turn Right                                                            J\n"
        "Turn Left                                                              G\n"
        "Shoot                                                                    U")
    p2_text=(
        "Move Forward                                Arrow Up\n"
        "Move Backward                             Arrow Down\n\n"
        "Turn Right                                        Arrow Right\n"
        "Turn Left                                           Arrow Left\n"
        "Shoot                                                 Right Ctrl")
    #mode1->display 2 boxes; mode2->all bxs
    if mode == '1 vs 1':
        player_box(frame, 0.21, 'Controls Player 1', p1_text, tank_p1_img)
        player_box(frame, 0.54, 'Controls Player 2', p2_text, tank_p2_img)
    else:
        player_box(frame, 0.06, 'Controls Player 1', p1_text, tank_p1_img)
        player_box(frame, 0.38, 'Controls Player 2', p2_text, tank_p2_img)
        player_box(frame, 0.7, 'Controls Player 3', p3_text, tank_p3_img)
 
    #continue btn
    btn_continue = Button(frame, text='Continue', bg='orange', font=('Calibri', 14, 'bold'), command=lambda: name_input_screen(mode))
    btn_continue.place(relx=0.36, rely=0.75, relwidth=0.27, relheight=0.1)

def player_name_box(frame, x_pos, title_text, default_name, tank_img, name_entries_list): 
    """
    Macht: Erstellt eine Eingabebox, in der ein Spieler seinen Namen anpassen kann,
           ergänzt durch den jeweiligen Tank und Beschriftungen.
    Input: frame (Frame) - Das übergeordnete Fenster-Frame
           x_pos (float) - Die horizontale Position (relx) der Box
           title_text (str) - Titel der Box (z.B. 'Player 1')
           default_name (str) - Der voreingestellte Name im Textfeld
           tank_img (PhotoImage) - Das zugehörige Tank-Bild
           name_entries_list (list) - Liste, in der das Eingabefeld referenziert wird
    Output: Keine (platziert das UI-Element im Frame)
    """
    box=Frame(frame, bd=2, relief=GROOVE)
    box.place(relx=x_pos, rely=0.18, relwidth=0.23, relheight=0.55)
    lbl_title=Label(box, text=title_text, font=('Calibri', 14, 'bold'))
    lbl_title.pack(pady=5)
    if tank_img:
        Label(box, image=tank_img).pack(pady=(35, 10))
    lbl_desc=Label(box, text="Enter name here:", font=('Calibri', 11))
    lbl_desc.pack(pady=5)
    ent=Entry(box, font=('Calibri', 12), justify='center')
    ent.insert(0, default_name)
    ent.pack(padx=10, pady=5, fill=X)
    name_entries_list.append(ent)

#Namenseingabe von Noah geschrieben
### Claude code für start_game als eigene Funktion
def start_game(mode):
    """
    Macht: Liest die eingegebenen Namen aus (ein leeres Feld wird zu "Player N")
           und startet das Spiel.
    Input: mode (str) - Der ausgewählte Spielmodus ('1 vs 1' oder '1 vs 1 vs 1')
    Output: Keine (startet das Spiel)
    """
    names = [entry.get().strip() or f'Player {i+1}' for i, entry in enumerate(name_entries)]
    game.run_game(root, mode, names)
### Claude code für start_game als eigene Funktion

def name_input_screen(mode):
    """
    Macht: Zeigt den Bildschirm zur Namensänderung vor dem Spielstart an, 
           sammelt die Eingaben und startet das eigentliche Spiel.
    Input: mode (str) - Der ausgewählte Spielmodus ('1 vs 1' oder '1 vs 1 vs 1')
    Output: Keine (startet das Spiel oder wechselt den Screen)
    """
    for widget in root.winfo_children():
        widget.destroy()
    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten
    bg_canvas, width, height = create_background_canvas(frame)
    bg_canvas.create_text(width * 0.5, height * 0.1, text='Enter Player Names', fill='white', font=TITLE_FONT)
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten
    
    # Return button goes back to controls screen
    btn_back = Button(frame, text='← Return', bg='lightgray', command=lambda: controls_screen(mode))
    btn_back.place(relx=0.005, rely=0.01, relwidth=0.1, relheight=0.1)
    global name_entries
    name_entries=[]

    if mode == '1 vs 1':
        player_name_box(frame, 0.21, 'Player 1', 'Player 1', tank_p1_img, name_entries)
        player_name_box(frame, 0.54, 'Player 2', 'Player 2', tank_p2_img, name_entries)
    else:
        player_name_box(frame, 0.06, 'Player 1', 'Player 1', tank_p1_img, name_entries)
        player_name_box(frame, 0.38, 'Player 2', 'Player 2', tank_p2_img, name_entries)
        player_name_box(frame, 0.7, 'Player 3', 'Player 3', tank_p3_img, name_entries)   
        
    #play btn->launches the game
    btn_play = Button(frame, text='Play', bg='orange', font=('Calibri', 14, 'bold'), command=lambda: start_game(mode))
    btn_play.place(relx=0.36, rely=0.77, relwidth=0.27, relheight=0.1)
 
root = Tk()
root.title('Tank Game')
root.attributes('-fullscreen', True)
root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))
root.option_add('*Font', 'Calibri 12')
root.option_add('*Background','#f0f0f0')
myappid = 'Tray_Icon'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
root.iconbitmap(resource_path('Assets/Logo/App-Logo.ico'))
# start app on menufunct
mode_menu()
root.mainloop()