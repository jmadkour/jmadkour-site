#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur du CV de Jaouad Madkour.

Lit  : cv/cv.yml       (la source unique des données)
       cv/modele.tex   (la mise en page LaTeX, avec des repères @@...@@)

Écrit: cv/CV_Jaouad_Madkour.tex   à compiler par xelatex pour obtenir le PDF
       profile.qmd     la page « Jaouad Madkour » du site

Usage :  python cv/build.py
"""

import io
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("Le module PyYAML est requis :  pip install pyyaml")

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)


# =====================================================================
#  Conversion LaTeX -> Markdown, pour la page web
# =====================================================================

def tex_vers_md(t):
    """Traduit le balisage LaTeX des données en Markdown."""
    # liens : \href{url}{texte} -> [texte](url)
    t = re.sub(r"\\href\{([^}]*)\}\{([^}]*)\}", r"[\2](\1)", t)
    # gras coloré : \textbf{\color{navy}X} -> **X**
    t = re.sub(r"\\textbf\{\\color\{navy\}(.*?)\}", r"**\1**", t)
    t = re.sub(r"\\textbf\{(.*?)\}", r"**\1**", t)
    t = re.sub(r"\\textit\{(.*?)\}", r"*\1*", t)
    # exposants et symboles
    t = t.replace("n\\textsuperscript{o}", "n&deg;")
    t = re.sub(r"\\textsuperscript\{(.*?)\}", r"^\1^", t)
    t = t.replace("$\\Delta$", "Δ")
    # tirets, dans cet ordre : le cadratin avant le demi-cadratin
    t = t.replace("---", "—").replace("--", "–")
    # espaces LaTeX
    t = t.replace("~", "\u00a0").replace("\\ ", " ").replace("\\,", "\u202f")
    # caractères échappés
    for a, b in (("\\&", "&"), ("\\%", "%"), ("\\_", "_"),
                 ("\\#", "#"), ("\\$", "$")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def couper_titre(texte_tex):
    """Sépare la partie en gras du reste, pour la mise en forme web."""
    m = re.match(r"^\\textbf\{\\color\{navy\}(.*?)\}\s*(.*)$", texte_tex, re.S)
    if m:
        return tex_vers_md(m.group(1)), tex_vers_md(m.group(2))
    return None, tex_vers_md(texte_tex)


# =====================================================================
#  Génération du LaTeX
# =====================================================================

def corps_latex(d):
    L = []
    A = L.append

    A("\\cvsection{Profil}")
    A("{\\fontsize{9.9}{14.5}\\selectfont\\justifying")
    A("\\par\n\\vspace{5pt}\n".join(d["profil"]))
    A("}")

    for sec in d["sections"]:
        A("")
        A("% " + "=" * 69)
        A("\\cvsection{%s}" % sec["titre"])
        for bloc in sec["blocs"]:
            if bloc.get("sous_titre"):
                A("")
                A("\\cvsubsection{%s}" % bloc["sous_titre"])
            entrees = bloc["entrees"]
            if bloc.get("type") == "publications":
                for e in entrees:
                    A("")
                    A("\\pub{%s}" % e["titre"])
                    A("{%s}" % e["source"])
                    A("{%s}" % e.get("lien", ""))
            else:
                A("\\begin{cvlist}")
                for k, e in enumerate(entrees):
                    cmd = "\\cvrowlast" if k == len(entrees) - 1 else "\\cvrow"
                    A("%s{%s}{%s}" % (cmd, e["texte"], e.get("date", "")))
                A("\\end{cvlist}")

    A("")
    A("% " + "=" * 69)
    A("\\cvsection{Compétences}")
    # Trois colonnes egales, calculees sur \textwidth (moins l'espacement
    # inter-colonnes par defaut) plutot que des largeurs fixes en cm : le
    # tableau remplit toute la largeur quels que soient les reglages de page.
    A("\\begin{tabular}{@{}*{3}{L{\\dimexpr(\\textwidth-4\\tabcolsep)/3\\relax}}@{}}")
    A(" &\n".join(
        "{\\track\\fontsize{8.3}{10}\\selectfont\\color{gold}"
        "\\MakeUppercase{%s}}" % c["titre"] for c in d["competences"]) + " \\\\[3pt]")
    A(" &\n".join(
        "{\\fontsize{9.7}{13}\\selectfont %s}" % c["valeur"]
        for c in d["competences"]) + " \\\\")
    A("\\end{tabular}")
    return "\n".join(L)


def ecrire_tex(d):
    modele = io.open(os.path.join(ICI, "modele.tex"), encoding="utf-8").read()
    ident = d["identite"]

    contacts = ("\\ \\ {\\color{gold}$\\cdot$}\\ \\\n   ".join(
        "{\\color{cream}\\href{%s}{%s}}" % (c["url"], c["texte"])
        for c in ident["contacts"]))

    out = (modele
           .replace("@@NOM@@", ident["nom"])
           .replace("@@TITRE@@", ident["titre"])
           .replace("@@AFFILIATION@@", "\\\\\n   ".join(ident["affiliation"]))
           .replace("@@CONTACTS@@", contacts)
           .replace("@@CORPS@@", corps_latex(d))
           .replace("@@PIED@@", d["pied_de_page"]))

    chemin = os.path.join(ICI, "CV_Jaouad_Madkour.tex")
    io.open(chemin, "w", encoding="utf-8", newline="\n").write(out)
    return chemin


# =====================================================================
#  Génération de la page du site
# =====================================================================

CSS = """```{=html}
<style>
  .cv-sec { margin: 1.2rem 0 2rem; }
  .cv-row {
    display: flex; justify-content: space-between; align-items: baseline; gap: 1rem;
    border-left: 3px solid var(--bs-primary, #2f7ea8);
    padding: 0.5rem 0 0.5rem 1rem; margin-bottom: 0.4rem;
    border-bottom: 1px solid rgba(128,128,128,0.22);
  }
  .cv-row:hover { border-left-color: var(--bs-link-hover-color, #4aa3cf); }
  .cv-what { line-height: 1.4; }
  .cv-when { font-size: 0.82rem; opacity: 0.7; white-space: nowrap; font-variant-numeric: tabular-nums; }
  .cv-pub { border-left: 3px solid var(--bs-primary, #2f7ea8);
            padding: 0.55rem 0 0.9rem 1rem; margin-bottom: 0.9rem;
            border-bottom: 1px solid rgba(128,128,128,0.22); }
  .cv-pub-t { font-weight: 600; line-height: 1.35; margin-bottom: 0.3rem; }
  .cv-pub-s { font-size: 0.9rem; opacity: 0.85; }
  .cv-pub-l { font-size: 0.84rem; margin-top: 0.25rem; }
  .cv-cta { display: inline-block; font-size: 0.88rem; font-weight: 600; text-decoration: none;
            padding: 0.35rem 0.9rem; border-radius: 999px;
            background: var(--bs-primary, #2f7ea8); color: #fff; }
  .cv-cta:hover { color: #fff; opacity: 0.88; }
  @media (max-width: 575px) {
    .cv-row { flex-direction: column; gap: 0.15rem; }
    .cv-when { align-self: flex-start; }
  }
</style>
```"""


def echapper_html(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md_vers_html(t):
    """Gras, italique et liens Markdown -> HTML, après échappement."""
    t = echapper_html(t)
    t = t.replace("&amp;deg;", "&deg;")
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def ecrire_page(d):
    ident = d["identite"]
    L = []
    A = L.append

    A("---")
    A('title: "%s"' % ident["nom"])
    A('subtitle: "%s — statistique, économétrie et gestion des risques financiers"'
      % ident["titre"])
    A("sidebar: false")
    A("---")
    A("")
    A("<!-- Page produite par cv/build.py à partir de cv/cv.yml — ne pas modifier à la main. -->")
    A("")
    for p in d["profil"]:
        A(tex_vers_md(p))
        A("")
    web = d.get("web", {})
    if web.get("introduction"):
        A(web["introduction"])
        A("")
    A(CSS)
    A("")

    for sec in d["sections"]:
        A("## %s" % sec["titre"])
        A("")
        for bloc in sec["blocs"]:
            if bloc.get("sous_titre"):
                A("### %s" % tex_vers_md(bloc["sous_titre"]))
                A("")
            if bloc.get("type") == "publications":
                A("```{=html}")
                A('<div class="cv-sec">')
                for e in bloc["entrees"]:
                    A('  <div class="cv-pub">')
                    A('    <div class="cv-pub-t">%s</div>' % md_vers_html(tex_vers_md(e["titre"])))
                    A('    <div class="cv-pub-s">%s</div>' % md_vers_html(tex_vers_md(e["source"])))
                    if e.get("lien"):
                        A('    <div class="cv-pub-l">%s</div>' % md_vers_html(tex_vers_md(e["lien"])))
                    A("  </div>")
                A("</div>")
                A("```")
            else:
                A("```{=html}")
                A('<div class="cv-sec">')
                for e in bloc["entrees"]:
                    titre, reste = couper_titre(e["texte"])
                    corps = ("<strong>%s</strong> %s" % (md_vers_html(titre), md_vers_html(reste))
                             if titre else md_vers_html(reste))
                    A('  <div class="cv-row">')
                    A('    <div class="cv-what">%s</div>' % corps.strip())
                    A('    <div class="cv-when">%s</div>' % echapper_html(tex_vers_md(e.get("date", ""))))
                    A("  </div>")
                A("</div>")
                A("```")
            A("")
            for enc in web.get("encarts", []):
                if enc.get("apres_sous_titre") == bloc.get("sous_titre"):
                    A(enc["texte"])
                    A("")

    A("## Compétences")
    A("")
    for c in d["competences"]:
        A("**%s** — %s" % (tex_vers_md(c["titre"]), tex_vers_md(c["valeur"])))
        A("")

    A("## Me contacter")
    A("")
    for c in ident["contacts"]:
        A("- [%s](%s)" % (c["texte"], c["url"]))
    A("")
    A("```{=html}")
    A('<p style="margin-top:1.2rem"><a class="cv-cta" href="cv/CV_Jaouad_Madkour.pdf" '
      'target="_blank" rel="noopener">Télécharger le CV (PDF)</a></p>')
    A("```")

    chemin = os.path.join(RACINE, "profile.qmd")
    io.open(chemin, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    return chemin


# =====================================================================

def main():
    d = yaml.safe_load(io.open(os.path.join(ICI, "cv.yml"), encoding="utf-8"))
    t = ecrire_tex(d)
    p = ecrire_page(d)
    n = sum(len(b["entrees"]) for s in d["sections"] for b in s["blocs"])
    print("cv.yml lu : %d sections, %d entrées" % (len(d["sections"]), n))
    print("  écrit :", os.path.relpath(t, RACINE))
    print("  écrit :", os.path.relpath(p, RACINE))
    print("\nPour produire le PDF :  cd cv && xelatex CV_Jaouad_Madkour.tex")


if __name__ == "__main__":
    main()
