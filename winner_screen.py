from tkinter import Button, Canvas

### Claude code für weichgezeichneten Hintergrund auf allen Seiten
from utils import add_blurred_background
### Claude code für weichgezeichneten Hintergrund auf allen Seiten


def show_winner_screen(root, winner_text, leaderboard, replay_command, return_to_menu_command):
    """
    Macht: Zeigt die Endseite mit Gewinnertext, Scoreboard und Menue-Button.
    Input: root (Tk-Fenster), winner_text (Text), leaderboard (Liste), replay_command,
           return_to_menu_command (Funktionen)
    Output: kein Rueckgabewert
    """
    for widget in root.winfo_children():
        widget.destroy()

    width = root.winfo_width()
    height = root.winfo_height()
    end_canvas = Canvas(root, width=width, height=height, bg="#202020", highlightthickness=0)
    end_canvas.pack(fill="both", expand=True)
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten
    add_blurred_background(end_canvas, width, height)
    ### Claude code für weichgezeichneten Hintergrund auf allen Seiten
    end_canvas.create_text(
        width // 2,
        height * 0.20,
        text=winner_text,
        fill="white",
        font=("Calibri", 28, "bold"),
    )
    leaderboard_text = "\n".join(
        f"{position}. {name}: {wins}" for position, (name, wins) in enumerate(leaderboard, start=1)
    )
    board_left = width * 0.35
    board_top = height * 0.30
    board_right = width * 0.65
    board_bottom = height * 0.68
    end_canvas.create_rectangle(board_left, board_top, board_right, board_bottom, outline="white", width=2)
    end_canvas.create_text(
        width // 2,
        board_top + 28,
        text="Scoreboard",
        fill="white",
        font=("Calibri", 20, "bold"),
        justify="center",
    )
    end_canvas.create_text(
        width // 2,
        (board_top + board_bottom) / 2 + 25,
        text=leaderboard_text,
        fill="white",
        font=("Calibri", 16),
        justify="left",
    )
    replay_button = Button(
        root,
        text="Replay",
        font=("Calibri", 16, "bold"),
        command=replay_command,
    )
    end_canvas.create_window(width // 2, height * 0.78, window=replay_button)
    return_button = Button(
        root,
        text="Return to Menu",
        font=("Calibri", 16, "bold"),
        command=return_to_menu_command,
    )
    end_canvas.create_window(width // 2, height * 0.86, window=return_button)
