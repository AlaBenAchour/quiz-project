"""Gestion des utilisateurs"""

__author__ = "benach_a"


import hashlib
from datetime import date 
from utils import charger_json, sauvegarder_json
from config import LOGIN_ADMIN, MDP_ADMIN


def hasher(mot_de_passe):
    """Ne jamais stocker un mot de passe en clair"""
    return hashlib.sha256(mot_de_passe.encode("utf-8")).hexdigest()


class Utilisateur:
    """class utilisateur"""
    def __init__(self, login, mdp_hash, role="user", scores=None):
        self.login = login
        self.mdp_hash = mdp_hash
        self.role = role
        self.scores = scores or []

    @property
    def est_admin(self):
        return self.role == "admin"

    def ajouter_score(self, theme, score):                                # AJOUT
        """Ajoute un score à l'historique et retourne l'entrée créée."""
        entree = {"theme": theme, "score": score, "date": date.today().isoformat()}
        self.scores.append(entree)
        return entree

    @property
    def dernier_score(self):                                              # AJOUT
        """Dernière sauvegarde de l'utilisateur (None s'il n'a jamais joué)."""
        return self.scores[-1] if self.scores else None

    def to_dict(self):
        return {"mot_de_passe": self.mdp_hash, "role": self.role, "scores": self.scores}


class GestionnaireUtilisateurs:
    """Admin par défaut s'il n'existe pas encore"""
    def __init__(self, chemin):
        self.chemin = chemin
        brut = charger_json(chemin, defaut={})
        self.utilisateurs = {
            login: Utilisateur(login, d.get("mot_de_passe"), d.get("role", "user"), d.get("scores", []))
            for login, d in brut.items()
        }
        if LOGIN_ADMIN not in self.utilisateurs:
            self.utilisateurs[LOGIN_ADMIN] = Utilisateur(LOGIN_ADMIN, hasher(MDP_ADMIN), "admin")
            self.sauvegarder()

    def sauvegarder(self):
        sauvegarder_json(self.chemin, {l: u.to_dict() for l, u in self.utilisateurs.items()})

    def authentifier(self, login, mot_de_passe):
        """Retourne l'Utilisateur si login + mot de passe corrects, sinon None."""
        utilisateur = self.utilisateurs.get(login)
        if utilisateur and utilisateur.mdp_hash == hasher(mot_de_passe):
            return utilisateur
        return None

    def ajouter(self, demandeur, login, mot_de_passe):
        """Ajoute un utilisateur. Seul un admin a le droit"""
        if not demandeur.est_admin:
            raise PermissionError("Seul l'admin peut ajouter un utilisateur.")
        login = login.strip()
        if not login or not mot_de_passe:
            raise ValueError("Le login et le mot de passe ne peuvent pas être vides.")
        if login in self.utilisateurs:
            raise ValueError(f"Le login « {login} » existe déjà.")
        self.utilisateurs[login] = Utilisateur(login, hasher(mot_de_passe))
        self.sauvegarder()
