"""Interface Textual du quiz (remplace main.py)"""

__author__ = "benach_a"

import asyncio
from datetime import datetime

from rich.markup import escape
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from bonus import scoreboard
from bonus.api import CATEGORIES, ErreurAPI, charger_questions_api, compter_toutes_categories
from bonus.timer import (charger_date_debut, formater_duree, quiz_est_ouvert,
                         sauvegarder_date_debut, temps_restant)
from config import (DATE_DEBUT_QUIZ, FORMAT_DATE, LIMITE_SECONDES, PARAMETRES,
                    QUESTIONS, UTILISATEURS)
from quiz import Quiz, Resultat
from user import GestionnaireUtilisateurs
from utils import charger_json
from config import TOUS




class ChoixScreen(ModalScreen):
    """Fenêtre de choix dans une liste. Retourne la valeur choisie, ou None (Échap)"""

    BINDINGS = [("escape", "annuler", "Annuler")]

    def __init__(self, titre, choix):
        super().__init__()
        self.titre = titre
        self.choix = choix

    def compose(self) -> ComposeResult:
        with Vertical(id="dialogue"):
            yield Label(self.titre, classes="titre")
            yield OptionList(*[Option(escape(lib)) for lib, _ in self.choix])
            yield Label("Entrée : valider  |  Échap : annuler", classes="aide")

    @on(OptionList.OptionSelected)
    def choisi(self, event: OptionList.OptionSelected):
        self.dismiss(self.choix[event.option_index][1])

    def action_annuler(self):
        self.dismiss(None)


class TexteScreen(Screen):
    """Affiche un texte (résultats, résumé…) avec un bouton Retour"""

    BINDINGS = [("escape", "retour", "Retour")]

    def __init__(self, titre, texte):
        super().__init__()
        self.titre = titre
        self.texte = texte

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(classes="boite"):
            yield Label(self.titre, classes="titre")
            yield Static(self.texte, markup=True)
            yield Button("Retour", variant="primary", id="retour")
        yield Footer()

    @on(Button.Pressed, "#retour")
    def action_retour(self):
        self.dismiss()



class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="boite"):
            yield Label("Connexion", classes="titre")
            yield Input(placeholder="Login", id="login")
            yield Input(placeholder="Mot de passe", password=True, id="mdp")
            yield Button("Connexion", variant="primary", id="ok")
            yield Label("", id="erreur", classes="erreur")
        yield Footer()

    @on(Input.Submitted)
    @on(Button.Pressed, "#ok")
    def connexion(self):
        login = self.query_one("#login", Input).value.strip()
        mdp = self.query_one("#mdp", Input).value
        utilisateur = self.app.gestionnaire.authentifier(login, mdp)
        if utilisateur is None:
            self.query_one("#erreur", Label).update("Login ou mot de passe incorrect.")
            return
        self.app.utilisateur = utilisateur
        self.app.notify(f"Connexion réussie. Bienvenue {utilisateur.login} !")
        if utilisateur.est_admin:
            self.app.switch_screen(AdminScreen())
        else:
            self.app.switch_screen(MenuScreen())



def texte_resultats(utilisateur):
    lignes = []
    dernier = utilisateur.dernier_score
    if dernier is None:
        lignes.append("Aucun résultat sauvegardé pour l'instant.")
    else:
        lignes += ["[bold blue]Dernier résultat[/bold blue]",
                   f"📅 [bold magenta]Date   :[/bold magenta] {dernier['date']}",
                   f"🎨 [bold magenta]Thème  :[/bold magenta] {dernier['theme']}",
                   f"🏆 [bold magenta]Score  :[/bold magenta] {dernier['score']}%"]

    classement = scoreboard.actualiser_global()
    profil = next((u for u in classement if u["Utilisateur"] == utilisateur.login), None)
    lignes.append("")
    if profil:
        position = next(i for i, u in enumerate(classement, start=1)
                        if u["Utilisateur"] == utilisateur.login)
        lignes += ["[bold blue]Statistiques globales[/bold blue]",
                   f"🎮 [bold magenta]Quiz joués      :[/bold magenta] {profil['QuizJoues']}",
                   f"📊 [bold magenta]Score total     :[/bold magenta] {profil['ScoreTotal']}",
                   f"💰 [bold magenta]Coins accumulés :[/bold magenta] {profil['Coins']}",
                   f"⭐ [bold magenta]Rang            :[/bold magenta] {profil['Rang']}",
                   f"🏆 [bold magenta]Classement      :[/bold magenta] {position}/{len(classement)}"]
    else:
        lignes.append("Aucune statistique globale disponible.")
    return "\n".join(lignes)


