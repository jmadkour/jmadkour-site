# -*- coding: utf-8 -*-
"""
Gabarits du lecteur de chapitres à 3 volets (pages de cours du site).

Ce module ne fait qu'une chose : écrire, à partir de données déjà prêtes,
le texte exact des pages Quarto du lecteur. Il ne lit ni n'écrit aucun
fichier lui-même ; generer_lecteur.py s'en charge.

    page_chapitre(...)  -> cours/<cours>/chapitres/<slug>.qmd
    page_accueil(...)   -> cours/<cours>/index.qmd

Reconstruit le 11/10/2026 à partir des 399 pages produites en septembre
par l'ancien script ; refondu le 28/10/2026 (voir « Ce qui a changé »).

Ce qui a changé le 28/10/2026 (analyse du site du même jour) :
- chaque chapitre a son propre <title> (« Titre (Cours) – Jaouad Madkour »)
  et sa propre description, au lieu du titre du cours et du sous-titre ;
- chaque page a un seul <h1>, visible : le titre du chapitre, surmonté du
  nom du cours et du numéro du chapitre. Les sections passent en <h2>, les
  sous-sections en <h3> (voir normaliser.py) ;
- le bloc-titre de Quarto n'est plus produit (en-tête « pagetitle » au lieu
  de « title ») ;
- sur téléphone, le sommaire est replié, les ressources du chapitre sont
  juste sous le titre, et le panneau de droite est masqué (le même contenu
  existe sous forme de puces, `jm-ressources-mobile`) ;
- le contenu du chapitre est encadré par deux commentaires HTML
  (normaliser.MARQUE_DEBUT / MARQUE_FIN) pour être retrouvé tel quel.

Choix figés, à ne pas changer sans raison :
- le volet gauche ne numérote pas les chapitres (demande du 25/09/2026) ;
- les titres de chapitre sont échappés pour le HTML (html.escape), le
  titre du cours ne l'est pas (il ne contient jamais < ni &) ;
- une ressource absente reste visible, grisée (« — Diapositives »), pour
  que l'étudiant sache qu'elle viendra (sur téléphone, les puces ne
  montrent que les ressources présentes).
"""

import html

from normaliser import MARQUE_DEBUT, MARQUE_FIN

INCLUDES_CHAPITRE = ("../../../_includes/masquer-titre.html",
                     "../../../_includes/lecteur.html")
INCLUDES_ACCUEIL = ("../../_includes/masquer-titre.html",
                    "../../_includes/lecteur.html")

# (clé, libellé, chemin relatif depuis chapitres/, gabarit du nom de fichier)
RESSOURCES = (
    ("slides", "Diapositives", "../slides/{slug}.pdf"),
    ("poly", "Polycopié du chapitre", "../ressources/{slug}-poly.pdf"),
    ("exercices", "Exercices corrigés", "../ressources/{slug}-exercices-corriges.pdf"),
    ("outil", "Application interactive", "../outils/{slug}.html"),
)

PARAGRAPHE_ACCUEIL = (
    "Chaque chapitre du sommaire, à gauche, ouvre sa page de lecture : le "
    "contenu détaillé au centre, les diapositives, le polycopié, les "
    "exercices corrigés, l'application interactive et la vidéo dans le "
    "panneau de droite."
)

# Bloc-titre de la page d'accueil d'un cours (écrit juste après le sommaire).
DEBUT_ENTETE_ACCUEIL = '<header class="jm-entete-chapitre">'

# Script placé juste après le sommaire : replié sur téléphone, toujours
# ouvert sur ordinateur (le sommaire y est un panneau fixe, pas un menu).
SCRIPT_SOMMAIRE = (
    '<script>(function(){var d=document.currentScript.previousElementSibling,'
    'm=window.matchMedia("(max-width:991px)");if(!d)return;'
    'if(m.matches)d.removeAttribute("open");'
    'd.addEventListener("toggle",function(){if(!m.matches&&!d.open)d.open=true;});'
    '})();</script>'
)


