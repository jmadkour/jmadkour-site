#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produit, depuis l'atelier (dépôt stats-eco-cours), ce dont le lecteur à
3 volets a besoin pour un cours, en plus des diapositives :

  --fragments DOSSIER  le contenu central de chaque chapitre (HTML), un
                       fichier <slug>.html par chapitre, à passer ensuite
                       à generer_lecteur.py --fragments DOSSIER ;
  --polycopies         le polycopié PDF de chaque chapitre, déposé dans
                       cours/<cours>/ressources/<slug>-poly.pdf ;
  --exercices          les exercices et leur corrigé réunis en un seul
                       PDF, cours/<cours>/ressources/<slug>-exercices-corriges.pdf ;
  --outils             les applications interactives, copiées de
                       outils/<cours>-app-<unité>.html vers cours/<cours>/outils/<slug>.html.

Exemple, depuis la racine de jmadkour-site :

    python scripts/lecteur/rendre_atelier.py risque-credit \\
        --atelier ../stats-eco-cours --fragments /tmp/fragments-risque-credit \\
        --polycopies --exercices
    python scripts/lecteur/generer_lecteur.py risque-credit \\
        --fragments /tmp/fragments-risque-credit

Correspondance des fichiers. Les chapitres de l'atelier s'appellent
introduction.qmd, chapitre1.qmd, chapitre2.qmd... (puis annexeA.qmd... pour
l'économétrie avancée) ; le site les nomme par leur slug. La position dans
cours/chapitres.yml fait le lien : 1re entrée = introduction (s'il y en a
une), 2e = chapitre1, etc. Le script vérifie, avant de rien produire, que
le nombre de chapitres concorde ET que le titre de chaque chapitre
(champ subtitle: « Chapitre 3 : Titre ») est celui de chapitres.yml : le
décalage d'un cran entre numéros et slugs a déjà fait publier des
fichiers sous le mauvais nom. En cas de désaccord, rien n'est produit.

Prérequis côté atelier (déjà en place pour la Licence et le Master) :
  - _quarto.yml déclare, outre beamer, les formats `pdf` (polycopié,
    classe article, preamble-article.tex) et `html` (embed-resources,
    katex, toc: false) — voir cours-algebre-lineaire/_quarto.yml ;
  - pedago-blocks.lua est la version qui rend les encadrés en
    <details>/<summary> pour le format html ;
  - exercices/<cours>-exercices-<unité>.tex et -corrections-<unité>.tex,
    avec leur préambule partagé preambule-exercices-<cours>.tex.

Outils : quarto, xelatex (deux passes, pour la table des matières).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alleger_svg import alleger_fragment  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COURS = os.path.join(RACINE, "cours")


def lire(chemin):
    with open(chemin, encoding="utf-8", newline="") as f:
        return f.read()


def ecrire(chemin, texte):
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)


def _cle_unite(nom):
    if nom == "introduction":
        return (0, 0, "")
    m = re.fullmatch(r"chapitre(\d+)", nom)
    if m:
        return (1, int(m.group(1)), "")
    return (2, 0, nom)


def unites(atelier_cours):
    noms = [f[:-4] for f in os.listdir(atelier_cours)
            if re.fullmatch(r"(introduction|chapitre\d+|annexe[A-Z]?)\.qmd", f)]
    return sorted(noms, key=_cle_unite)


def _norm(t):
    t = t.replace("\u2019", "'").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", t).strip().lower()


def correspondance(cours, atelier_cours):
    """Liste ordonnée de (unité, slug, titre), vérifiée."""
    sommaire = yaml.safe_load(lire(os.path.join(COURS, "chapitres.yml")))
    chapitres = list(sommaire[cours].items())
    us = unites(atelier_cours)
    if len(us) != len(chapitres):
        raise SystemExit("%s : %d chapitres dans l'atelier, %d dans chapitres.yml — arrêt."
                         % (cours, len(us), len(chapitres)))
    erreurs = []
    for u, (slug, titre) in zip(us, chapitres):
        m = re.search(r'^subtitle:\s*["\']?(.*?)["\']?\s*$', lire(os.path.join(atelier_cours, u + ".qmd")), re.M)
        sous_titre = re.sub(r"^(Introduction|Chapitre\s+\d+|Annexe\s+[A-Z])\s*[:—-]\s*", "", m.group(1)) if m else ""
        if _norm(sous_titre) != _norm(titre):
            erreurs.append("  %-14s -> %-30s  atelier : « %s »  /  site : « %s »" % (u, slug, sous_titre, titre))
    if erreurs:
        print("Titres en désaccord entre l'atelier et chapitres.yml :")
        print("\n".join(erreurs))
        raise SystemExit("Arrêt : corriger la correspondance avant de produire quoi que ce soit.")
    return [(u, slug, titre) for u, (slug, titre) in zip(us, chapitres)]


