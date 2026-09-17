### Claude code für problem bei rückgehen von menu nach spiel
import sys
sys.modules.setdefault('menu', sys.modules[__name__])
### Claude code für problem bei rückgehen von menu nach spiel

from tkinter import *
import game
from tkinter import messagebox
import os
from PIL import Image, ImageTk, ImageFilter
import ctypes
from utils import resource_path

### Claude code für weichgezeichneten City-Hintergrund im Menu
CITY_BACKGROUND_PATH = resource_path('Assets/Map_City.png')
CITY_BLUR_RADIUS = 9  #Staerke der Weichzeichnung
CITY_DARKEN_AMOUNT = 0.35  #0 = Originalfarben, 1 = schwarz; dunkler = Text besser lesbar

def load_blurred_city_background(width, height):
    """
    Macht: Laedt die City-Karte, skaliert sie auf die Fenstergroesse,
           zeichnet sie weich und dunkelt sie leicht ab, damit Titel und
           Buttons darueber gut lesbar bleiben.
    Input: width, height (Zielgroesse in Pixeln)
    Output: ImageTk.PhotoImage
    """
    img = Image.open(CITY_BACKGROUND_PATH).convert('RGB')
    img = img.resize((max(1, width), max(1, height)))
    img = img.filter(ImageFilter.GaussianBlur(CITY_BLUR_RADIUS))
    img = Image.blend(img, Image.new('RGB', img.size, (0, 0, 0)), CITY_DARKEN_AMOUNT)
    return ImageTk.PhotoImage(img)
### Claude code für weichgezeichneten City-Hintergrund im Menu

def mode_menu():
    #clear old widgets->feels like switching
    for widget in root.winfo_children():
        widget.destroy()

    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

    ### Claude code für weichgezeichneten City-Hintergrund im Menu
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    #####
    global menu_background_img
    bg_canvas = Canvas(frame, width=width, height=height, highlightthickness=0, bd=0, bg='#3f5c3f')
    bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
    menu_background_img = load_blurred_city_background(width, height)
    bg_canvas.create_image(0, 0, anchor='nw', image=menu_background_img)

    #title,desc
    bg_canvas.create_text(width * 0.5, height * 0.225, text='TNK-XTREME',
                          fill='white', font=('Calibri', 28, 'bold'))
    bg_canvas.create_text(width * 0.5, height * 0.4, text='Choose battle mode to play:',
                          fill='white', font=('Calibri', 14))

    #-DECORATIVE SIDE TANKS-
    global tank_left_img, tank_right_img
    green_path = resource_path('Assets/Tank_Green_Homescreen.png')
    blue_path = resource_path('Assets/Tank_Blue_Homescreen.png')

    tank_left_img = PhotoImage(file=green_path).subsample(2, 2)
    tank_right_img = PhotoImage(file=blue_path).subsample(2, 2)

    bg_canvas.create_image(width * 0.15, height * 0.57, image=tank_left_img)
    bg_canvas.create_image(width * 0.85, height * 0.57, image=tank_right_img)
    ### Claude code für weichgezeichneten City-Hintergrund im Menu
 
    #button for mode1(string->controls screen)
    btn_1=Button(frame, text='1 VS 1 Mode', bg='lightgreen', command=lambda: controls_screen('1 vs 1'))
    btn_1.place(relx=0.4, rely=0.5, relwidth=0.2, relheight=0.1)
 
    #btn for mode2
    btn_2=Button(frame, text='1 VS 1 VS 1 Mode', bg='lightblue', command=lambda: controls_screen('1 vs 1 vs 1'))
    btn_2.place(relx=0.4, rely=0.65, relwidth=0.2, relheight=0.1)
 
