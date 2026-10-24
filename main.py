"""connexion et gestion des utilisateurs"""

__author__ = "benach_a"


import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


from datetime import datetime
from user import GestionnaireUtilisateurs
from quiz import Quiz
from config import UTILISATEURS, DATE_DEBUT_QUIZ, PARAMETRES,QUESTIONS, LIMITE_SECONDES
from utils import afficher_vert, afficher_rouge, demander_entier, charger_json
from bonus import scoreboard
from bonus.api import charger_questions_api, compter_toutes_categories, CATEGORIES, ErreurAPI
from bonus.timer import (quiz_est_ouvert, temps_restant, formater_duree,
                         charger_date_debut, sauvegarder_date_debut, FORMAT_DATE)
import getpass


def verifier_quiz(afficher_succes=True):
    """Vérifie si l'heure du quiz est arrivée"""
    date_debut = charger_date_debut(PARAMETRES, DATE_DEBUT_QUIZ)
    if quiz_est_ouvert(date_debut):
        if afficher_succes:
            afficher_vert("C'est bon, vous pouvez commencer le quiz !")
        return True
    debut = date_debut.strftime("%d/%m/%Y à %H:%M")
    reste = formater_duree(temps_restant(date_debut))
    afficher_rouge("Quiz introuvable : l'heure du quiz n'est pas encore arrivée")
    afficher_rouge(f"Début le {debut} (dans {reste}).")
    return False


def changer_date_quiz(admin):
    """Change la date et l'heure du quiz. Réservé à l'admin"""
    if not admin.est_admin:
        raise PermissionError("Seul l'admin peut changer la date du quiz")
    actuelle = charger_date_debut(PARAMETRES, DATE_DEBUT_QUIZ)
    print(f"Date actuelle du quiz : {actuelle.strftime(FORMAT_DATE)}")
    saisie = input("Nouvelle date (JJ/MM/AAAA HH:MM) : ").strip()
    try:
        nouvelle = datetime.strptime(saisie, FORMAT_DATE)
    except ValueError:
        afficher_rouge("Format invalide. Exemple : 24/10/2026 09:30")
        return False
    sauvegarder_date_debut(PARAMETRES, nouvelle)
    afficher_vert(f"Date du quiz modifiée : {nouvelle.strftime(FORMAT_DATE)}")
    return True


def choisir_theme():
    """Choisir theme local"""
    donnees = charger_json(QUESTIONS)
    nombres = {}
    for d in donnees:
        if "theme" in d:
            theme = d["theme"]
            nombres[theme] = nombres.get(theme, 0) + 1

    themes = sorted(nombres)

    print("\nThèmes disponibles :")
    for i, theme in enumerate(themes, start=1):
        print(f"  {i}. {theme} ({nombres[theme]} questions)")

    total = sum(nombres.values())
    print(f"  {len(themes) + 1}. Tous les thèmes ({total} questions)")

    n = demander_entier("Votre choix : ", 1, len(themes) + 1)

    return None if n == len(themes) + 1 else themes[n - 1]


def choisir_categorie_api():
    """Choisir theme dans api"""
    noms = list(CATEGORIES)
    nombres = compter_toutes_categories()
    print("\nCatégories Internet :")
    for i, nom in enumerate(noms, start=1):
        info = f" ({nombres[nom]} questions)" if nom in nombres else ""
        print(f"  {i}. {nom}{info}")
    print(f"  {len(noms) + 1}. Toutes les catégories")
    n = demander_entier("Votre choix : ", 1, len(noms) + 1)
    if n == len(noms) + 1:
        return "Internet", None
    return noms[n - 1], CATEGORIES[noms[n - 1]]

def preparer_quiz():
    """Choix de la source : fichier local ou API Open Trivia DB (avec repli sur le local)"""
    print("\nSource des questions :\n  1. Fichier local\n  2. Internet (Open Trivia DB, en anglais)")
    if demander_entier("Votre choix : ", 1, 2) == 2:
        nom, code = choisir_categorie_api()
        try:
            donnees = charger_questions_api(5, code, nom)
            return Quiz.depuis_donnees(donnees, nom, 5)
        except ErreurAPI as e:
            afficher_rouge(f"Erreur API : {e}")
            afficher_rouge("Utilisation des questions locales à la place.")
    return Quiz.depuis_fichier(QUESTIONS, choisir_theme(), nombre=5)


