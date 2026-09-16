session_wins = {}


def register_players(player_names):
    """
    Macht: Fuegt Spieler ohne bisherigen Sieg zum sessionsweiten Scoreboard hinzu.
    Input: player_names (Liste von Spielernamen)
    Output: kein Rueckgabewert
    """
    for name in player_names:
        session_wins.setdefault(name, 0)


def record_win(player_name):
    """
    Macht: Erhoeht die Anzahl Siege eines Spielers um eins.
    Input: player_name (Name des Gewinners)
    Output: kein Rueckgabewert
    """
    session_wins[player_name] = session_wins.get(player_name, 0) + 1


def get_leaderboard():
    """
    Macht: Liefert alle Spieler nach Anzahl Siege sortiert.
    Input: keine
    Output: Liste von (Name, Siege)-Tupeln
    """
    return sorted(session_wins.items(), key=lambda entry: (-entry[1], entry[0].lower()))
