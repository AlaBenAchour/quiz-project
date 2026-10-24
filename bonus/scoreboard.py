"""classement global et système de coins."""

__author__ = "benach_a"


import csv
from pathlib import Path


DOSSIER = Path(__file__).parent
CHEMIN = DOSSIER / "scoreboard.csv"
CHEMIN_GLOBAL = DOSSIER / "scoreboardglobal.csv"

ENTETE = ["Utilisateur", "Theme", "Score", "Date"]
ENTETE_GLOBAL = [
    "Utilisateur",
    "ScoreTotal",
    "QuizJoues",
    "Coins",
    "Rang"
]


def ajouter(utilisateur, theme, score, date):
    """Ajoute le résultat d'un quiz dans l'historique"""
    nouveau = not CHEMIN.exists()

    with open(CHEMIN, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if nouveau:
            writer.writerow(ENTETE)

        writer.writerow([utilisateur, theme, score, date])


def coins_gagnes(score):
    """10 coins pour terminer le quiz + bonus selon le score"""
    return 10 + max(0, min(100, int(score))) // 20


def obtenir_rang(score_total):
    """Détermine le rang selon le total des scores"""
    if score_total >= 500:
        return "Alpha"
    elif score_total >= 200:
        return "Beta"
    return "Oméga"


def actualiser_global():
    """Recalcule le classement global depuis scoreboard.csv"""
    utilisateurs = {}

    try:
        with open(CHEMIN, newline="", encoding="utf-8") as f:
            lignes = csv.DictReader(f)

            for ligne in lignes:
                try:
                    nom = ligne["Utilisateur"].strip()
                    score = max(0, min(100, int(ligne["Score"])))
                except (KeyError, ValueError, TypeError):
                    continue

                if not nom:
                    continue

                if nom not in utilisateurs:
                    utilisateurs[nom] = {
                        "ScoreTotal": 0,
                        "QuizJoues": 0,
                        "Coins": 0
                    }

                utilisateurs[nom]["ScoreTotal"] += score
                utilisateurs[nom]["QuizJoues"] += 1
                utilisateurs[nom]["Coins"] += coins_gagnes(score)

    except FileNotFoundError:
        pass

    classement = []

    for nom, donnees in utilisateurs.items():
        classement.append({
            "Utilisateur": nom,
            **donnees,
            "Rang": obtenir_rang(donnees["ScoreTotal"])
        })

    classement.sort(
        key=lambda u: (u["ScoreTotal"], u["Coins"]),
        reverse=True
    )

    CHEMIN_GLOBAL.parent.mkdir(parents=True, exist_ok=True)

    with open(
        CHEMIN_GLOBAL, "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=ENTETE_GLOBAL)
        writer.writeheader()
        writer.writerows(classement)

    return classement


def classement(limite=10):
    """Retourne les meilleurs résultats individuels"""
    try:
        with open(CHEMIN, newline="", encoding="utf-8") as f:
            lignes = list(csv.DictReader(f))
    except FileNotFoundError:
        return []

    lignes.sort(
        key=lambda ligne: int(ligne.get("Score", 0)),
        reverse=True
    )
    return lignes[:limite]


def classement_global(limite=10):
    """Actualise le CSV global et retourne les meilleurs utilisateurs"""
    return actualiser_global()[:limite]


def afficher_classement(limite=10):
    """Affiche le classement général des utilisateurs"""
    resultats = classement_global(limite)

    print("\n========== CLASSEMENT GLOBAL ==========")

    if not resultats:
        print("Aucun résultat enregistré.")
        return

    for position, utilisateur in enumerate(resultats, start=1):
        print(
            f"{position}. {utilisateur['Utilisateur']} | "
            f"🏆 Score total : {utilisateur['ScoreTotal']} | "
            f"💰 Coins : {utilisateur['Coins']} | "
            f"🏆 Quiz : {utilisateur['QuizJoues']} | "
            f"⭐ Rang : {utilisateur['Rang']}"
        )
