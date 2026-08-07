#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dégroupe les ressources communes des diaporamas reveal.js.

Les diaporamas sont produits dans le dépôt « stats-eco-cours » avec
``embed-resources: true`` : chaque fichier est autonome, ce qui est
souhaitable pour les distribuer un par un, mais désastreux sur le site,
où les mêmes 3,2 Mo de polices et de moteur reveal.js se retrouvent
recopiés dans chacun des diaporamas.

Ce script sort ces blocs identiques dans « cours/diapos-communs/ » et les
remplace, dans chaque diaporama, par une référence vers la copie unique.
Le rendu est inchangé : mêmes ressources, même ordre de chargement.

Usage :
    python scripts/degrouper-diapos.py            # traite tout
    python scripts/degrouper-diapos.py --verifier  # n'écrit rien, rapporte

À relancer après avoir copié un nouveau diaporama depuis stats-eco-cours.
Le script est idempotent : un diaporama déjà dégroupé est ignoré.
"""

import glob
import os
import re
import sys
from urllib.parse import unquote

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMUN = os.path.join(RACINE, "cours", "diapos-communs")
MOTIF_DECKS = os.path.join(RACINE, "cours", "*", "slides", "*.html")

# Un bloc n'est extrait que s'il dépasse ce seuil : en dessous, la
# référence externe coûterait plus cher que le gain.
SEUIL = 15000

RE_LINK_POLICES = re.compile(
    r'<link[^>]*href="data:text/css,%40font%2Dface[^"]*"[^>]*>'
)
RE_SCRIPT = re.compile(r"<script>(.*?)</script>", re.S)
RE_STYLE = re.compile(r'<style type="text/css">(.*?)</style>', re.S)


def decks():
    return sorted(glob.glob(MOTIF_DECKS))


def lire(chemin):
    with open(chemin, encoding="utf-8", errors="replace") as f:
        return f.read()


def ecrire(chemin, texte):
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        f.write(texte)


# ---------------------------------------------------------------------
# 1. Extraction : constituer le dossier commun à partir d'un diaporama
#    encore intact.
# ---------------------------------------------------------------------

def extraire(reference):
    """Écrit les ressources partagées et renvoie la liste des blocs."""
    txt = lire(reference)
    os.makedirs(COMMUN, exist_ok=True)
    blocs = []  # (tag_original, nom_fichier, genre)

    m = RE_LINK_POLICES.search(txt)
    if m and len(m.group(0)) > SEUIL:
        css = unquote(m.group(0).split('href="data:text/css,', 1)[1].rsplit('"', 1)[0])
        ecrire(os.path.join(COMMUN, "polices.css"), css)
        blocs.append((m.group(0), "polices.css", "css"))

    for i, m in enumerate(RE_STYLE.finditer(txt), 1):
        if len(m.group(1)) > SEUIL:
            nom = "reveal-%02d.css" % i
            ecrire(os.path.join(COMMUN, nom), m.group(1))
            blocs.append((m.group(0), nom, "css"))

    for i, m in enumerate(RE_SCRIPT.finditer(txt), 1):
        if len(m.group(1)) > SEUIL:
            nom = "reveal-%02d.js" % i
            ecrire(os.path.join(COMMUN, nom), m.group(1))
            blocs.append((m.group(0), nom, "js"))

    return blocs


def recomposer():
    """Reconstitue les blocs originaux à partir du dossier commun.

    Permet de traiter un nouveau diaporama sans disposer d'un fichier
    de référence intact.
    """
    blocs = []
    for nom in sorted(os.listdir(COMMUN)):
        chemin = os.path.join(COMMUN, nom)
        if nom == "polices.css":
            continue  # repéré par motif, pas par contenu
        charge = lire(chemin)
        if nom.endswith(".js"):
            blocs.append(("<script>" + charge + "</script>", nom, "js"))
        elif nom.endswith(".css"):
            blocs.append(
                ('<style type="text/css">' + charge + "</style>", nom, "css")
            )
    return blocs


# ---------------------------------------------------------------------
# 2. Réécriture des diaporamas
# ---------------------------------------------------------------------

def reference_relative(deck):
    """Chemin relatif du dossier commun, vu depuis un diaporama."""
    return os.path.relpath(COMMUN, os.path.dirname(deck)).replace(os.sep, "/")


def balise(nom, genre, prefixe):
    cible = "%s/%s" % (prefixe, nom)
    if genre == "js":
        return '<script src="%s"></script>' % cible
    return '<link rel="stylesheet" href="%s">' % cible


def traiter(deck, blocs, ecrire_reellement=True):
    txt = lire(deck)
    if "diapos-communs/" in txt:
        return None  # déjà dégroupé
    prefixe = reference_relative(deck)
    avant = len(txt)
    manquants = []

    for original, nom, genre in blocs:
        if nom == "polices.css":
            m = RE_LINK_POLICES.search(txt)
            if not m or len(m.group(0)) <= SEUIL:
                manquants.append(nom)
                continue
            txt = txt.replace(m.group(0), balise(nom, genre, prefixe), 1)
        else:
            if txt.count(original) != 1:
                manquants.append(nom)
                continue
            txt = txt.replace(original, balise(nom, genre, prefixe), 1)

    if manquants:
        return ("incomplet", manquants, avant, len(txt))
    if ecrire_reellement:
        ecrire(deck, txt)
    return ("ok", [], avant, len(txt))


def main():
    verif = "--verifier" in sys.argv
    liste = decks()
    if not liste:
        print("Aucun diaporama trouvé sous cours/*/slides/.")
        return 1

    intacts = [d for d in liste if "diapos-communs/" not in lire(d)]
    if not os.path.isdir(COMMUN) or not os.listdir(COMMUN):
        if not intacts:
            print("Rien à faire : tous les diaporamas sont déjà dégroupés.")
            return 0
        blocs = extraire(intacts[0])
        print("Ressources partagées extraites de %s :" % os.path.relpath(intacts[0], RACINE))
        for _, nom, _ in blocs:
            print("   %-16s %8.0f ko" % (nom, os.path.getsize(os.path.join(COMMUN, nom)) / 1024))
    else:
        blocs = recomposer()
        polices = os.path.join(COMMUN, "polices.css")
        if os.path.exists(polices):
            blocs.insert(0, (None, "polices.css", "css"))
        print("Ressources partagées déjà présentes (%d fichiers)." % len(blocs))

    gagne = 0
    faits = deja = rates = 0
    for d in liste:
        r = traiter(d, blocs, ecrire_reellement=not verif)
        if r is None:
            deja += 1
            continue
        etat, manquants, avant, apres = r
        if etat == "ok":
            faits += 1
            gagne += avant - apres
        else:
            rates += 1
            print("   ! %s : blocs introuvables %s" % (os.path.relpath(d, RACINE), manquants))

    print()
    print("%d diaporama(s) traité(s), %d déjà à jour, %d en échec."
          % (faits, deja, rates))
    print("Économie : %.0f Mo%s" % (gagne / 1048576, " (simulation)" if verif else ""))
    return 1 if rates else 0


if __name__ == "__main__":
    sys.exit(main())
