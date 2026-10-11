#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Écrit les pages du lecteur de chapitres à 3 volets d'un cours :

    cours/<cours>/index.qmd             présentation + sommaire
    cours/<cours>/chapitres/<slug>.qmd  une page par chapitre

Deux usages.

1. Rafraîchir un cours déjà passé au lecteur (le cas courant) :

       python scripts/lecteur/generer_lecteur.py algebre-lineaire
       python scripts/lecteur/generer_lecteur.py --migres

   Le contenu central de chaque chapitre est repris des pages en place ;
   seuls changent le sommaire (titres et ordre de cours/chapitres.yml),
   les liens précédent/suivant, et le volet droit, recalculé d'après les
   fichiers réellement présents sur le disque. À relancer après avoir
   déposé des diapositives, polycopiés, exercices ou applications, ou
   déclaré une vidéo dans cours/liens-video.yml. --migres traite tous les
   cours qui ont déjà un dossier chapitres/.

2. Passer un cours au lecteur, ou remplacer le contenu de ses chapitres :

       python scripts/lecteur/generer_lecteur.py risque-credit --fragments /chemin/fragments

   Le dossier --fragments contient <slug>.html pour chaque chapitre, tel
   que le produit rendre_atelier.py. Si index.qmd est encore au format
   tableau (bloc TABLEAU:DEBUT/FIN), sa présentation et son syllabus sont
   repris, le tableau est remplacé par le lecteur.

Option --verifier : n'écrit rien, dit ce qui changerait.

Les ressources liées depuis le volet droit, pour un chapitre <slug> :

    slides/<slug>.pdf                        Diapositives
    ressources/<slug>-poly.pdf               Polycopié du chapitre
    ressources/<slug>-exercices-corriges.pdf Exercices corrigés
    outils/<slug>.html                       Application interactive

