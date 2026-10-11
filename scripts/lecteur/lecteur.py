# -*- coding: utf-8 -*-
"""
Gabarits du lecteur de chapitres à 3 volets (pages de cours du site).

Ce module ne fait qu'une chose : écrire, à partir de données déjà prêtes,
le texte exact des pages Quarto du lecteur. Il ne lit ni n'écrit aucun
fichier lui-même ; generer_lecteur.py s'en charge.

    page_chapitre(...)  -> cours/<cours>/chapitres/<slug>.qmd
    page_accueil(...)   -> cours/<cours>/index.qmd

Reconstruit le 11/10/2026 à partir des 399 pages produites en septembre
par l'ancien script (perdu avec l'espace de travail de Claude) : il les
reproduit octet pour octet (voir verifier_reproduction.py).

Choix figés, à ne pas changer sans raison :
- le volet gauche ne numérote pas les chapitres (demande du 25/09/2026) ;
- les titres de chapitre sont échappés pour le HTML (html.escape), le
  titre du cours ne l'est pas (il ne contient jamais < ni &) ;
- une ressource absente reste visible, grisée (« — Diapositives »), pour
  que l'étudiant sache qu'elle viendra.
"""

import html

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


def _yaml(texte):
    """Chaîne YAML entre guillemets doubles."""
    return '"%s"' % texte.replace("\\", "\\\\").replace('"', '\\"')


def _esc(texte):
    return html.escape(texte, quote=True)


def entete(titre, sous_titre, includes):
    lignes = ["---", "title: " + _yaml(titre)]
    if sous_titre is not None:
        lignes.append("subtitle: " + _yaml(sous_titre))
    lignes += ["sidebar: false", "toc: false", "page-layout: full",
               "include-in-header:"]
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
    L = ['<div class="jm-lecteur-titre-cours">%s</div>' % titre_cours,
         "<ul>", accueil]
    for slug, titre in chapitres:
        cls = "jm-actif" if slug == actif else ""
        L.append('<li><a class="%s" href="%s%s.qmd">%s</a></li>'
                 % (cls, prefixe, slug, _esc(titre)))
    L.append("</ul>")
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


def volet_droit(slug, disponibles, video=None):
    """`disponibles` : ensemble des clés de RESSOURCES présentes sur le
    disque. `video` : URL de la vidéo du chapitre, ou None."""
    L = ['<div class="jm-lecteur-droite">', "<h3>Ressources du chapitre</h3>", "<ul>"]
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


def page_chapitre(titre_cours, chapitres, i, fragment, disponibles, video=None):
    """Texte complet de cours/<cours>/chapitres/<slug>.qmd.

    `fragment` : contenu HTML du chapitre (voir extraire_fragments.py),
    tel quel ; il commence par un saut de ligne et se termine par un."""
    slug, titre = chapitres[i]
    return (
        entete(titre_cours, titre, INCLUDES_CHAPITRE)
        + "\n```{=html}\n"
        + '<div class="jm-lecteur">\n'
        + '<div class="jm-lecteur-gauche">\n'
        + nav_gauche(titre_cours, chapitres, slug, True) + "\n"
        + "</div>\n"
        + '<div class="jm-lecteur-centre">\n'
        + fragment + "\n"
        + nav_bas(chapitres, i) + "\n"
        + "</div>\n"
        + volet_droit(slug, disponibles, video) + "\n"
        + "</div>\n"
        + "```\n"
    )


def page_accueil(titre_cours, chapitres, presentation):
    """Texte complet de cours/<cours>/index.qmd.

    `presentation` : le Markdown de présentation du cours (paragraphes
    d'introduction et section « Syllabus »), sans le paragraphe final
    standard, qui est ajouté ici."""
    corps = presentation.strip("\n") + "\n\n" + PARAGRAPHE_ACCUEIL + "\n"
    return (
        entete(titre_cours, None, INCLUDES_ACCUEIL)
        + "\n:::: {.jm-lecteur .jm-lecteur-accueil}\n"
        + "::: {.jm-lecteur-gauche}\n"
        + "```{=html}\n"
        + nav_gauche(titre_cours, chapitres, None, False) + "\n"
        + "```\n"
        + ":::\n"
        + "::: {.jm-lecteur-centre}\n"
        + corps
        + ":::\n"
        + "::::\n"
    )