def _yaml(texte):
    """Chaîne YAML entre guillemets doubles."""
    return '"%s"' % texte.replace("\\", "\\\\").replace('"', '\\"')


def _esc(texte):
    return html.escape(texte, quote=True)


def entete(titre_page, includes, description=None):
    # « pagetitle » et non « title » : Quarto ne produit alors aucun bloc-titre
    # (donc aucun second <h1>), mais écrit le même <title> et les mêmes balises
    # de partage ; l'unique <h1> de la page est celui du gabarit.
    lignes = ["---", "pagetitle: " + _yaml(titre_page)]
    if description:
        lignes.append("description: " + _yaml(description))
    lignes += ["sidebar: false", "toc: false",
               "page-layout: full", "include-in-header:"]
    lignes += ["  - " + i for i in includes]
    lignes.append("---")
    return "\n".join(lignes) + "\n"


def nav_gauche(titre_cours, chapitres, actif, depuis_chapitre):
    """Sommaire du cours. `actif` : slug du chapitre courant, ou None pour
    la page d'accueil. `chapitres` : liste ordonnée de (slug, titre)."""
    if depuis_chapitre:
        accueil = '<li><a class="jm-accueil" href="../index.qmd">Présentation du cours</a></li>'
        prefixe = ""
    else:
        accueil = '<li><a class="jm-accueil jm-actif" href="index.qmd">Présentation du cours</a></li>'
        prefixe = "chapitres/"
    L = ['<details class="jm-sommaire" open>',
         '<summary class="jm-lecteur-titre-cours">%s</summary>' % titre_cours,
         "<ul>", accueil]
    for slug, titre in chapitres:
        cls = "jm-actif" if slug == actif else ""
        L.append('<li><a class="%s" href="%s%s.qmd">%s</a></li>'
                 % (cls, prefixe, slug, _esc(titre)))
    L += ["</ul>", "</details>", SCRIPT_SOMMAIRE]
    return "\n".join(L)


def nav_bas(chapitres, i):
    """Liens précédent / suivant sous le contenu du chapitre i."""
    L = ['<div class="jm-lecteur-nav">']
    if i == 0:
        L.append('<a href="../index.qmd">&larr; Présentation du cours</a>')
    else:
        slug, titre = chapitres[i - 1]
        L.append('<a href="%s.qmd">&larr; Chapitre précédent'
                 '<span class="jm-nav-label">%s</span></a>' % (slug, _esc(titre)))
    if i < len(chapitres) - 1:
        slug, titre = chapitres[i + 1]
        L.append('<a class="jm-nav-suivant" href="%s.qmd">Chapitre suivant &rarr;'
                 '<span class="jm-nav-label">%s</span></a>' % (slug, _esc(titre)))
    L.append("</div>")
    return "\n".join(L)


def entete_chapitre(titre_cours, titre, etiquette):
    """Bloc-titre visible d'un chapitre : le seul <h1> de la page."""
    attr = ' data-etiquette="%s"' % _esc(etiquette) if etiquette else ""
    suite = "&nbsp;· %s" % _esc(etiquette) if etiquette else ""
    return "\n".join([
        '<header class="jm-entete-chapitre"%s>' % attr,
        '<p class="jm-surtitre"><a href="../index.qmd">%s</a>%s</p>' % (titre_cours, suite),
        '<h1 class="jm-titre-chapitre">%s</h1>' % _esc(titre),
        "</header>",
    ])


def entete_accueil(titre_cours):
    """Bloc-titre visible de la page d'accueil d'un cours."""
    return "\n".join([
        DEBUT_ENTETE_ACCUEIL,
        '<h1 class="jm-titre-chapitre">%s</h1>' % titre_cours,
        "</header>",
    ])


