#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contrôle de non-régression du générateur.

Pour chaque cours déjà passé au lecteur à 3 volets, relit les pages en
place (index.qmd et chapitres/*.qmd), en extrait les éléments variables
(contenu central, présentation, ressources liées), les fait réécrire par
lecteur.py, et compare au texte d'origine, octet pour octet.

Aucun fichier n'est modifié. Code de sortie 0 si tout est identique.

    python scripts/lecteur/verifier_reproduction.py            # tous les cours
    python scripts/lecteur/verifier_reproduction.py algebre-lineaire
"""

import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lecteur  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COURS = os.path.join(RACINE, "cours")


def lire(chemin):
    with open(chemin, encoding="utf-8", newline="") as f:
        return f.read()


def titre_entete(texte):
    m = re.search(r'^title: "((?:[^"\\]|\\.)*)"$', texte, re.M)
    return m.group(1).replace('\\"', '"').replace("\\\\", "\\")


def extraire_chapitre(texte, slug):
    debut = texte.index('<div class="jm-lecteur-centre">\n') + len('<div class="jm-lecteur-centre">\n')
    fin = texte.index('\n<div class="jm-lecteur-nav">')
    fragment = texte[debut:fin]
    droite = texte[texte.index('<div class="jm-lecteur-droite">'):]
    dispo = {cle for cle, _, gabarit in lecteur.RESSOURCES
             if 'class="jm-ressource" href="%s"' % gabarit.format(slug=slug) in droite}
    m = re.search(r'<li><a class="jm-ressource" href="([^"]+)">Vidéo</a></li>', droite)
    video = m.group(1) if m else None
    return fragment, dispo, video


def extraire_accueil(texte):
    centre = texte.split("::: {.jm-lecteur-centre}\n", 1)[1]
    centre = centre.rsplit(":::\n::::\n", 1)[0]
    if not centre.rstrip("\n").endswith(lecteur.PARAGRAPHE_ACCUEIL):
        raise ValueError("paragraphe final inattendu")
    return centre.rstrip("\n")[: -len(lecteur.PARAGRAPHE_ACCUEIL)].rstrip("\n")


def verifier_cours(cours, sommaire):
    dossier = os.path.join(COURS, cours)
    chapitres = list(sommaire[cours].items())
    ecarts = []
    index = lire(os.path.join(dossier, "index.qmd"))
    titre = titre_entete(index)
    refait = lecteur.page_accueil(titre, chapitres, extraire_accueil(index))
    if refait != index:
        ecarts.append("index.qmd")
    for i, (slug, _) in enumerate(chapitres):
        chemin = os.path.join(dossier, "chapitres", slug + ".qmd")
        texte = lire(chemin)
        fragment, dispo, video = extraire_chapitre(texte, slug)
        refait = lecteur.page_chapitre(titre, chapitres, i, fragment, dispo, video)
        if refait != texte:
            ecarts.append("chapitres/%s.qmd" % slug)
    return len(chapitres) + 1, ecarts


def main():
    sommaire = yaml.safe_load(lire(os.path.join(COURS, "chapitres.yml")))
    demandes = sys.argv[1:] or [
        c for c in sommaire
        if os.path.isdir(os.path.join(COURS, c, "chapitres"))
    ]
    total = 0
    tous = []
    for cours in demandes:
        n, ecarts = verifier_cours(cours, sommaire)
        total += n
        tous += ["%s/%s" % (cours, e) for e in ecarts]
        print("  %-32s %3d pages  %s" % (cours, n, "identiques" if not ecarts else "%d ÉCART(S)" % len(ecarts)))
    print()
    print("%d pages relues, %d écart(s)." % (total, len(tous)))
    for e in tous[:20]:
        print("   ", e)
    return 1 if tous else 0


if __name__ == "__main__":
    sys.exit(main())