def quarto(atelier_cours, unite, format_, sortie):
    cmd = ["quarto", "render", unite + ".qmd", "--to", format_, "--output", sortie]
    r = subprocess.run(cmd, cwd=atelier_cours, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit("échec : %s (dans %s)" % (" ".join(cmd), atelier_cours))
    return os.path.join(atelier_cours, sortie)


# ---------------------------------------------------------------------
#  Contenu central (HTML)
# ---------------------------------------------------------------------
def fragment(chemin_html):
    """Contenu de <main id="quarto-document-content">, tel quel."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(lire(chemin_html), "html.parser")
    main = soup.find("main", id="quarto-document-content")
    if main is None:
        raise SystemExit("%s : pas de <main id=quarto-document-content>" % chemin_html)
    # Les marqueurs de synchronisation de l'atelier (<!-- sortie: verif/... -->)
    # n'ont rien à faire dans une page publiée.
    return re.sub(r"<!-- sortie: [^>]*? -->", "", main.decode_contents())


def produire_fragments(atelier_cours, table, dossier):
    os.makedirs(dossier, exist_ok=True)
    for u, slug, _ in table:
        html = quarto(atelier_cours, u, "html", "%s-lecture.html" % u)
        ecrire(os.path.join(dossier, slug + ".html"), alleger_fragment(fragment(html)))
        os.remove(html)
        print("  fragment     %-14s -> %s.html" % (u, slug))


# ---------------------------------------------------------------------
#  Polycopiés (PDF, classe article)
# ---------------------------------------------------------------------
def produire_polycopies(atelier_cours, table, cours):
    dest = os.path.join(COURS, cours, "ressources")
    os.makedirs(dest, exist_ok=True)
    for u, slug, _ in table:
        pdf = quarto(atelier_cours, u, "pdf", "%s-poly.pdf" % u)
        shutil.move(pdf, os.path.join(dest, slug + "-poly.pdf"))
        print("  polycopié    %-14s -> ressources/%s-poly.pdf" % (u, slug))


# ---------------------------------------------------------------------
#  Exercices + corrigé réunis
# ---------------------------------------------------------------------
_RESERVEES = ("\\PolyTitreCourt", "\\PolyChapitre", "\\PolySousTitre", "\\PolyTypeDoc")


def _decouper(tex):
    """(préambule, corps) d'une feuille d'exercices ou d'un corrigé. Le
    corps est ce qui suit \\fabriquetitre, jusqu'à \\end{document}."""
    avant, apres = tex.split("\\begin{document}", 1)
    corps = apres.split("\\fabriquetitre", 1)[1] if "\\fabriquetitre" in apres else apres
    corps = corps.rsplit("\\end{document}", 1)[0]
    return avant, corps.strip("\n")


def _macro(preambule, nom):
    m = re.search(r"\\(?:re)?newcommand\{\\%s\}\{(.*)\}\s*$" % nom, preambule, re.M)
    return m.group(1) if m else None


def gabarit_fusion(titre_cours, exo, corr):
    pre_exo, corps_exo = _decouper(exo)
    pre_corr, corps_corr = _decouper(corr)
    chapitre = _macro(pre_exo, "PolyChapitre") or ""
    sous_titre = _macro(pre_exo, "PolySousTitre") or ""
    # Définitions propres au corrigé (rares), qui ne sont pas déjà dans
    # le préambule des exercices et ne touchent pas aux macros de titre.
    lignes_exo = set(l.strip() for l in pre_exo.splitlines())
    supplement = [l for l in pre_corr.splitlines()
                  if l.strip() and l.strip() not in lignes_exo
                  and not l.lstrip().startswith("\\input")
                  and not any(r in l for r in _RESERVEES)]
    intitule = "%s : %s" % (chapitre, sous_titre) if chapitre and sous_titre else (chapitre or sous_titre)
    return "\n".join([
        pre_exo.rstrip("\n"),
        *supplement,
        "\\renewcommand{\\PolyTypeDoc}{Exercices corrigés}",
        "\\begin{document}",
        "\\begin{titlepage}",
        "  \\begin{center}",
        "    \\vspace*{0.10\\textheight}",
        "    {\\sffamily\\huge\\bfseries\\color{cdef}%s\\par}" % titre_cours,
        "    \\vspace{0.8em}",
        "    {\\sffamily\\Large\\color{cgris}%s\\par}" % intitule,
        "    \\vspace{1.4em}",
        "    {\\sffamily\\large\\bfseries\\color{ceco}Exercices corrigés\\par}",
        "    \\vspace{2.2em}",
        "    {\\color{cdef!35}\\rule{0.55\\textwidth}{0.8pt}\\par}",
        "    \\vspace{1.2em}",
        "    {\\normalsize Jaouad Madkour\\par}",
        "    \\vspace{0.3em}",
        "    {\\small\\color{cgris}Faculté d'Économie et de Gestion de Tanger\\par}",
        "    \\vspace{0.15em}",
        "    {\\small\\color{cgris}%s\\par}" % titre_cours,
        "  \\end{center}",
        "\\end{titlepage}",
        "\\thispagestyle{empty}",
        "\\vspace*{0.06\\textheight}",
        "\\begin{center}",
        "  {\\sffamily\\large\\bfseries\\color{cdef}Table des matières\\par}",
        "  \\vspace{1.6em}",
        "  \\begin{minipage}{0.62\\textwidth}\\sffamily\\color{ceco}",
        "    \\hyperref[jm-partie-1]{Partie 1 — Énoncés}\\dotfill\\pageref{jm-partie-1}\\par",
        "    \\vspace{0.9em}",
        "    \\hyperref[jm-partie-2]{Partie 2 — Corrections}\\dotfill\\pageref{jm-partie-2}\\par",
        "  \\end{minipage}",
        "\\end{center}",
        "\\clearpage",
        "\\setcounter{page}{1}",
        "\\phantomsection\\label{jm-partie-1}",
        corps_exo,
        "\\clearpage",
        "\\setcounter{section}{0}",
        "\\phantomsection\\label{jm-partie-2}",
        corps_corr,
        "\\end{document}",
        "",
    ])


def produire_exercices(atelier_cours, table, cours, titre_cours):
    nom = os.path.basename(atelier_cours.rstrip("/\\"))
    prefixe = nom[len("cours-"):] if nom.startswith("cours-") else cours
    dossier_ex = os.path.join(atelier_cours, "exercices")
    dest = os.path.join(COURS, cours, "ressources")
    os.makedirs(dest, exist_ok=True)
    for u, slug, _ in table:
        exo = os.path.join(dossier_ex, "%s-exercices-%s.tex" % (prefixe, u))
        corr = os.path.join(dossier_ex, "%s-corrections-%s.tex" % (prefixe, u))
        if not (os.path.isfile(exo) and os.path.isfile(corr)):
            print("  exercices    %-14s   ABSENTS (%s)" % (u, os.path.basename(exo)))
            continue
        tex = gabarit_fusion(titre_cours, lire(exo), lire(corr))
        # Compilé dans le dossier exercices/, pour que \input{preambule...}
        # et les chemins relatifs des figures se résolvent comme d'habitude.
        base = "_fusion-%s" % u
        ecrire(os.path.join(dossier_ex, base + ".tex"), tex)
        try:
            for _ in range(2):
                r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", base + ".tex"],
                                   cwd=dossier_ex, capture_output=True, text=True)
                if r.returncode != 0:
                    print(r.stdout[-3000:])
                    raise SystemExit("échec xelatex : %s" % os.path.join(dossier_ex, base + ".tex"))
            shutil.move(os.path.join(dossier_ex, base + ".pdf"),
                        os.path.join(dest, slug + "-exercices-corriges.pdf"))
        finally:
            for ext in (".tex", ".aux", ".log", ".toc", ".out", ".pdf"):
                p = os.path.join(dossier_ex, base + ext)
                if os.path.exists(p):
                    os.remove(p)
        print("  exercices    %-14s -> ressources/%s-exercices-corriges.pdf" % (u, slug))


