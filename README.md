# TNK-XTREME

Ein lokales Panzer-Duell für 2 oder 3 Spieler an einer Tastatur, geschrieben in Python mit Tkinter.
Entstanden in der EF-Woche 2026 am Gymnasium Lerbermatt.

Wer als Letzter noch fährt, gewinnt die Runde. Das Scoreboard zählt die Siege, solange das Spiel offen ist.

## Starten

Benötigt wird **Python 3.10 oder neuer** (entwickelt mit Python 3.12) unter **Windows**.

1. Pakete installieren:

   ```bash
   pip install pillow pygame
   ```

2. Im Projektordner das Menü starten:

   ```bash
   python menu.py
   ```

| Paket | Wofür | Getestete Version |
|---|---|---|
| `pillow` | Bilder laden, skalieren, drehen und weichzeichnen | 12.3 |
| `pygame` | Sounds (nur `pygame.mixer`) | 2.6 |
| `tkinter` | Fenster und Spielfeld | ist bei Python dabei |

Hat der PC keine Tonausgabe, läuft das Spiel ohne Ton weiter.

## Spielablauf

1. Im Menü **1 VS 1** oder **1 VS 1 VS 1** wählen.
2. Die Steuerung ansehen und mit **Continue** weiter.
3. Namen eingeben und **Play** drücken. Doppelte Namen bekommen automatisch eine Nummer („Noah“, „Noah 2“).
4. Nach der Runde erscheint das Scoreboard: **Replay** startet eine neue Runde mit denselben Spielern, **Return to Menu** führt zurück ins Menü.

Während der Runde bringt der Button **Leave** oben links zurück ins Menü. **Escape** beendet den Vollbildmodus.

### Regeln

- Ein Treffer zerstört einen Panzer. Nach jedem Schuss muss 4 Sekunden nachgeladen werden. Der graue Ring neben dem Namen zeigt, wie weit.
- **Bäume** blockieren Panzer. Ein Schuss fällt einen Baum, danach ist nur noch ein Stumpf übrig, über den man fahren kann.
- **Minen** explodieren, sobald man darüberfährt.
- Ein zerstörter Panzer bleibt als brennendes **Wrack** liegen. Es blockiert Panzer und Schüsse und dient so als Deckung.

## Steuerung

| Aktion | Spieler 1 (blau) | Spieler 2 (rot) | Spieler 3 (grün) |
|---|---|---|---|
| Vorwärts | `W` | `↑` | `Z` |
| Rückwärts | `S` | `↓` | `H` |
| Links drehen | `A` | `←` | `G` |
| Rechts drehen | `D` | `→` | `J` |
| Schießen | `E` | `Ctrl` rechts | `U` |

Spieler 3 spielt nur im Modus 1 VS 1 VS 1 mit. Die Tasten gelten für eine Schweizer Tastatur (QWERTZ).

## Exe bauen

Die exe wird mit [PyInstaller](https://pyinstaller.org) gebaut (getestet mit 6.22):

```bash
pip install pyinstaller
```

```bash
python -m PyInstaller -F --name "TNK-XTREME" --icon=Assets/Logo/App-Logo.ico --noconsole --add-data "Assets;Assets" --add-data "Sounds;Sounds" menu.py
```

- Die fertige Datei liegt danach unter `dist/TNK-XTREME.exe`.
- Es reicht, `menu.py` anzugeben. Die übrigen Python-Dateien findet PyInstaller über die Imports selbst.
- `--add-data` packt die Ordner `Assets` und `Sounds` mit ein. In der exe findet `utils.resource_path()` sie im temporären Entpack-Ordner (`sys._MEIPASS`).
- `build/`, `dist/` und `*.spec` stehen in der `.gitignore` und kommen nicht ins Repository.

## Tests

```bash
python -m unittest test_game -v
```

Die Unit-Tests prüfen unter anderem:
- Kollisionen, Spawn-Positionen, Bewegung und Drehung
- Schüsse, Minen, Wracks und das Spielende
- das Scoreboard, die Bilderzeugung und `resource_path`
- das Spiel ohne Tonausgabe

Für die Tests öffnet sich kurz ein unsichtbares Tk-Fenster.

## Projektaufbau

| Datei / Ordner | Inhalt |
|---|---|
| `menu.py` | Startpunkt: Hauptmenü, Steuerungsübersicht und Namenseingabe |
| `game.py` | Das eigentliche Spiel: Spielfeld, Panzer, Schüsse, Kollisionen, Sounds und Ablauf einer Runde |
| `build_tank_images.py` | Erzeugt aus den Panzerbildern alle 8 Blickrichtungen, die Schuss-Animation und die Wracks |
| `scoreboard.py` | Zählt die Siege, solange das Spiel läuft |
| `winner_screen.py` | Endbildschirm mit Gewinner und Scoreboard |
| `utils.py` | `resource_path()`: findet Assets als Skript und in der exe |
| `test_game.py` | Unit-Tests |
| `Assets/` | Grafiken (Karte, Panzer, Bäume, Minen, Explosionen, Logo) |
| `Sounds/` | Soundeffekte und Hintergrundgeräusche |

## Team

| Person | Aufgaben |
|---|---|
| Noah Hiltbrunner | Spiellogik (`game.py`), Bilderzeugung (`build_tank_images.py`), Scoreboard, Endbildschirm, Tests, Build der exe |
| dim mim | Menü (`menu.py`) |
| Jun Rösli | Grafiken: Karte, Panzer, Bäume, Minen und Explosionen (`Assets/`) |
| Kian Böhm | Animationen für Schuss und zerstörte Panzer, Logo und Sounds |

### Hilfe durch KI

Teile des Codes wurden mit Hilfe von Claude (Anthropic) geschrieben. Diese Stellen sind im Code mit `### Claude code für …` markiert, jeweils vor und nach dem Abschnitt.
