from tkinter import *
from tkinter import messagebox
HEIGHT = 600
WIDTH = 800

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
    label.place(relx=0.2, rely=0.2, relwidth=0.6, relheight=0.1)
    #controlsexplain
    label_controls=Label(frame, text='Controls explanation will be here...', font=('Calibri', 14))
    label_controls.place(relx=0.2, rely=0.4, relwidth=0.6, relheight=0.2)
    #go-back-to-menu btn
    btn_back=Button(frame, text='Back to Menu', bg='lightgray', command=mode_menu)
    btn_back.place(relx=0.3, rely=0.7, relwidth=0.4, relheight=0.1)

#setup rootwindow
root = Tk()
root.title('Tank Game')
root.geometry(f'{WIDTH}x{HEIGHT}')
root.resizable(False, False)
root.option_add('*Font', 'Calibri 12')
root.option_add('*Background', 'white')
#start app on menufunct
mode_menu()
root.mainloop()