def ressources_mobiles(slug, disponibles, video=None):
    """Puces de ressources, sous le titre ; affichées sur téléphone seulement."""
    L = ['<nav class="jm-ressources-mobile" aria-label="Ressources du chapitre">']
    for cle, libelle, gabarit in RESSOURCES:
        if cle in disponibles:
            L.append('<a class="jm-ressource" href="%s">%s</a>'
                     % (gabarit.format(slug=slug), libelle))
    if video:
        L.append('<a class="jm-ressource" href="%s">Vidéo</a>' % _esc(video))
    L.append("</nav>")
    return "\n".join(L)


def volet_droit(slug, disponibles, video=None):
    """`disponibles` : ensemble des clés de RESSOURCES présentes sur le
    disque. `video` : URL de la vidéo du chapitre, ou None."""
    L = ['<div class="jm-lecteur-droite">', "<h2>Ressources du chapitre</h2>", "<ul>"]
    for cle, libelle, gabarit in RESSOURCES:
        if cle in disponibles:
            L.append('<li><a class="jm-ressource" href="%s">%s</a></li>'
                     % (gabarit.format(slug=slug), libelle))
        else:
            L.append('<li><span class="jm-indisponible">— %s</span></li>' % libelle)
    if video:
        L.append('<li><a class="jm-ressource" href="%s">Vidéo</a></li>' % _esc(video))
    else:
        L.append('<li><span class="jm-indisponible">— Vidéo</span></li>')
    L.append('<li><span class="jm-reserve">QCM (bientôt)</span></li>')
    L.append("</ul>")
    L.append("</div>")
    return "\n".join(L)


def page_chapitre(titre_cours, chapitres, i, fragment, disponibles, video=None,
                  etiquette=None, description=None):
    """Texte complet de cours/<cours>/chapitres/<slug>.qmd.

    `fragment` : contenu HTML du chapitre, normalisé (voir normaliser.py),
    sans marques ; il commence par un saut de ligne et se termine par un.
    `etiquette` : « Chapitre 14 », « Annexe A », « Introduction »."""
    slug, titre = chapitres[i]
    return (
        entete("%s (%s)" % (titre, titre_cours), INCLUDES_CHAPITRE, description)
        + "\n```{=html}\n"
        + '<div class="jm-lecteur">\n'
        + '<div class="jm-lecteur-gauche">\n'
        + nav_gauche(titre_cours, chapitres, slug, True) + "\n"
        + "</div>\n"
        + '<div class="jm-lecteur-centre">\n'
        + entete_chapitre(titre_cours, titre, etiquette) + "\n"
        + ressources_mobiles(slug, disponibles, video) + "\n"
        + MARQUE_DEBUT + "\n"
        + fragment + "\n"
        + MARQUE_FIN + "\n"
        + nav_bas(chapitres, i) + "\n"
        + "</div>\n"
        + volet_droit(slug, disponibles, video) + "\n"
        + "</div>\n"
        + "```\n"
    )


def page_accueil(titre_cours, chapitres, presentation, description=None):
    """Texte complet de cours/<cours>/index.qmd.

    `presentation` : le Markdown de présentation du cours (paragraphes
    d'introduction et section « Syllabus »), sans le paragraphe final
    standard, qui est ajouté ici."""
    corps = presentation.strip("\n") + "\n\n" + PARAGRAPHE_ACCUEIL + "\n"
    return (
        entete(titre_cours, INCLUDES_ACCUEIL, description)
        + "\n:::: {.jm-lecteur .jm-lecteur-accueil}\n"
        + "::: {.jm-lecteur-gauche}\n"
        + "```{=html}\n"
        + nav_gauche(titre_cours, chapitres, None, False) + "\n"
        + "```\n"
        + ":::\n"
        + "::: {.jm-lecteur-centre}\n"
        + "```{=html}\n"
        + entete_accueil(titre_cours) + "\n"
        + "```\n\n"
        + corps
        + ":::\n"
        + "::::\n"
    )