Une ressource absente reste affichée, grisée. C'est voulu : la page se
remet à jour dès qu'on relance ce script une fois le fichier déposé.
"""

import argparse
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lecteur  # noqa: E402
from alleger_svg import alleger_fragment  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COURS = os.path.join(RACINE, "cours")

FIN_PRESENTATION_ANCIENNE = "Chaque chapitre est un diaporama en PDF."
MARQUEUR_TABLEAU = "<!-- TABLEAU:DEBUT -->"


def lire(chemin):
    with open(chemin, encoding="utf-8", newline="") as f:
        return f.read()


def ecrire(chemin, texte):
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)


def titre_entete(texte):
    m = re.search(r'^title:\s*"((?:[^"\\]|\\.)*)"\s*$', texte, re.M)
    if not m:
        m = re.search(r"^title:\s*'?(.*?)'?\s*$", texte, re.M)
        return m.group(1)
    return m.group(1).replace('\\"', '"').replace("\\\\", "\\")


def presentation(index):
    """Markdown de présentation du cours, sans le paragraphe final."""
    if "jm-lecteur" in index:
        centre = index.split("::: {.jm-lecteur-centre}\n", 1)[1]
        centre = centre.rsplit(":::\n::::\n", 1)[0].rstrip("\n")
        if not centre.endswith(lecteur.PARAGRAPHE_ACCUEIL):
            raise SystemExit("index.qmd : paragraphe final du lecteur introuvable")
        return centre[: -len(lecteur.PARAGRAPHE_ACCUEIL)].rstrip("\n")
    # Ancien format : tout ce qui suit l'entête, jusqu'au paragraphe qui
    # annonçait le tableau (ou, à défaut, jusqu'au marqueur du tableau).
    corps = re.split(r"^---\s*$", index, maxsplit=2, flags=re.M)[2]
    for borne in (FIN_PRESENTATION_ANCIENNE, MARQUEUR_TABLEAU):
        i = corps.find(borne)
        if i != -1:
            return corps[:i].strip("\n")
    raise SystemExit("index.qmd : ni lecteur ni bloc TABLEAU — format inconnu")


def fragment_en_place(chemin):
    texte = lire(chemin)
    debut = texte.index('<div class="jm-lecteur-centre">\n') + len('<div class="jm-lecteur-centre">\n')
    fin = texte.index('\n<div class="jm-lecteur-nav">')
    return texte[debut:fin]


def ressources_presentes(dossier, slug):
    presentes = set()
    for cle, _, gabarit in lecteur.RESSOURCES:
        relatif = gabarit.format(slug=slug)[len("../"):]
        if os.path.isfile(os.path.join(dossier, relatif)):
            presentes.add(cle)
    return presentes


def traiter(cours, sommaire, videos, fragments, verifier):
    dossier = os.path.join(COURS, cours)
    if cours not in sommaire:
        raise SystemExit("%s : absent de cours/chapitres.yml" % cours)
    chapitres = list(sommaire[cours].items())
    index_chemin = os.path.join(dossier, "index.qmd")
    index = lire(index_chemin)
    titre = titre_entete(index)
    videos_cours = ((videos.get(cours) or {}).get("chapitres") or {})

    pages = {index_chemin: lecteur.page_accueil(titre, chapitres, presentation(index))}
    manquants = []
    for i, (slug, _) in enumerate(chapitres):
        chemin = os.path.join(dossier, "chapitres", slug + ".qmd")
        if fragments:
            source = os.path.join(fragments, slug + ".html")
            if not os.path.isfile(source):
                raise SystemExit("%s : fragment manquant %s" % (cours, source))
            fragment = lire(source)
        elif os.path.isfile(chemin):
            fragment = fragment_en_place(chemin)
        else:
            raise SystemExit("%s : pas de page %s et pas de --fragments" % (cours, chemin))
        fragment = alleger_fragment(fragment)
        dispo = ressources_presentes(dossier, slug)
        if len(dispo) < len(lecteur.RESSOURCES):
            manquants.append(slug)
        video = (videos_cours.get(slug) or "").strip() or None
        pages[chemin] = lecteur.page_chapitre(titre, chapitres, i, fragment, dispo, video)

    # Pages de chapitre qui ne correspondent plus à aucun slug.
    dossier_ch = os.path.join(dossier, "chapitres")
    attendus = {slug + ".qmd" for slug, _ in chapitres}
    orphelines = sorted(f for f in os.listdir(dossier_ch) if f.endswith(".qmd") and f not in attendus) \
        if os.path.isdir(dossier_ch) else []

    changees = 0
    for chemin, texte in pages.items():
        ancien = lire(chemin) if os.path.isfile(chemin) else None
        if ancien == texte:
            continue
        changees += 1
        if not verifier:
            os.makedirs(os.path.dirname(chemin), exist_ok=True)
            ecrire(chemin, texte)
    etat = "à mettre à jour" if verifier else "écrite(s)"
    note = ""
    if manquants:
        note += "  ressources incomplètes : %d chapitre(s)" % len(manquants)
    print("  %-32s %3d pages, %3d %s%s" % (cours, len(pages), changees, etat, note))
    for o in orphelines:
        print("      orpheline (absente de chapitres.yml) : chapitres/%s" % o)
    return changees


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("cours", nargs="*", help="dossier(s) sous cours/")
    p.add_argument("--migres", action="store_true", help="tous les cours déjà au lecteur")
    p.add_argument("--fragments", help="dossier des fragments <slug>.html")
    p.add_argument("--verifier", action="store_true", help="n'écrit rien")
    args = p.parse_args()

    sommaire = yaml.safe_load(lire(os.path.join(COURS, "chapitres.yml")))
    chemin_videos = os.path.join(COURS, "liens-video.yml")
    videos = (yaml.safe_load(lire(chemin_videos)) or {}) if os.path.isfile(chemin_videos) else {}

    liste = list(args.cours)
    if args.migres:
        liste += [c for c in sommaire if os.path.isdir(os.path.join(COURS, c, "chapitres")) and c not in liste]
    if not liste:
        p.error("indiquer un cours, ou --migres")
    if args.fragments and len(liste) > 1:
        p.error("--fragments ne s'utilise qu'avec un seul cours")

    total = sum(traiter(c, sommaire, videos, args.fragments, args.verifier) for c in liste)
    print()
    print("%d page(s) %s." % (total, "à mettre à jour" if args.verifier else "écrite(s)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
