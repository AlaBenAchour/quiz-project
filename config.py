"""ajouter variable global"""

__author__ = "benach_a"



from pathlib import Path
from datetime import datetime

LOGIN_ADMIN = "admin"
MDP_ADMIN = "admin123"

CHEMIN = Path(__file__).parent / "scoreboard.csv"
UTILISATEURS = Path(__file__).parent / "data" / "utilisateurs.json"
QUESTIONS = Path(__file__).parent / "data" / "questions.json"
PARAMETRES = Path(__file__).parent / "data" / "parametres.json" 
LIMITE_SECONDES = 20   
ENTETE = ["Utilisateur", "Theme", "Score", "Date"]

DATE_DEBUT_QUIZ = datetime(2026, 10, 24, 9, 34)
FORMAT_DATE = "%d/%m/%Y %H:%M" 

VERT = "\033[92m"
ROUGE = "\033[91m"
RESET = "\033[0m"

TOUS = "__tous__"