#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contrôle de non-régression du générateur.

Pour chaque cours déjà passé au lecteur à 3 volets, relit les pages en
place (index.qmd et chapitres/*.qmd), en extrait les éléments variables
(contenu central, étiquette du chapitre, présentation, ressources liées),
les fait réécrire par lecteur.py, et compare au texte d'origine, octet pour
octet. Les descriptions, déduites du contenu, sont recalculées de même.

Ce contrôle suppose les pages au format du 28/10/2026 (contenu encadré par
les marques de normaliser.py) : lancer d'abord generer_lecteur.py --migres.

Aucun fichier n'est modifié. Code de sortie 0 si tout est identique.

    python scripts/lecteur/verifier_reproduction.py            # tous les cours
    python scripts/lecteur/verifier_reproduction.py algebre-lineaire
"""

import html
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lecteur  # noqa: E402
import normaliser  # noqa: E402
import generer_lecteur  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COURS = os.path.join(RACINE, "cours")


def lire(chemin):
    with open(chemin, encoding="utf-8", newline="") as f:
        return f.read()


def titre_entete(texte):
    m = re.search(r'^(?:pagetitle|title): "((?:[^"\\]|\\.)*)"$', texte, re.M)
    return m.group(1).replace('\\"', '"').replace("\\\\", "\\")


def extraire_chapitre(texte, slug):
    if normaliser.MARQUE_DEBUT not in texte:
        raise ValueError("page au format ancien (relancer generer_lecteur.py)")
    debut = texte.index(normaliser.MARQUE_DEBUT) + len(normaliser.MARQUE_DEBUT) + 1
    fin = texte.index("\n" + normaliser.MARQUE_FIN)
    fragment = texte[debut:fin]
    m = re.search(r'<header class="jm-entete-chapitre" data-etiquette="([^"]*)">', texte)
    etiquette = html.unescape(m.group(1)) if m else None
    droite = texte[texte.index('<div class="jm-lecteur-droite">'):]
    dispo = {cle for cle, _, gabarit in lecteur.RESSOURCES
             if 'class="jm-ressource" href="%s"' % gabarit.format(slug=slug) in droite}
    m = re.search(r'<li><a class="jm-ressource" href="([^"]+)">Vidéo</a></li>', droite)
    video = html.unescape(m.group(1)) if m else None
    return fragment, etiquette, dispo, video


def extraire_accueil(texte):
    return generer_lecteur.presentation(texte)


def verifier_cours(cours, sommaire):
    dossier = os.path.join(COURS, cours)
    chapitres = list(sommaire[cours].items())
    ecarts = []
    index = lire(os.path.join(dossier, "index.qmd"))
    titre = titre_entete(index)
    pres = extraire_accueil(index)
    refait = lecteur.page_accueil(titre, chapitres, pres, normaliser.description_cours(pres))
    if refait != index:
        ecarts.append("index.qmd")
    for i, (slug, _) in enumerate(chapitres):
        chemin = os.path.join(dossier, "chapitres", slug + ".qmd")
        texte = lire(chemin)
        fragment, etiquette, dispo, video = extraire_chapitre(texte, slug)
        description = normaliser.description_chapitre(titre, etiquette, chapitres[i][1], fragment)
        refait = lecteur.page_chapitre(titre, chapitres, i, fragment, dispo, video,
                                       etiquette, description)
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
