"""Classes Question, QuestionVraiFaux et Quiz"""

__author__ = "benach_a"


import random
import time
from bonus.timer import lire_avec_timer
from utils import charger_json, demander_entier


class Question:
    def __init__(self, id, theme, texte, options, reponse):
        self.id = id
        self.theme = theme
        self.texte = texte
        self.options = list(options)
        self.reponse = reponse

    @property
    def texte(self):
        return self._texte

    @texte.setter
    def texte(self, valeur):
        if not valeur or not valeur.strip():
            raise ValueError("L'énoncé d'une question ne peut pas être vide")
        self._texte = valeur.strip()

    def afficher(self):
        print(f"\n[{self.theme}] {self.texte}")
        for i, option in enumerate(self.options, start=1):
            print(f"  {i}. {option}")

    def verifier(self, numero):
        return self.options[numero - 1] == self.reponse


class QuestionVraiFaux(Question):
    """Polymorphisme : affichage différent pour les questions Vrai/Faux"""

    def __init__(self, id, theme, texte, reponse):
        super().__init__(id, theme, texte, ["Vrai", "Faux"], reponse)

    def afficher(self):
        print(f"\n[{self.theme}] (Vrai/Faux) {self.texte}")
        print("  1. Vrai    2. Faux")


class Resultat:
    def __init__(self, theme, bonnes, total, erreurs):
        self.theme = theme
        self.bonnes = bonnes
        self.total = total
        self.erreurs = erreurs

    @property
    def score(self):
        """Score en pourcentage."""
        return round(100 * self.bonnes / self.total) if self.total else 0


def poser_question(question, limite=None):
    """Retourne le numéro choisi (1..n), ou None si le temps est écoulé
    Une saisie invalide est redemandée, mais le temps continue de s'écouler"""
    nb = len(question.options)
    if limite is None:
        return demander_entier("Votre réponse : ", 1, nb)
    fin = time.monotonic() + limite
    while True:
        reste = fin - time.monotonic()
        if reste <= 0:
            return None
        saisie = lire_avec_timer("Votre réponse : ", reste)
        if saisie is None:
            return None
        try:
            choix = int(saisie.strip())
        except ValueError:
            print("Veuillez entrer un nombre")
            continue
        if 1 <= choix <= nb:
            return choix
        print(f"Choisissez un nombre entre 1 et {nb}")


class Quiz:
    """Classe de quiz"""

    def __init__(self, questions, theme="Tous"):
        self.questions = questions
        self.theme = theme

    @classmethod
    def depuis_fichier(cls, chemin, theme=None, nombre=5):
        return cls.depuis_donnees(charger_json(chemin), theme, nombre)

    @classmethod
    def depuis_donnees(cls, donnees, theme=None, nombre=5):
        """Construit un Quiz à partir d'une liste de dictionnaires (fichier JSON ou API)"""
        questions = []
        for d in donnees:
            try:
                if d["options"] == ["Vrai", "Faux"]:
                    q = QuestionVraiFaux(d["id"], d["theme"], d["question"], d["reponse"])
                else:
                    q = Question(d["id"], d["theme"], d["question"], d["options"], d["reponse"])
            except (KeyError, ValueError) as e:
                print(f"Question ignorée (invalide) : {e!r}")
                continue
            if theme is None or q.theme == theme:
                questions.append(q)
        random.shuffle(questions)
        return cls(questions[:nombre], theme or "Tous")

    @staticmethod
    def themes_disponibles(chemin):
        """theme disponible"""
        return sorted({d["theme"] for d in charger_json(chemin) if "theme" in d})

    def jouer(self, limite=None):
        """fonction jouer"""
        bonnes, erreurs = 0, []
        for q in self.questions:
            q.afficher()
            choix = poser_question(q, limite)
            if choix is None:
                print("⏰ Temps écoulé ! Question suivante.")
                erreurs.append((q, "(temps écoulé)"))
            elif q.verifier(choix):
                print("✅ Correct !")
                bonnes += 1
            else:
                print(f"❌ Faux. Bonne réponse : {q.reponse}")
                erreurs.append((q, q.options[choix - 1]))
        return Resultat(self.theme, bonnes, len(self.questions), erreurs)
