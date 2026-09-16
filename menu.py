from tkinter import *
import game
import gc
import os

def mode_menu():
    #clear old widgets->feels like switching
    for widget in root.winfo_children():
        widget.destroy()

    ### Claude code für problem bei rückgehen von menu nach spiel
    #nach einer Partie haengen sehr viele Panzer-/Explosionsbilder aus dem
    #Spiel im zyklischen Garbage Collector; Tk vergibt Bildnamen fortlaufend
    #und recycelt freigewordene Nummern. Ohne diesen expliziten Collect-Aufruf
    #kann ein spaeter (verzoegert) aufgeraeumtes altes Spielbild zufaellig
    #denselben Namen wie ein gerade frisch erstelltes Menue-Bild bekommen und
    #es beim Aufraeumen aus Tk loeschen -> Bilder verschwinden oder Screens
    #brechen mitten in der Erstellung ab (siehe controls_screen/name_input_screen).
    gc.collect()
    ### Claude code für problem bei rückgehen von menu nach spiel

    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
    #title,desc
    label_title=Label(frame, text='TNK-XTREME', fg='dark blue', font=('Calibri', 28, 'bold'))
    label_title.place(relx=0.2, rely=0.15, relwidth=0.6, relheight=0.15)
    label_desc=Label(frame, text='Choose battle mode to play:', font=('Calibri', 14))
    label_desc.place(relx=0.1, rely=0.35, relwidth=0.8, relheight=0.1)

    #-DECORATIVE SIDE TANKS-
    global tank_left_img, tank_right_img
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        green_path = os.path.join(script_dir, 'Assets', 'Tank_Green_Homescreen.png')
        blue_path = os.path.join(script_dir, 'Assets', 'Tank_Blue_Homescreen.png')
        
        raw_img_green = PhotoImage(file=green_path)
        raw_img_blue = PhotoImage(file=blue_path)
        
        tank_left_img = raw_img_green.subsample(2, 2)
        tank_right_img = raw_img_blue.subsample(2, 2)
        
        Label(frame, image=tank_left_img).place(relx=0.15, rely=0.57, anchor='center')
        Label(frame, image=tank_right_img).place(relx=0.85, rely=0.57, anchor='center')
    except Exception as e:
        print(f"Image load note: {e}")
    #decor side tanks - imported from ai entirely!
 
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

    ### Claude code für problem bei rückgehen von menu nach spiel
    #siehe Kommentar in mode_menu() -- verhindert, dass ein verzoegert
    #aufgeraeumtes altes Spielbild ein gerade erst erstelltes Bild hier
    #ungueltig macht und die Funktion mitten in der Erstellung abbricht
    gc.collect()
    ### Claude code für problem bei rückgehen von menu nach spiel

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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tank_p1_img = PhotoImage(file=os.path.join(script_dir, 'Assets', 'Tank_Blue_Right.png')).subsample(4, 4)
    tank_p2_img = PhotoImage(file=os.path.join(script_dir, 'Assets', 'Red_Tank_Right.png')).subsample(4, 4)
    tank_p3_img = PhotoImage(file=os.path.join(script_dir, 'Assets', 'Tank_Green_Right.png')).subsample(4, 4)

    #helpfunct->create player boxes(controls explain)
    def player_box(x_pos, title_text, controls_text):
        box=Frame(frame, bd=2, relief=GROOVE)
        box.place(relx=x_pos, rely=0.18, relwidth=0.23, relheight=0.45)

        lbl_title=Label(box, text=title_text, font=('Calibri', 14, 'bold'))
        lbl_title.pack(pady=10)

        lbl_body=Label(box, text=controls_text, font=('Calibri', 11), justify=LEFT)
        lbl_body.pack(padx=10, anchor='w')

        ### Claude code für problem bei rückgehen von menu nach spiel
        #pics: einzeln abgesichert, damit ein kaputtes Bild nicht die
        #restliche Screen-Erstellung (Continue-Button!) mitreisst
        try:
            if title_text == 'Controls Player 1': Label(box, image=tank_p1_img).pack(pady=(25, 0))
            elif title_text == 'Controls Player 2': Label(box, image=tank_p2_img).pack(pady=(25, 0))
            elif title_text == 'Controls Player 3': Label(box, image=tank_p3_img).pack(pady=(25, 0))
        except Exception as e:
            print(f"Image load note: {e}")
        ### Claude code für problem bei rückgehen von menu nach spiel
 
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
        "Shoot                                                 Left Ctrl")
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

    ### Claude code für problem bei rückgehen von menu nach spiel
    #siehe Kommentar in mode_menu()
    gc.collect()
    ### Claude code für problem bei rückgehen von menu nach spiel

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
        ### Claude code für problem bei rückgehen von menu nach spiel
        if tank_img:
            try:
                Label(box, image=tank_img).pack(pady=(35, 10))
            except Exception as e:
                print(f"Image load note: {e}")
        ### Claude code für problem bei rückgehen von menu nach spiel
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
# start app on menufunct
mode_menu()
root.mainloop()