def controls_screen(mode):
    #d previous frame
    for widget in root.winfo_children():
        widget.destroy()

    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

    #check selected mode(->change text header)
    if mode == '1 vs 1':
        text_mode='1 vs 1 Controls'
    else:
        text_mode='1 vs 1 vs 1 Controls'
    label=Label(frame, text=text_mode, fg='brown', font=('Calibri', 20, 'bold'))
    label.place(relx=0.2, rely=0.05, relwidth=0.6, relheight=0.1)
    #go-back-to-menu btn
    btn_back=Button(frame, text='← Return', bg='lightgray', command=mode_menu)
    btn_back.place(relx=0.005, rely=0.01, relwidth=0.1, relheight=0.1)

    #load player tank images
    global tank_p1_img, tank_p2_img, tank_p3_img
    tank_p1_img = PhotoImage(file=resource_path('Assets/Tank_Blue_Right.png')).subsample(4, 4)
    tank_p2_img = PhotoImage(file=resource_path('Assets/Red_Tank_Right.png')).subsample(4, 4)
    tank_p3_img = PhotoImage(file=resource_path('Assets/Tank_Green_Right.png')).subsample(4, 4)

    #helpfunct->create player boxes(controls explain)
    def player_box(x_pos, title_text, controls_text):
        box=Frame(frame, bd=2, relief=GROOVE)
        box.place(relx=x_pos, rely=0.18, relwidth=0.23, relheight=0.45)

        lbl_title=Label(box, text=title_text, font=('Calibri', 14, 'bold'))
        lbl_title.pack(pady=10)

        lbl_body=Label(box, text=controls_text, font=('Calibri', 11), justify=LEFT)
        lbl_body.pack(padx=10, anchor='w')

        #pics:
        if title_text == 'Controls Player 1': Label(box, image=tank_p1_img).pack(pady=(25, 0))
        elif title_text == 'Controls Player 2': Label(box, image=tank_p2_img).pack(pady=(25, 0))
        elif title_text == 'Controls Player 3': Label(box, image=tank_p3_img).pack(pady=(25, 0))
 
    #texts-based on prototyp design
    p1_text=(
        "Move Forward                                                   W\n"
        "Move Backward                                                 S\n\n"
        "Turn Right                                                            D\n"
        "Turn Left                                                               A\n"
        "Shoot                                                                     E")
    p3_text=(
        "Move Forward                                                   z\n"
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
    if mode=='1 vs 1':
        player_box(0.21, 'Controls Player 1', p1_text)
        player_box(0.54, 'Controls Player 2', p2_text)
    else:
        player_box(0.06, 'Controls Player 1', p1_text)
        player_box(0.38, 'Controls Player 2', p2_text)
        player_box(0.7, 'Controls Player 3', p3_text)
 
    #continue btn
    btn_continue = Button(frame, text='Continue', bg='orange', font=('Calibri', 14, 'bold'), command=lambda: name_input_screen(mode))
    btn_continue.place(relx=0.36, rely=0.75, relwidth=0.27, relheight=0.1)

#wndw to hcange players' names
def name_input_screen(mode):
    for widget in root.winfo_children():
        widget.destroy()
    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
    label=Label(frame, text='Enter Player Names', fg='brown', font=('Calibri', 20, 'bold'))
    label.place(relx=0.2, rely=0.05, relwidth=0.6, relheight=0.1)
    
    # Return button goes back to controls screen
    btn_back = Button(frame, text='← Return', bg='lightgray', command=lambda: controls_screen(mode))
    btn_back.place(relx=0.005, rely=0.01, relwidth=0.1, relheight=0.1)
    global name_entries
    name_entries=[]

    def player_name_box(x_pos, title_text, default_name, tank_img):
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
        name_entries.append(ent)
    if mode == '1 vs 1':
        player_name_box(0.21, 'Player 1', 'Player 1', tank_p1_img)
        player_name_box(0.54, 'Player 2', 'Player 2', tank_p2_img)
    else:
        player_name_box(0.06, 'Player 1', 'Player 1', tank_p1_img)
        player_name_box(0.38, 'Player 2', 'Player 2', tank_p2_img)
        player_name_box(0.7, 'Player 3', 'Player 3', tank_p3_img)
 
    #play btn->launches the game
    #Namenseingabe von Noah geschrieben 
    def start_game():
        names = [entry.get().strip() or default for entry, default in zip(name_entries, [f'Player {i+1}' for i in range(len(name_entries))])]
        game.run_game(root, mode, names)

    btn_play = Button(frame, text='Play', bg='orange', font=('Calibri', 14, 'bold'), command=start_game)
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