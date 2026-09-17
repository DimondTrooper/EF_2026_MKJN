import os
import sys


def resource_path(relative_path):
    """
    Macht: Liefert den vollstaendigen Pfad zu einer Datei aus Assets/ oder Sounds/.
           Als exe (PyInstaller) liegen diese Dateien im temporaeren Entpack-Ordner
           sys._MEIPASS -- diese Variable existiert nur in der gepackten exe.
           Als normales .py-Skript wird der Projektordner genommen (der Ordner
           dieser Datei), damit es auch klappt, wenn das Spiel aus einem anderen
           Ordner gestartet wird.
    Input: relative_path (z.B. "Sounds/Shoot.wav")
    Output: absoluter Pfad als String
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
