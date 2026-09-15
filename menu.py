from tkinter import *
from tkinter import messagebox
import game
 
def mode_menu():
    #clear old widgets->feels like switching
    for widget in root.winfo_children():
        widget.destroy()
 
    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
    #title,desc
    label_title=Label(frame, text='TNK-XTREME', fg='dark blue', font=('Calibri', 28, 'bold'))
    label_title.place(relx=0.2, rely=0.15, relwidth=0.6, relheight=0.15)
    label_desc=Label(frame, text='Choose your battle mode to play on one computer:', font=('Calibri', 14))
    label_desc.place(relx=0.1, rely=0.35, relwidth=0.8, relheight=0.1)
 
    #button for mode1(string->controls screen)
    btn_1=Button(frame, text='1 VS 1 Mode', bg='yellow', command=lambda: controls_screen('1 vs 1'))
    btn_1.place(relx=0.3, rely=0.5, relwidth=0.4, relheight=0.1)
 
    #btn for mode2
    btn_2=Button(frame, text='1 VS 1 VS 1 Mode', bg='yellow', command=lambda: controls_screen('1 vs 1 vs 1'))
    btn_2.place(relx=0.3, rely=0.65, relwidth=0.4, relheight=0.1)
 
def controls_screen(mode):
    #d previous frame
    for widget in root.winfo_children():
        widget.destroy()
 
    frame=Frame(root, bd=0)
    frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
 
    #check selected mode(->change text header)
    text_mode='1 vs 1 Controls' if mode == '1 vs 1' else '1 vs 1 vs 1 Controls'
    label=Label(frame, text=text_mode, fg='green', font=('Calibri', 20, 'bold'))
    label.place(relx=0.2, rely=0.05, relwidth=0.6, relheight=0.1)
    #go-back-to-menu btn
    btn_back=Button(frame, text='← Return', bg='lightgray', command=mode_menu)
    btn_back.place(relx=0.005, rely=0.01, relwidth=0.1, relheight=0.1)
 
    #helpfunct->create player boxes(controls explain)
    def player_box(x_pos, title_text, controls_text):
        box=Frame(frame, bd=2, relief=GROOVE)
        box.place(relx=x_pos, rely=0.18, relwidth=0.23, relheight=0.45)
 
        lbl_title=Label(box, text=title_text, font=('Calibri', 14, 'bold'))
        lbl_title.pack(pady=10)
 
        lbl_body=Label(box, text=controls_text, font=('Calibri', 11), justify=LEFT)
        lbl_body.pack(padx=10, anchor='w')
 
    #texts-based on prototyp design
    p1_text=(
        "Move Forward                                                   W\n"
        "Move Backward                                                 S\n\n"
        "Turn Right                                                            D\n"
        "Turn Left                                                               A\n"
        "Shoot                                                                     E")
    p2_text=(
        "Move Forward                                                   F\n"
        "Move Backward                                                H\n\n"
        "Turn Right                                                            J\n"
        "Turn Left                                                              G\n"
        "Shoot                                                                    U")
    p3_text=(
        "Move Forward                                             Up\n"
        "Move Backward                                          Down\n\n"
        "Turn Right                                                     Right\n"
        "Turn Left                                                        Left\n"
        "Shoot                                                              Left Ctrl")
    #mode1->display 2 boxes; mode2->all bxs
    if mode=='1 vs 1':
        player_box(0.21, 'Controls Player 1', p1_text)
        player_box(0.54, 'Controls Player 2', p2_text)
    else:
        player_box(0.06, 'Controls Player 1', p1_text)
        player_box(0.38, 'Controls Player 2', p2_text)
        player_box(0.7, 'Controls Player 3', p3_text)
 
    #play btn
    btn_play = Button(frame, text='Play', bg='lightgreen', font=('Calibri', 14, 'bold'), command=lambda: game.run_game(root, mode))
    btn_play.place(relx=0.35, rely=0.75, relwidth=0.3, relheight=0.08)
 
root = Tk()
root.title('Tank Game')
root.attributes('-fullscreen', True)
root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))
root.option_add('*Font', 'Calibri 12')
root.option_add('*Background', 'white')
# start app on menufunct
mode_menu()
root.mainloop()