def texte_classement(limite=10):
    resultats = scoreboard.classement_global(limite)
    if not resultats:
        return "Aucun résultat enregistré."
    return "\n".join(
        f"{i}. {u['Utilisateur']} | 🏆 {u['ScoreTotal']} | 💰 {u['Coins']} | "
        f"Quiz : {u['QuizJoues']} | ⭐ {u['Rang']}"
        for i, u in enumerate(resultats, start=1)
    )


class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="boite"):
            yield Label("Menu", classes="titre")
            yield Label(self.statut(), id="statut")
            yield Button("Jouer", variant="primary", id="jouer")
            yield Button("Voir mes résultats", id="resultats")
            yield Button("Quitter", variant="error", id="quitter")
        yield Footer()

    @staticmethod
    def statut():
        debut = charger_date_debut(PARAMETRES, DATE_DEBUT_QUIZ)
        if quiz_est_ouvert(debut):
            return "[bold green]C'est bon, vous pouvez commencer le quiz ![/bold green]"
        return (f"[bold red]Quiz fermé. Début le {debut.strftime('%d/%m/%Y à %H:%M')}[/bold red] "
                f"(dans {formater_duree(temps_restant(debut))}).")

    @on(Button.Pressed, "#resultats")
    def voir_resultats(self):
        u = self.app.utilisateur
        self.app.push_screen(TexteScreen(f"Resumé de {u.login.upper()}", texte_resultats(u)))

    @on(Button.Pressed, "#quitter")
    def quitter(self):
        self.app.exit()

    @on(Button.Pressed, "#jouer")
    def jouer(self):
        self.query_one("#statut", Label).update(self.statut())
        debut = charger_date_debut(PARAMETRES, DATE_DEBUT_QUIZ)
        if not quiz_est_ouvert(debut):
            self.app.notify("Quiz introuvable : l'heure du quiz n'est pas encore arrivée",
                            severity="error")
            return
        self.lancer()

    @work
    async def lancer(self):
        app = self.app
        quiz = None

        source = await app.push_screen_wait(ChoixScreen(
            "Source des questions",
            [("Fichier local", "local"),
             ("Internet (Open Trivia DB, en anglais)", "api")]))
        if source is None:
            return

        if source == "api":
            nombres = await asyncio.to_thread(compter_toutes_categories)
            choix = [(f"{nom} ({nombres[nom]} questions)" if nom in nombres else nom, nom)
                     for nom in CATEGORIES]
            choix.append(("Toutes les catégories", TOUS))
            cat = await app.push_screen_wait(ChoixScreen("Catégories Internet", choix))
            if cat is None:
                return
            nom, code = ("Internet", None) if cat == TOUS else (cat, CATEGORIES[cat])
            try:
                donnees = await asyncio.to_thread(charger_questions_api, 5, code, nom)
                quiz = Quiz.depuis_donnees(donnees, nom, 5)
            except ErreurAPI as e:
                app.notify(f"Erreur API : {e}. Utilisation des questions locales.",
                           severity="error")

        if quiz is None:
            try:
                donnees = charger_json(QUESTIONS)
            except FileNotFoundError:
                app.notify("Erreur : fichier des questions introuvable.", severity="error")
                return
            nombres = {}
            for d in donnees:
                if "theme" in d:
                    nombres[d["theme"]] = nombres.get(d["theme"], 0) + 1
            choix = [(f"{t} ({n} questions)", t) for t, n in sorted(nombres.items())]
            choix.append((f"Tous les thèmes ({sum(nombres.values())} questions)", TOUS))
            theme = await app.push_screen_wait(ChoixScreen("Thèmes disponibles", choix))
            if theme is None:
                return
            quiz = Quiz.depuis_donnees(donnees, None if theme == TOUS else theme, 5)

        if not quiz.questions:
            app.notify("Aucune question disponible.", severity="warning")
            return

        res = await app.push_screen_wait(QuizScreen(quiz))
        await self.terminer(res)

    async def terminer(self, res: Resultat):
        app = self.app
        u = app.utilisateur
        entree = u.ajouter_score(res.theme, res.score)
        app.gestionnaire.sauvegarder()
        scoreboard.ajouter(u.login, res.theme, res.score, entree["date"])
        coins = scoreboard.coins_gagnes(res.score)
        classement = scoreboard.actualiser_global()
        profil = next((p for p in classement if p["Utilisateur"] == u.login), None)

        lignes = [f"[bold red]Score :[/bold red] {res.score}% ({res.bonnes}/{res.total} correctes, "
                  f"{len(res.erreurs)} incorrectes)", ""]
        for q, donnee in res.erreurs:
            lignes += [f" - {q.texte}",
                       f"   Votre réponse : {donnee} | Bonne réponse : {q.reponse}"]
        lignes += ["", f"🎁 Coins gagnés : +{coins}"]
        if profil:
            lignes += [f"💰 Total de coins : {profil['Coins']}",
                       f"🏆 Score total : {profil['ScoreTotal']}",
                       f"⭐ Rang : {profil['Rang']}"]
        lignes += ["", "[bold green]Résultat sauvegardé[/bold green]", "",
                   "[bold blue]Classement Global[/bold blue]", texte_classement()]
        await app.push_screen_wait(TexteScreen("Resume", "\n".join(lignes)))
        self.query_one("#statut", Label).update(self.statut())



