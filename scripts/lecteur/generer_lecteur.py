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
import html
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lecteur  # noqa: E402
import normaliser  # noqa: E402
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
    """Titre du cours : champ « pagetitle » (pages écrites depuis le
    28/10/2026) ou « title » (pages plus anciennes) de l'en-tête."""
    m = re.search(r'^(?:pagetitle|title):\s*"((?:[^"\\]|\\.)*)"\s*$', texte, re.M)
    if not m:
        m = re.search(r"^(?:pagetitle|title):\s*'?(.*?)'?\s*$", texte, re.M)
        return m.group(1)
    return m.group(1).replace('\\"', '"').replace("\\\\", "\\")


def presentation(index):
    """Markdown de présentation du cours, sans le paragraphe final."""
    if "jm-lecteur" in index:
        centre = index.split("::: {.jm-lecteur-centre}\n", 1)[1]
        centre = centre.rsplit(":::\n::::\n", 1)[0].rstrip("\n")
        if not centre.endswith(lecteur.PARAGRAPHE_ACCUEIL):
            raise SystemExit("index.qmd : paragraphe final du lecteur introuvable")
        centre = centre[: -len(lecteur.PARAGRAPHE_ACCUEIL)].rstrip("\n")
        # Bloc-titre visible écrit par lecteur.entete_accueil (depuis le 28/10/2026).
        m = re.match(r"```\{=html\}\n" + re.escape(lecteur.DEBUT_ENTETE_ACCUEIL)
                     + r".*?</header>\n```\n\n", centre, re.S)
        return centre[m.end():] if m else centre
    # Ancien format : tout ce qui suit l'entête, jusqu'au paragraphe qui
    # annonçait le tableau (ou, à défaut, jusqu'au marqueur du tableau).
    corps = re.split(r"^---\s*$", index, maxsplit=2, flags=re.M)[2]
    for borne in (FIN_PRESENTATION_ANCIENNE, MARQUEUR_TABLEAU):
        i = corps.find(borne)
        if i != -1:
            return corps[:i].strip("\n")
    raise SystemExit("index.qmd : ni lecteur ni bloc TABLEAU — format inconnu")


def fragment_en_place(chemin):
    """(fragment normalisé, étiquette) d'une page de chapitre en place.

    Deux états possibles : page écrite depuis le 28/10/2026 (fragment
    encadré par les marques de normaliser.py, étiquette dans l'en-tête), ou
    page plus ancienne (fragment brut, avec son bloc-titre de Quarto, qu'on
    normalise ici)."""
    texte = lire(chemin)
    if normaliser.MARQUE_DEBUT in texte:
        debut = texte.index(normaliser.MARQUE_DEBUT) + len(normaliser.MARQUE_DEBUT) + 1
        fin = texte.index("\n" + normaliser.MARQUE_FIN)
        m = re.search(r'<header class="jm-entete-chapitre" data-etiquette="([^"]*)">', texte)
        return texte[debut:fin], (html.unescape(m.group(1)) if m else None)
    debut = texte.index('<div class="jm-lecteur-centre">\n') + len('<div class="jm-lecteur-centre">\n')
    fin = texte.index('\n<div class="jm-lecteur-nav">')
    return fragment_brut(texte[debut:fin])


def fragment_brut(brut):
    """(fragment normalisé, étiquette) d'un fragment brut du rendu Quarto."""
    return normaliser.normaliser_fragment(brut), normaliser.etiquette_depuis_entete(brut)


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

    texte_presentation = presentation(index)
    pages = {index_chemin: lecteur.page_accueil(
        titre, chapitres, texte_presentation,
        normaliser.description_cours(texte_presentation))}
    manquants = []
    sans_description = []
    for i, (slug, titre_chapitre) in enumerate(chapitres):
        chemin = os.path.join(dossier, "chapitres", slug + ".qmd")
        if fragments:
            source = os.path.join(fragments, slug + ".html")
            if not os.path.isfile(source):
                raise SystemExit("%s : fragment manquant %s" % (cours, source))
            fragment, etiquette = fragment_brut(lire(source))
        elif os.path.isfile(chemin):
            fragment, etiquette = fragment_en_place(chemin)
        else:
            raise SystemExit("%s : pas de page %s et pas de --fragments" % (cours, chemin))
        # Nommer avant d'alléger : le nom ajoute quelques octets, qui peuvent
        # faire franchir à une figure le seuil de l'allègement ; dans l'autre
        # ordre, la page ne serait stable qu'au second passage.
        fragment = alleger_fragment(normaliser.nommer_figures(fragment))
        dispo = ressources_presentes(dossier, slug)
        if len(dispo) < len(lecteur.RESSOURCES):
            manquants.append(slug)
        video = (videos_cours.get(slug) or "").strip() or None
        description = normaliser.description_chapitre(
            titre, etiquette, titre_chapitre, fragment)
        if normaliser.premiere_phrase_utile(fragment) is None:
            sans_description.append(slug)
        pages[chemin] = lecteur.page_chapitre(
            titre, chapitres, i, fragment, dispo, video, etiquette, description)

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
    if sans_description:
        note += "  description de repli : %d chapitre(s)" % len(sans_description)
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
