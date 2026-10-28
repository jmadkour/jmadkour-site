#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Écrit la liste « Tous les cours » de la page d'accueil (index.qmd), d'après
les pages de niveau, qui restent la seule source de la liste des cours :

    licence.qmd, master.qmd, doctorat.qmd, informatique.qmd

Dans chacune, une ligne « - [**Titre du cours**](cours/<dossier>/index.qmd) »
déclare un cours ; un titre « ## Bloc » (s'il y en a) le range dans un bloc.
Le résultat est écrit entre deux commentaires de index.qmd :

    <!-- accueil:cours:debut ... -->   <!-- accueil:cours:fin -->

Usage (à relancer après avoir ajouté ou renommé un cours) :

    python3 scripts/generer-accueil.py            # écrit index.qmd
    python3 scripts/generer-accueil.py --verifier # n'écrit rien

Il signale aussi les dossiers de cours/ qui ne figurent dans aucune page de
niveau (hors redirections), et les cours cités dont le dossier n'existe pas.
"""

import argparse
import html
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUT = "<!-- accueil:cours:debut"
FIN = "<!-- accueil:cours:fin -->"
EN_TETE = (DEBUT + " : généré par scripts/generer-accueil.py d'après licence.qmd, "
           "master.qmd, doctorat.qmd et informatique.qmd ; ne pas modifier à la main -->")

# (fichier, titre affiché, phrase d'accroche)
NIVEAUX = (
    ("licence.qmd", "Licence",
     "Économie, mathématiques, statistique, puis l'introduction à l'économétrie."),
    ("master.qmd", "Master",
     "Économétrie avancée, économétrie financière et science des données."),
    ("doctorat.qmd", "Doctorat",
     "La gestion des risques financiers, d'après le curriculum FRM."),
    ("informatique.qmd", "Informatique",
     "R, Python, MATLAB, EViews et LaTeX, sans prérequis."),
)

COURS = re.compile(r"^- \[\*\*(.+?)\*\*\]\(cours/([^/)]+)/index\.qmd\)\s*$")
BLOC = re.compile(r"^## (.+?)\s*$")
# Titres de bloc sans intérêt sur l'accueil.
BLOCS_MUETS = {"Les cours"}
# Dossiers de cours/ qui ne sont pas des cours (redirections).
REDIRECTIONS = {"analyse-donnees"}


def _esc(texte):
    return html.escape(texte, quote=False)


def lire(chemin):
    with open(os.path.join(RACINE, chemin), encoding="utf-8", newline="") as f:
        return f.read()


def lire_niveau(fichier):
    """[(titre du bloc ou None, [(titre du cours, dossier), ...]), ...]"""
    blocs, courant = [], None
    for ligne in lire(fichier).splitlines():
        m = BLOC.match(ligne)
        if m:
            courant = (m.group(1), [])
            blocs.append(courant)
            continue
        m = COURS.match(ligne)
        if m:
            if courant is None:
                courant = (None, [])
                blocs.append(courant)
            courant[1].append((m.group(1), m.group(2)))
    return [b for b in blocs if b[1]]


def bloc_html():
    cites, L = [], []
    L.append(EN_TETE)
    L.append('<section class="jm-accueil-cours" aria-labelledby="jm-cours-titre">')
    L.append('<h2 id="jm-cours-titre">Tous les cours</h2>')
    L.append('<div class="jm-niveaux">')
    for fichier, titre, accroche in NIVEAUX:
        blocs = lire_niveau(fichier)
        if not blocs:
            raise SystemExit("%s : aucun cours trouvé" % fichier)
        L.append('<div class="jm-niveau">')
        L.append('<h3><a href="%s">%s</a></h3>' % (fichier[:-4] + ".html", _esc(titre)))
        L.append('<p class="jm-niveau-desc">%s</p>' % _esc(accroche))
        for sous_titre, cours in blocs:
            seul = len(cours) == 1 and cours[0][0] == sous_titre
            if sous_titre and sous_titre not in BLOCS_MUETS and not seul:
                L.append("<h4>%s</h4>" % _esc(sous_titre))
            L.append("<ul>")
            for nom, dossier in cours:
                cites.append(dossier)
                L.append('<li><a href="cours/%s/index.html">%s</a></li>'
                         % (dossier, _esc(nom)))
            L.append("</ul>")
        L.append("</div>")
    L += ["</div>", "</section>", FIN]
    return "\n".join(L), cites


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--verifier", action="store_true", help="n'écrit rien")
    args = p.parse_args()

    bloc, cites = bloc_html()
    index = lire("index.qmd")
    debut = index.find(DEBUT)
    fin = index.find(FIN)
    if debut == -1 or fin == -1:
        raise SystemExit("index.qmd : repères « accueil:cours » introuvables")
    nouveau = index[:debut] + bloc + index[fin + len(FIN):]

    existants = {d for d in os.listdir(os.path.join(RACINE, "cours"))
                 if os.path.isfile(os.path.join(RACINE, "cours", d, "index.qmd"))}
    for d in sorted(existants - set(cites) - REDIRECTIONS):
        print("  cours absent des pages de niveau : cours/%s" % d)
    for d in sorted(set(cites) - existants):
        print("  cours cité mais sans dossier : cours/%s" % d)
    doublons = sorted({d for d in cites if cites.count(d) > 1})
    for d in doublons:
        print("  cours cité plusieurs fois : cours/%s" % d)

    if nouveau == index:
        print("index.qmd : liste des cours à jour (%d cours)." % len(cites))
        return 0
    if args.verifier:
        print("index.qmd : liste des cours à mettre à jour (%d cours)." % len(cites))
        return 0
    with open(os.path.join(RACINE, "index.qmd"), "w", encoding="utf-8", newline="\n") as f:
        f.write(nouveau)
    print("index.qmd : liste des cours écrite (%d cours)." % len(cites))
    return 0


if __name__ == "__main__":
    sys.exit(main())
