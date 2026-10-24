"""gestion du temps de réponse"""

__author__ = "benach_a"


import math
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from utils import charger_json, sauvegarder_json


FORMAT_DATE = "%d/%m/%Y %H:%M"


try:
    import msvcrt
    os.system("")
except ImportError:
    msvcrt = None
    import select
    try:
        import termios
    except ImportError:
        termios = None

ESC = "\033"


class Chrono:
    """Mesure le temps écoulé et vérifie une limite"""

    def __init__(self, limite=None):
        self.limite = limite
        self._debut = None

    def demarrer(self):
        self._debut = time.monotonic()

    @property
    def ecoule(self):
        return 0.0 if self._debut is None else time.monotonic() - self._debut

    @property
    def depasse(self):
        return self.limite is not None and self.ecoule > self.limite


def quiz_est_ouvert(date_debut):
    """True si l'heure de début du quiz est arrivée"""
    return datetime.now() >= date_debut


def temps_restant(date_debut):
    """Durée restante avant le début (jamais négative)"""
    return max(date_debut - datetime.now(), timedelta(0))


def formater_duree(duree):
    """Ex. : '1 j 2 h 5 min'"""
    minutes_totales = int(duree.total_seconds() // 60)
    jours, reste = divmod(minutes_totales, 24 * 60)
    heures, minutes = divmod(reste, 60)
    return f"{jours} j {heures} h {minutes} min"


def charger_date_debut(chemin, defaut):
    """Lit la date du quiz dans le fichier. Retourne `defaut` si absent ou invalide"""
    if not Path(chemin).exists():
        return defaut
    donnees = charger_json(chemin, defaut={})
    try:
        return datetime.strptime(donnees["date_debut_quiz"], FORMAT_DATE)
    except (KeyError, ValueError, TypeError):
        return defaut


def sauvegarder_date_debut(chemin, date):
    """Enregistre la date du quiz dans le fichier"""
    sauvegarder_json(chemin, {"date_debut_quiz": date.strftime(FORMAT_DATE)})


def _afficher_restant(reste):
    """Met à jour la ligne « Temps restant » juste au-dessus de la saisie (sans la perturber)"""
    sys.stdout.write(f"{ESC}7{ESC}[1A\rTemps restant : {math.ceil(reste):2d}s {ESC}8")
    sys.stdout.flush()


def _vider_entree():
    """Jette ce que l'utilisateur a tapé sans valider (Linux), pour ne pas gêner la question suivante"""
    if termios:
        try:
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except (termios.error, OSError, ValueError):
            pass


def _lire_unix(fin):
    """lire sur linux"""
    while True:
        reste = fin - time.monotonic()
        if reste <= 0:
            _vider_entree()
            print()
            return None
        pret, _, _ = select.select([sys.stdin], [], [], min(1.0, reste))
        if pret:
            ligne = sys.stdin.readline()
            if ligne == "":
                raise EOFError
            return ligne.rstrip("\n")
        _afficher_restant(fin - time.monotonic())


def _lire_windows(fin):
    """lire sur windows"""
    saisie = ""
    dernier = time.monotonic()
    while True:
        reste = fin - time.monotonic()
        if reste <= 0:
            print()
            return None
        if msvcrt.kbhit():
            c = msvcrt.getwch()
            if c in ("\x00", "\xe0"):
                msvcrt.getwch()
            elif c in ("\r", "\n"):
                print()
                return saisie
            elif c == "\x03":
                raise KeyboardInterrupt
            elif c == "\b":
                if saisie:
                    saisie = saisie[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif c.isprintable():
                saisie += c
                sys.stdout.write(c)
                sys.stdout.flush()
        else:
            time.sleep(0.05)
        if time.monotonic() - dernier >= 1:
            _afficher_restant(reste)
            dernier = time.monotonic()


def lire_avec_timer(message, delai):
    """Affiche un compte à rebours et lit une ligne
    Retourne le texte saisi, ou None si le temps est écoulé"""
    if not sys.stdin.isatty():
        return input(message)
    print(f"Temps restant : {math.ceil(delai):2d}s")
    print(message, end="", flush=True)
    fin = time.monotonic() + delai
    return _lire_windows(fin) if msvcrt else _lire_unix(fin)