def jouer(utilisateur, gestionnaire):
    """Lance le quiz si la date est arrivée, sinon affiche l'erreur et revient au menu"""
    if not verifier_quiz(afficher_succes=False):
        return
    quiz = preparer_quiz()
    if not quiz.questions:
        print("Aucune question disponible.")
        return
    print(f"\nQuiz « {quiz.theme} » - {LIMITE_SECONDES}s max par question")
    res = quiz.jouer(limite=LIMITE_SECONDES)
    print(f"\n===== RÉSUMÉ =====\nScore : {res.score}% ({res.bonnes}/{res.total} correctes, "
          f"{len(res.erreurs)} incorrectes)")
    for q, donnee in res.erreurs:
        print(f" - {q.texte}\n   Votre réponse : {donnee} | Bonne réponse : {q.reponse}")
    
    entree = utilisateur.ajouter_score(res.theme, res.score)
    gestionnaire.sauvegarder()

    scoreboard.ajouter(
        utilisateur.login,
        res.theme,
        res.score,
        entree["date"]
    )

    coins = scoreboard.coins_gagnes(res.score)

    classement = scoreboard.actualiser_global()

    profil = next(
        (u for u in classement
         if u["Utilisateur"] == utilisateur.login),
        None
    )

    print(f"\n🎁 Coins gagnés : +{coins}")

    if profil:
        print(f"💰 Total de coins : {profil['Coins']}")
        print(f"🏆 Score total : {profil['ScoreTotal']}")
        print(f"⭐ Rang : {profil['Rang']}")

    print("Résultat sauvegardé.")
    scoreboard.afficher_classement()


def voir_dernier_resultat(utilisateur):
    """Affiche le dernier résultat et le résumé global de l'utilisateur"""

    dernier = utilisateur.dernier_score

    print(f"\n===== RÉSUMÉ DE {utilisateur.login.upper()} =====")

    if dernier is None:
        print("Aucun résultat sauvegardé pour l'instant.")

    else:
        print("\n--- Dernier résultat ---")
        print(f"Date   : {dernier['date']}")
        print(f"Thème  : {dernier['theme']}")
        print(f"Score  : {dernier['score']}%")

    classement = scoreboard.actualiser_global()

    profil = next(
        (u for u in classement
         if u["Utilisateur"] == utilisateur.login),
        None
    )

    if profil:
        print("\n--- Statistiques globales ---")
        print(f"Quiz joués      : {profil['QuizJoues']}")
        print(f"Score total     : {profil['ScoreTotal']}")
        print(f"Coins accumulés : {profil['Coins']}")
        print(f"Rang            : {profil['Rang']}")

        position = next(
            i for i, u in enumerate(classement, start=1)
            if u["Utilisateur"] == utilisateur.login
        )

        print(f"Classement      : {position}/{len(classement)}")

    else:
        print("\nAucune statistique globale disponible.")


def menu_utilisateur(utilisateur, gestionnaire):
    """Menu utilisateur"""
    while True:
        print("\n--- MENU ---\n1. Jouer\n2. Voir mes résultats\n3. Quitter")
        choix = demander_entier("Votre choix : ", 1, 3)
        if choix == 1:
            try:
                jouer(utilisateur, gestionnaire)
            except FileNotFoundError:
                afficher_rouge("Erreur : fichier des questions introuvable.")
        elif choix == 2:
            voir_dernier_resultat(utilisateur)
        else:
            print("À bientôt !")
            break


def menu_admin(admin, gestionnaire):
    """Menu admine"""
    while True:
        print("\n--- MENU ADMIN ---")
        print("1. Ajouter un utilisateur")
        print("2. Changer la date du quiz")
        print("3. Quitter")
        choix = input("Votre choix : ").strip()
        if choix == "1":
            login = input("Nouveau login : ")
            mdp = getpass.getpass("Mot de passe : ")
            # mdp = input("Mot de passe : ")
            try:
                gestionnaire.ajouter(admin, login, mdp)
                print(f"Utilisateur « {login.strip()} » ajouté avec succès.")
            except (ValueError, PermissionError) as e:
                print(f"Erreur : {e}")
        elif choix == "2":
            try:
                changer_date_quiz(admin)
            except PermissionError as e:
                print(f"Erreur : {e}")
        elif choix == "3":
            break
        else:
            print("Erreur : choix invalide (1, 2 ou 3).")


def main():
    gestionnaire = GestionnaireUtilisateurs(UTILISATEURS)
    print("=== CONNEXION ===")
    login = input("Login : ").strip()
    mdp = getpass.getpass("Mot de passe : ")

    utilisateur = gestionnaire.authentifier(login, mdp)
    if utilisateur is None:
        print("Erreur : login ou mot de passe incorrect.")
        return
    print(f"Connexion réussie. Bienvenue {utilisateur.login} !")
    if utilisateur.est_admin:
        menu_admin(utilisateur, gestionnaire)
    else:
        verifier_quiz()
        menu_utilisateur(utilisateur, gestionnaire)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nInterruption.")
