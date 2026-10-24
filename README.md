# Quiz Project

## Présentation du projet

`quiz_project` est un projet Python de quiz en ligne de commande avec une interface interactive basée sur **Textual**.  
Le projet utilise notamment :

- `main.py` : point d'entrée principal du projet.
- `quiz_textual.py` : interface interactive du quiz dans le terminal.
- `quiz.py` : logique du quiz.
- `user.py` : gestion des utilisateurs.
- `config.py` : configuration.
- `utils.py` : fonctions utilitaires.
- `bonus/` : fonctionnalités complémentaires, notamment le classement et le chronomètre.
- `data/` : données utilisées par le projet.

## Prérequis

- Python 3 installé.
- Un terminal : Linux (machine distante) ou Windows PowerShell.
- Les bibliothèques Python `rich` et `textual`.

Un environnement virtuel `.venv` permet d'installer les dépendances du projet sans modifier les autres projets Python de la machine. Il faut créer un environnement séparé sur Linux et sur Windows : un environnement virtuel n'est pas portable d'un système à l'autre.

---

## Installation sur la machine distante Linux

Ouvrir un terminal SSH et exécuter les commandes suivantes depuis le répertoire personnel :

```bash
cd ~/quiz_project

# Installer le module venv si nécessaire (Debian/Ubuntu)
sudo apt update
sudo apt install python3-venv

# Créer l'environnement virtuel
python3 -m venv .venv

# Activer l'environnement virtuel
source .venv/bin/activate

# Mettre pip à jour et installer les dépendances
python -m pip install --upgrade pip
python -m pip install rich textual

# Lancer l'interface du quiz
python quiz_textual.py
```

Si le projet contient un fichier `requirements.txt`, on peut installer les dépendances listées avec :

```bash
python -m pip install -r requirements.txt
```

### Quitter l'environnement virtuel sous Linux

```bash
deactivate
```

---

## Installation sur Windows (PowerShell)

Ouvrir PowerShell dans le dossier du projet :

```powershell
cd C:\ala-work-flow\dev-ala\python\quiz_project
```

### Vérifier l'environnement virtuel

Lister le contenu de `.venv` :

```powershell
Get-ChildItem -Force .venv
```

Vérifier que le script d'activation Windows existe :

```powershell
Test-Path .venv\Scripts\Activate.ps1
```

- Si le résultat est `True`, activer l'environnement à l'étape suivante.
- Si le résultat est `False`, l'environnement est absent ou a été créé pour un autre système (par exemple Linux). Recréer alors l'environnement Windows.

### Créer ou recréer `.venv`

**Attention :** la commande de suppression ci-dessous efface uniquement le dossier `.venv` du projet. Vérifier le chemin courant avant de l'exécuter.

```powershell
Remove-Item -Recurse -Force .venv
py -m venv .venv
```

Si `py` n'est pas reconnu, essayer :

```powershell
python -m venv .venv
```

### Activer et installer les dépendances

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install rich textual
```

Si PowerShell bloque l'exécution du script, autoriser les scripts pour la session actuelle seulement, puis réessayer l'activation :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Lancer le quiz sous Windows

```powershell
python quiz_textual.py
```

### Quitter l'environnement virtuel sous Windows

```powershell
deactivate
```

---

## Dépannage

### `ModuleNotFoundError: No module named 'rich'` ou `textual`

Vérifier que `.venv` est activé (le terminal affiche généralement `(.venv)`), puis exécuter :

```bash
python -m pip install rich textual
```

### Le fichier `quiz_textual.py` est introuvable

Vérifier le nom exact du fichier et être dans le dossier `quiz_project` :

```bash
ls
```

Sous PowerShell, utiliser :

```powershell
Get-ChildItem
```

Le nom correct du fichier est `quiz_textual.py` (avec un underscore `_`).

### À retenir

- Linux : `source .venv/bin/activate`
- Windows PowerShell : `.\.venv\Scripts\Activate.ps1`
- Linux et Windows : `deactivate` pour quitter l'environnement virtuel.
- Ne pas copier un dossier `.venv` de Linux vers Windows ou inversement : créer un environnement virtuel séparé sur chaque système.
