from tkinter import Button, Canvas


def show_winner_screen(root, winner_text, replay_command):
    """
    Macht: Zeigt eine Endseite mit Gewinnertext und einem Replay-Button.
    Input: root (Tk-Fenster), winner_text (Text), replay_command (Funktion)
    Output: kein Rueckgabewert
    """
    for widget in root.winfo_children():
        widget.destroy()

    width = root.winfo_width()
    height = root.winfo_height()
    end_canvas = Canvas(root, width=width, height=height, bg="#202020", highlightthickness=0)
    end_canvas.pack(fill="both", expand=True)
    end_canvas.create_text(
        width // 2,
        height // 2 - 35,
        text=winner_text,
        fill="white",
        font=("Calibri", 32, "bold"),
    )
    replay_button = Button(
        root,
        text="Replay",
        font=("Calibri", 16, "bold"),
        command=replay_command,
    )
    end_canvas.create_window(width // 2, height // 2 + 35, window=replay_button)
