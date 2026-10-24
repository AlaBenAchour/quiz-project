"""charger des questions depuis l'API Open Trivia Database (opentdb.com)"""

__author__ = "benach_a"


import html
import json
import random
import urllib.parse
import urllib.request


URL = "https://opentdb.com/api.php"
URL_COUNT = "https://opentdb.com/api_count.php"

CATEGORIES = {
    "Culture générale": 9,
    "Informatique": 18,
    "Sciences et nature": 17,
    "Géographie": 22,
    "Histoire": 23,
}

MESSAGES_CODES = {
    1: "pas assez de questions disponibles pour cette demande",
    2: "paramètre invalide",
    5: "trop de requêtes, réessayez dans quelques secondes",
}


class ErreurAPI(Exception):
    """
    Levée quand l'API est inaccessible ou
    renvoie une réponse inutilisable
    """


def _lire_json(url, timeout=10):
    """Appelle une URL et retourne le JSON décodé"""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as reponse:
            return json.load(reponse)
    except OSError as e:
        raise ErreurAPI(f"connexion impossible ({e})") from e
    except ValueError as e:
        raise ErreurAPI("réponse illisible") from e


def compter_questions_api(categorie):
    """Nombre de questions d'une catégorie"""
    url = f"{URL_COUNT}?{urllib.parse.urlencode({'category': categorie})}"
    donnees = _lire_json(url, timeout=5)
    try:
        c = donnees["category_question_count"]
        return {
            "total": c["total_question_count"],
            "facile": c.get("total_easy_question_count"),
            "moyen": c.get("total_medium_question_count"),
            "difficile": c.get("total_hard_question_count"),
        }
    except (KeyError, TypeError, AttributeError) as e:
        raise ErreurAPI("format de réponse inattendu") from e


def compter_toutes_categories():
    """S'arrête à la première erreur"""
    resultat = {}
    for nom, code in CATEGORIES.items():
        try:
            resultat[nom] = compter_questions_api(code)["total"]
        except ErreurAPI:
            break
    return resultat


def charger_questions_api(nombre=5, categorie=None, theme="Internet"):
    """Retourne une liste de dictionnaires au même format que questions.json"""
    params = {"amount": nombre, "type": "multiple"}
    if categorie:
        params["category"] = categorie
    url = f"{URL}?{urllib.parse.urlencode(params)}"

    donnees = _lire_json(url)

    code = donnees.get("response_code", -1)
    if code != 0:
        raise ErreurAPI(MESSAGES_CODES.get(code, f"code d'erreur {code}"))

    try:
        questions = []
        for i, r in enumerate(donnees["results"], start=1):
            bonne = html.unescape(r["correct_answer"])
            options = [html.unescape(x) for x in r["incorrect_answers"]] + [bonne]
            random.shuffle(options)
            questions.append({
                "id": i,
                "theme": theme,
                "question": html.unescape(r["question"]),
                "options": options,
                "reponse": bonne,
            })
    except (KeyError, TypeError) as e:
        raise ErreurAPI("format de réponse inattendu") from e
    return questions
