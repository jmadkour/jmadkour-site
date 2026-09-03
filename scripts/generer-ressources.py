#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insère, dans la page de chaque cours, le tableau qui lui sert de sommaire.

Depuis que les diaporamas ne sont plus publiés qu'en PDF, la page du cours
est le seul point d'entrée : elle porte sa présentation, puis un tableau
donnant pour chaque chapitre le lien vers les diapositives, le polycopié,
les exercices et la vidéo. Il n'y a plus de page « Ressources ».

Le tableau est écrit entre deux marqueurs, que la page doit contenir :

    <!-- TABLEAU:DEBUT -->
    <!-- TABLEAU:FIN -->

Tout ce qui se trouve entre les deux est remplacé ; le reste de la page,
écrit à la main, n'est jamais touché.

Sommaire des cours : cours/chapitres.yml
    <cours>:
      <slug du chapitre>: "<titre du chapitre>"
    L'ordre des lignes est l'ordre pédagogique.

Conventions de dépôt des fichiers, pour un chapitre de slug <c>
appartenant au cours <cours> :

    cours/<cours>/slides/<c>.pdf                  diapositives
    cours/<cours>/ressources/<c>-poly.pdf         polycopié du chapitre
    cours/<cours>/ressources/<c>-exercices.pdf    exercices (énoncé, sans le corrigé)
    cours/<cours>/ressources/<c>-corrections.pdf  corrigé des exercices
    cours/<cours>/outils/<c>.html                 application interactive (calculette, graphiques)

Et, pour le cours entier :

    cours/<cours>/ressources/polycopie.pdf            polycopié complet
    cours/<cours>/ressources/exercices.pdf            recueil d'exercices
    cours/<cours>/ressources/exercices-synthese.pdf   exercices de synthèse

Les liens vidéo se déclarent dans cours/liens-video.yml.

Usage :
    python scripts/generer-ressources.py
    python scripts/generer-ressources.py --verifier   # n'écrit rien
"""

import os
import sys

import yaml

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOMMAIRE = os.path.join(RACINE, "cours", "chapitres.yml")
VIDEOS = os.path.join(RACINE, "cours", "liens-video.yml")

DEBUT = "<!-- TABLEAU:DEBUT -->"
FIN = "<!-- TABLEAU:FIN -->"

ANNEXES_CHAPITRE = [
    ("poly", "Polycopié"),
    ("exercices", "Exercices"),
    ("corrections", "Corrigé"),
]

ANNEXES_COURS = [
    ("polycopie.pdf", "Polycopié complet du cours"),
    ("exercices.pdf", "Recueil d'exercices"),
    ("exercices-synthese.pdf", "Exercices de synthèse"),
]


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def lien(dossier, relatif, libelle):
    """Lien vers un fichier, ou tiret s'il n'existe pas encore."""
    if os.path.exists(os.path.join(RACINE, dossier, relatif)):
        return "[%s](%s)" % (libelle, relatif)
    return "—"


def tableau(cours, chapitres, videos):
    """Le bloc à insérer entre les deux marqueurs."""
    d = os.path.join("cours", cours)
    conf = videos.get(cours) or {}
    playlist = (conf.get("playlist") or "").strip()
    par_chapitre = conf.get("chapitres") or {}

    L = []
    L.append("")
    L.append("<!-- Bloc produit par scripts/generer-ressources.py. -->")
    L.append("<!-- Ne pas modifier à la main : déposez les fichiers selon -->")
    L.append("<!-- les conventions décrites en tête du script, puis relancez. -->")
    L.append("")
    L.append("## Chapitres et documents")
    L.append("")
    L.append("| # | Chapitre | Diapositives | Polycopié | Exercices | Corrigé | Application | Vidéo |")
    L.append("|--:|---|---|---|---|---|---|---|")

    manquants = 0
    for i, (slug, titre) in enumerate(chapitres.items(), 1):
        pdf = lien(d, "slides/%s.pdf" % slug, "PDF")
        if pdf == "—":
            manquants += 1
        cells = [str(i), titre, pdf]
        for suffixe, _ in ANNEXES_CHAPITRE:
            cells.append(lien(d, "ressources/%s-%s.pdf" % (slug, suffixe), "PDF"))
        cells.append(lien(d, "outils/%s.html" % slug, "Ouvrir"))
        url = (par_chapitre.get(slug) or "").strip()
        cells.append("[Voir](%s)" % url if url else "—")
        L.append("| " + " | ".join(cells) + " |")

    L.append("")

    globaux = [
        (nom, libelle)
        for nom, libelle in ANNEXES_COURS
        if os.path.exists(os.path.join(RACINE, d, "ressources", nom))
    ]
    if globaux:
        L.append("## Le cours entier")
        L.append("")
        for nom, libelle in globaux:
            L.append("- [%s](ressources/%s)" % (libelle, nom))
        L.append("")

    if playlist:
        L.append("## En vidéo")
        L.append("")
        L.append(
            "Les séances filmées sont réunies dans une "
            "[playlist YouTube](%s)." % playlist
        )
        L.append("")

    return "\n".join(L), manquants


def inserer(page, bloc):
    """Remplace ce qui se trouve entre les deux marqueurs."""
    i = page.find(DEBUT)
    j = page.find(FIN)
    if i == -1 or j == -1 or j < i:
        return None
    return page[: i + len(DEBUT)] + bloc + page[j:]


def main():
    verif = "--verifier" in sys.argv
    sommaire = yaml.safe_load(lire(SOMMAIRE)) or {}
    videos = yaml.safe_load(lire(VIDEOS)) or {}

    ecrits = 0
    sans_marqueur = []
    total_manquants = 0

    for cours, chapitres in sommaire.items():
        cible = os.path.join(RACINE, "cours", cours, "index.qmd")
        if not os.path.exists(cible):
            print("  ABSENTE   cours/%s/index.qmd" % cours)
            continue

        bloc, manquants = tableau(cours, chapitres, videos)
        total_manquants += manquants

        ancien = lire(cible)
        nouveau = inserer(ancien, bloc)
        if nouveau is None:
            sans_marqueur.append(cours)
            print("  MARQUEURS cours/%s/index.qmd — bloc TABLEAU absent" % cours)
            continue

        etat = "inchangée" if nouveau == ancien else "écrite"
        if nouveau != ancien and not verif:
            with open(cible, "w", encoding="utf-8", newline="\n") as f:
                f.write(nouveau)
            ecrits += 1
        note = "" if manquants == 0 else "  (%d PDF manquant(s))" % manquants
        print("  %-9s cours/%-34s %2d chapitres%s"
              % (etat, cours + "/index.qmd", len(chapitres), note))

    print()
    print("%d cours, %d page(s) %s."
          % (len(sommaire), ecrits if not verif else 0,
             "mise(s) à jour" if not verif else "à mettre à jour"))
    if total_manquants:
        print("%d chapitre(s) sans PDF : lancer publier.sh depuis le dépôt source."
              % total_manquants)
    if sans_marqueur:
        print("Pages sans marqueurs : " + ", ".join(sans_marqueur))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