class OptionBouton(Button):
    def __init__(self, texte, numero):
        super().__init__(f"{numero}. {escape(texte)}", classes="option")
        self.numero = numero


class QuizScreen(Screen):
    def __init__(self, quiz: Quiz):
        super().__init__()
        self.quiz = quiz
        self.index = 0
        self.bonnes = 0
        self.erreurs = []
        self.reste = LIMITE_SECONDES
        self.occupe = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="boite"):
            yield Label("", id="progression", classes="titre")
            yield Static("", id="question", markup=False)
            yield Vertical(id="options")
            yield Label("", id="chrono")
            yield Label("", id="feedback")
        yield Footer()

    async def on_mount(self):
        await self.afficher_question()
        self.set_interval(1, self.tick)

    async def afficher_question(self):
        q = self.quiz.questions[self.index]
        self.query_one("#progression", Label).update(
            f"Quiz « {escape(self.quiz.theme)} » - Question "
            f"{self.index + 1}/{len(self.quiz.questions)}")
        suffixe = "(Vrai/Faux) " if q.__class__.__name__ == "QuestionVraiFaux" else ""
        self.query_one("#question", Static).update(f"[{q.theme}] {suffixe}{q.texte}")
        self.query_one("#feedback", Label).update("")
        conteneur = self.query_one("#options", Vertical)
        await conteneur.remove_children()
        await conteneur.mount(*[OptionBouton(o, i) for i, o in enumerate(q.options, start=1)])
        self.reste = LIMITE_SECONDES
        self.maj_chrono()
        self.occupe = False

    def maj_chrono(self):
        self.query_one("#chrono", Label).update(f"Temps restant : {self.reste:2d}s")

    async def tick(self):
        if self.occupe:
            return
        self.reste -= 1
        self.maj_chrono()
        if self.reste <= 0:
            await self.repondre(None)

    @on(Button.Pressed, ".option")
    async def bouton(self, event: Button.Pressed):
        await self.repondre(event.button.numero)

    async def on_key(self, event):
        q = self.quiz.questions[self.index]
        if event.key.isdigit() and 1 <= int(event.key) <= len(q.options):
            await self.repondre(int(event.key))

    async def repondre(self, choix):
        """choix : numéro (1..n) ou None si le temps est écoulé"""
        if self.occupe:
            return
        self.occupe = True
        q = self.quiz.questions[self.index]
        feedback = self.query_one("#feedback", Label)
        if choix is None:
            self.erreurs.append((q, "(temps écoulé)"))
            feedback.update("Temps écoulé ! Question suivante.")
        elif q.verifier(choix):
            self.bonnes += 1
            feedback.update("[bold green]Correct ![/bold green]")
        else:
            self.erreurs.append((q, q.options[choix - 1]))
            feedback.update(f"[bold red]Faux. Bonne réponse : {escape(q.reponse)}[/bold red]")

        await asyncio.sleep(1.2)
        self.index += 1
        if self.index >= len(self.quiz.questions):
            self.dismiss(Resultat(self.quiz.theme, self.bonnes,
                                  len(self.quiz.questions), self.erreurs))
            return
        await self.afficher_question()



