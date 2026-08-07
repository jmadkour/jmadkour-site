#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intègre les diaporamas au site : thème accordé et liens de retour.

Les diaporamas sont produits dans « stats-eco-cours », indépendamment du
site. Ce script leur ajoute, juste avant </body>, une feuille de style et
un script partagés qui les font se fondre dans jmadkour.org :

  * cours/diapos-communs/jm-diapos.css  — variante sombre et liens de retour
  * cours/diapos-communs/jm-diapos.js   — bascule du thème, pose des liens

Usage :
    python scripts/integrer-diapos.py             # traite tout
    python scripts/integrer-diapos.py --verifier   # n'écrit rien, rapporte
    python scripts/integrer-diapos.py --retirer    # défait l'intégration

À relancer après avoir copié un nouveau diaporama depuis stats-eco-cours.
Le script est idempotent : un diaporama déjà intégré est ignoré.
"""

import glob
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMUN = os.path.join(RACINE, "cours", "diapos-communs")
MOTIF = os.path.join(RACINE, "cours", "*", "slides", "*.html")

MARQUE_DEBUT = "<!-- jm-integration -->"
MARQUE_FIN = "<!-- /jm-integration -->"


def lire(chemin):
    with open(chemin, encoding="utf-8", errors="replace") as f:
        return f.read()


def ecrire(chemin, texte):
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        f.write(texte)


def bloc(deck):
    """Bloc à insérer, avec des chemins relatifs corrects pour ce diaporama."""
    dossier = os.path.dirname(deck)
    prefixe = os.path.relpath(COMMUN, dossier).replace(os.sep, "/")
    racine = os.path.relpath(RACINE, dossier).replace(os.sep, "/")
    return (
        "\n" + MARQUE_DEBUT + "\n"
        # Les diaporamas sont produits hors du site et n'héritent pas de sa
        # favicône : on la rattache ici, sinon l'onglet perd son identité.
        '<link rel="icon" href="%s/favicon.png">\n'
        '<link rel="stylesheet" href="%s/jm-diapos.css">\n'
        '<script src="%s/jm-diapos.js"></script>\n'
        % (racine, prefixe, prefixe)
        + MARQUE_FIN + "\n"
    )


def deja_integre(txt):
    return MARQUE_DEBUT in txt


def retirer_bloc(txt):
    i = txt.find(MARQUE_DEBUT)
    if i == -1:
        return txt, False
    j = txt.find(MARQUE_FIN, i)
    if j == -1:
        return txt, False
    j += len(MARQUE_FIN)
    # avaler le saut de ligne qui suit, et celui qui précède
    if txt[j : j + 1] == "\n":
        j += 1
    if i > 0 and txt[i - 1] == "\n":
        i -= 1
    return txt[:i] + txt[j:], True


def traiter(deck, ecrire_reellement=True):
    txt = lire(deck)
    if deja_integre(txt):
        return "deja"
    i = txt.rfind("</body>")
    if i == -1:
        return "sans-body"
    nouveau = txt[:i] + bloc(deck) + txt[i:]
    if ecrire_reellement:
        ecrire(deck, nouveau)
    return "ok"


def defaire(deck):
    txt = lire(deck)
    nouveau, fait = retirer_bloc(txt)
    if not fait:
        return "rien"
    ecrire(deck, nouveau)
    return "ok"


def main():
    verif = "--verifier" in sys.argv
    retrait = "--retirer" in sys.argv

    for nom in ("jm-diapos.css", "jm-diapos.js"):
        if not os.path.exists(os.path.join(COMMUN, nom)):
            print("Ressource manquante : cours/diapos-communs/%s" % nom)
            return 1

    decks = sorted(glob.glob(MOTIF))
    if not decks:
        print("Aucun diaporama trouvé sous cours/*/slides/.")
        return 1

    compte = {}
    for d in decks:
        r = defaire(d) if retrait else traiter(d, ecrire_reellement=not verif)
        compte[r] = compte.get(r, 0) + 1
        if r == "sans-body":
            print("   ! %s : pas de </body>" % os.path.relpath(d, RACINE))

    print("%d diaporama(s) examiné(s)" % len(decks))
    for etat, libelle in (
        ("ok", "traité(s)"),
        ("deja", "déjà à jour"),
        ("rien", "sans intégration à retirer"),
        ("sans-body", "en échec"),
    ):
        if compte.get(etat):
            print("   %4d %s" % (compte[etat], libelle))
    if verif:
        print("(simulation : aucun fichier modifié)")
    return 1 if compte.get("sans-body") else 0


if __name__ == "__main__":
    sys.exit(main())