def copier_outils(atelier_cours, table, cours):
    nom = os.path.basename(atelier_cours.rstrip("/\\"))
    prefixe = nom[len("cours-"):] if nom.startswith("cours-") else cours
    dest = os.path.join(COURS, cours, "outils")
    os.makedirs(dest, exist_ok=True)
    for u, slug, _ in table:
        src = os.path.join(atelier_cours, "outils", "%s-app-%s.html" % (prefixe, u))
        if not os.path.isfile(src):
            print("  outil        %-14s   ABSENT (%s)" % (u, os.path.basename(src)))
            continue
        shutil.copyfile(src, os.path.join(dest, slug + ".html"))
        print("  outil        %-14s -> outils/%s.html" % (u, slug))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("cours", help="dossier du cours sous cours/ (site)")
    p.add_argument("--atelier", required=True, help="racine du dépôt stats-eco-cours")
    p.add_argument("--fragments", help="dossier où écrire les fragments <slug>.html")
    p.add_argument("--polycopies", action="store_true")
    p.add_argument("--exercices", action="store_true")
    p.add_argument("--outils", action="store_true")
    args = p.parse_args()

    atelier_cours = os.path.join(args.atelier, "cours-" + args.cours)
    if not os.path.isdir(atelier_cours):
        raise SystemExit("introuvable : %s" % atelier_cours)
    table = correspondance(args.cours, atelier_cours)
    print("%s : %d chapitres, correspondance atelier/site vérifiée." % (args.cours, len(table)))

    index = lire(os.path.join(COURS, args.cours, "index.qmd"))
    # « pagetitle » depuis le 28/10/2026 (plus de bloc-titre Quarto), « title » avant.
    titre = re.search(r'^(?:pagetitle|title):\s*"(.*)"\s*$', index, re.M).group(1)

    if args.fragments:
        produire_fragments(atelier_cours, table, args.fragments)
    if args.polycopies:
        produire_polycopies(atelier_cours, table, args.cours)
    if args.exercices:
        produire_exercices(atelier_cours, table, args.cours, titre)
    if args.outils:
        copier_outils(atelier_cours, table, args.cours)
    if not (args.fragments or args.polycopies or args.exercices or args.outils):
        print("Rien demandé : --fragments, --polycopies, --exercices et/ou --outils.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