class AdminScreen(Screen):
    def compose(self) -> ComposeResult:
        actuelle = charger_date_debut(PARAMETRES, DATE_DEBUT_QUIZ)
        yield Header(show_clock=True)
        with VerticalScroll(classes="boite"):
            yield Label("Menu Admin", classes="titre")
            yield Label("1. Ajouter un utilisateur")
            yield Input(placeholder="Nouveau login", id="nouveau_login")
            yield Input(placeholder="Mot de passe", password=True, id="nouveau_mdp")
            yield Button("Ajouter", variant="primary", id="ajouter")
            yield Label(f"2. Changer la date du quiz (actuelle : "
                        f"{actuelle.strftime(FORMAT_DATE)})", id="date_actuelle")
            yield Input(placeholder="JJ/MM/AAAA HH:MM", id="date")
            yield Button("Changer la date", variant="primary", id="changer")
            yield Button("Quitter", variant="error", id="quitter")
        yield Footer()

    @on(Button.Pressed, "#ajouter")
    def ajouter(self):
        login = self.query_one("#nouveau_login", Input)
        mdp = self.query_one("#nouveau_mdp", Input)
        try:
            self.app.gestionnaire.ajouter(self.app.utilisateur, login.value, mdp.value)
        except (ValueError, PermissionError) as e:
            self.app.notify(f"Erreur : {e}", severity="error")
            return
        self.app.notify(f"Utilisateur « {login.value.strip()} » ajouté avec succès.")
        login.value = ""
        mdp.value = ""

    @on(Button.Pressed, "#changer")
    def changer_date(self):
        if not self.app.utilisateur.est_admin:
            self.app.notify("Seul l'admin peut changer la date du quiz", severity="error")
            return
        champ = self.query_one("#date", Input)
        try:
            nouvelle = datetime.strptime(champ.value.strip(), FORMAT_DATE)
        except ValueError:
            self.app.notify("Format invalide. Exemple : 24/10/2026 09:30", severity="error")
            return
        sauvegarder_date_debut(PARAMETRES, nouvelle)
        self.query_one("#date_actuelle", Label).update(
            f"2. Changer la date du quiz (actuelle : {nouvelle.strftime(FORMAT_DATE)})")
        self.app.notify(f"Date du quiz modifiée : {nouvelle.strftime(FORMAT_DATE)}")
        champ.value = ""

    @on(Button.Pressed, "#quitter")
    def quitter(self):
        self.app.exit()



class QuizApp(App):
    TITLE = "QuizApp"

    CSS = """
    Screen { align: center middle; }
    .boite { width: 70; max-width: 100%; height: auto; max-height: 90%;
             border: round $primary; padding: 1 2; }
    .titre {
    text-style: bold;
    text-align: center;
    color: $success;
    margin: 1 2;
    padding: 1 2;
    width: 100%;
}
    .aide { color: $text-muted; margin-top: 1; }
    .erreur { color: $error; }
    Button { margin-top: 1; width: 100%; }
    .option { width: 100%; }
    #feedback { margin-top: 1; text-style: bold; }
    #chrono { margin-top: 1; color: $warning; }
    #question { margin-bottom: 1; }
    ChoixScreen { align: center middle; }
    #dialogue { width: 70; height: auto; max-height: 80%;
                border: round $primary; background: $surface; padding: 1 2; }
    """

    BINDINGS = [
        ("d", "toggle_dark_mode", "Thème clair/sombre"),
    ]

    def __init__(self):
        super().__init__()
        self.gestionnaire = GestionnaireUtilisateurs(UTILISATEURS)
        self.utilisateur = None

    def on_mount(self):
        self.push_screen(LoginScreen())

    def action_toggle_dark_mode(self):
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"


if __name__ == "__main__":
    QuizApp().run()