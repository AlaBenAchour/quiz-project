"""Fonctions utilitaires fichiers JSON et saisies sécurisées"""

__author__ = "benach_a"


import json
from pathlib import Path
import csv
from config import VERT, ROUGE, RESET


def afficher_vert(message):
    print(f"{VERT}{message}{RESET}")


def afficher_rouge(message):
    print(f"{ROUGE}{message}{RESET}")


def charger_json(chemin, defaut=None):
    """Charge un fichier JSON"""
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fichier introuvable : {chemin}")
        if defaut is None:
            raise
        return defaut
    except json.JSONDecodeError:
        print(f"Fichier JSON invalide : {chemin}")
        if defaut is None:
            raise
        return defaut


def sauvegarder_json(chemin, donnees):
    """Sauvegarde des données dans un fichier JSON"""
    Path(chemin).parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=2, ensure_ascii=False)


def demander_entier(message, minimum, maximum):
    """Redemande tant que l'entrée n'est pas un entier dans [minimum, maximum]"""
    while True:
        saisie = input(message).strip()
        try:
            valeur = int(saisie)
        except ValueError:
            print("Veuillez entrer un nombre.")
            continue
        if minimum <= valeur <= maximum:
            return valeur
        print(f"Choisissez un nombre entre {minimum} et {maximum}.")


def ajouter_ligne_csv(chemin, entete, ligne):
    """Ajoute une ligne à un CSV. Écrit d'abord l'en-tête si le fichier n'existe pas"""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    nouveau = not chemin.exists()
    with open(chemin, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if nouveau:
            writer.writerow(entete)
        writer.writerow(ligne)


def lire_csv(chemin):
    """Lit un CSV et retourne une liste de dictionnaires"""
    try:
        with open(chemin, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []
