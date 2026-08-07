#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Écrit une page « Ressources » par cours, à partir des fichiers présents.

Depuis que le titre d'un chapitre mène directement à ses diapositives, les
documents annexes sont rassemblés sur une page unique par cours. Ce script
la reconstruit en inspectant le disque : rien à tenir à jour à la main,
il suffit de déposer un fichier au bon endroit et de relancer.

Conventions, pour un chapitre dont les diapositives sont
« cours/<cours>/slides/<chapitre>.html » :

    slides/<chapitre>.pdf                  diapositives en PDF
    ressources/<chapitre>-poly.pdf         polycopié du chapitre
    ressources/<chapitre>-exercices.pdf    exercices corrigés
    ressources/<chapitre>-examen.pdf       examen corrigé

Et, pour le cours entier :

    ressources/polycopie.pdf               polycopié complet
    ressources/exercices.pdf               recueil d'exercices
    ressources/examens.pdf                 annales

Les liens vidéo se déclarent dans cours/liens-video.yml.

Usage :
    python scripts/generer-ressources.py
    python scripts/generer-ressources.py --verifier   # n'écrit rien
"""

import os
import sys

import yaml

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(RACINE, "_quarto.yml")
VIDEOS = os.path.join(RACINE, "cours", "liens-video.yml")

ANNEXES_CHAPITRE = [
    ("poly", "Polycopié"),
    ("exercices", "Exercices"),
    ("examen", "Examen"),
]

ANNEXES_COURS = [
    ("polycopie.pdf", "Polycopié complet du cours"),
    ("exercices.pdf", "Recueil d'exercices corrigés"),
    ("examens.pdf", "Annales d'examens corrigés"),
]


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def cours_du_site():
    """Relève, cours par cours, l'ordre et le titre des chapitres.

    La source de vérité est la barre latérale : c'est elle qui fixe
    l'ordre pédagogique, que la liste des fichiers ne donne pas.
    """
    cfg = yaml.safe_load(lire(CONFIG))
    resultat = []
    for sb in cfg["website"]["sidebar"]:
        entrees = []

        def parcourir(contenu):
            for it in contenu or []:
                if isinstance(it, str):
                    entrees.append(it)
                elif isinstance(it, dict):
                    if isinstance(it.get("href"), str):
                        entrees.append(it["href"])
                    parcourir(it.get("contents"))

        parcourir(sb.get("contents"))

        chapitres = []
        dossier = None
        for e in entrees:
            if not e.startswith("cours/"):
                continue
            d = os.path.dirname(e)
            base = os.path.splitext(os.path.basename(e))[0]
            if base in ("index", "ressources"):
                continue
            deck = os.path.join(RACINE, d, "slides", base + ".html")
            if not os.path.exists(deck):
                continue  # chapitre sans diaporama : cours d'informatique
            dossier = d
            chapitres.append((base, titre_du_chapitre(d, base)))

        if chapitres:
            resultat.append(
                {
                    "id": sb.get("id"),
                    "titre": sb.get("title"),
                    "dossier": dossier,
                    "chapitres": chapitres,
                }
            )
    return resultat


def titre_du_chapitre(dossier, base):
    """Titre lisible du chapitre.

    On le prend dans la page du chapitre tant qu'elle existe ; une fois
    celle-ci retirée, on se rabat sur le titre inscrit dans le diaporama.
    """
    page = os.path.join(RACINE, dossier, base + ".qmd")
    if os.path.exists(page):
        txt = lire(page)
        if txt.startswith("---"):
            try:
                fm = yaml.safe_load(txt.split("---", 2)[1])
                if fm and fm.get("title"):
                    return str(fm["title"])
            except Exception:
                pass

    deck = os.path.join(RACINE, dossier, "slides", base + ".html")
    if os.path.exists(deck):
        with open(deck, encoding="utf-8", errors="replace") as f:
            for ligne in f:
                if "<title>" in ligne:
                    t = ligne.split("<title>", 1)[1].split("</title>")[0]
                    return t.strip()
    return base.replace("-", " ").capitalize()


def lien(dossier, relatif, libelle):
    """Lien vers un fichier, ou tiret s'il n'existe pas encore."""
    if os.path.exists(os.path.join(RACINE, dossier, relatif)):
        return "[%s](%s)" % (libelle, relatif)
    return "—"


def page(cours, videos):
    d = cours["dossier"]
    conf = videos.get(os.path.basename(d)) or {}
    playlist = (conf.get("playlist") or "").strip()
    par_chapitre = conf.get("chapitres") or {}

    L = []
    L.append("---")
    L.append('title: "Ressources — %s"' % cours["titre"])
    L.append("sidebar: %s" % cours["id"])
    L.append("---")
    L.append("")
    L.append(
        "Les documents du cours, chapitre par chapitre. "
        "Les diapositives se consultent en ligne depuis la barre latérale ; "
        "on les retrouve ici en PDF, avec le reste du matériel."
    )
    L.append("")
    L.append("<!-- Page produite par scripts/generer-ressources.py. -->")
    L.append("<!-- Ne pas modifier à la main : déposez les fichiers selon -->")
    L.append("<!-- les conventions décrites en tête du script, puis relancez. -->")
    L.append("")
    L.append("## Par chapitre")
    L.append("")
    L.append("| # | Chapitre | Diapositives | Polycopié | Exercices | Examen | Vidéo |")
    L.append("|--:|---|---|---|---|---|---|")

    for i, (base, titre) in enumerate(cours["chapitres"], 1):
        cells = [str(i), titre]
        cells.append(lien(d, "slides/%s.pdf" % base, "PDF"))
        for suffixe, _ in ANNEXES_CHAPITRE:
            cells.append(lien(d, "ressources/%s-%s.pdf" % (base, suffixe), "PDF"))
        url = (par_chapitre.get(base) or "").strip()
        cells.append("[Voir](%s)" % url if url else "—")
        L.append("| " + " | ".join(cells) + " |")

    L.append("")

    # Documents portant sur le cours entier : la section n'apparaît que
    # si au moins un de ces fichiers existe.
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

    return "\n".join(L) + "\n"


def main():
    verif = "--verifier" in sys.argv
    videos = yaml.safe_load(lire(VIDEOS)) or {}
    liste = cours_du_site()
    if not liste:
        print("Aucun cours à diaporamas trouvé.")
        return 1

    ecrits = 0
    for c in liste:
        cible = os.path.join(RACINE, c["dossier"], "ressources.qmd")
        contenu = page(c, videos)
        ancien = lire(cible) if os.path.exists(cible) else None
        etat = "inchangé" if ancien == contenu else "écrit"
        if ancien != contenu and not verif:
            with open(cible, "w", encoding="utf-8", newline="\n") as f:
                f.write(contenu)
            ecrits += 1
        print(
            "  %-9s %-44s %2d chapitres"
            % (etat, os.path.relpath(cible, RACINE), len(c["chapitres"]))
        )

    print()
    print("%d cours, %d page(s) %s."
          % (len(liste), ecrits if not verif else 0,
             "mise(s) à jour" if not verif else "à mettre à jour"))
    if verif:
        print("(simulation : aucun fichier modifié)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
