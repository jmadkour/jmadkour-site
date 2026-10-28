#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retire du plan du site (_site/sitemap.xml) les pages qu'il est inutile
d'indexer : les pages de redirection (<meta http-equiv="refresh">) et celles
qui se déclarent <meta name="robots" content="noindex">.

Quarto n'offre pas, dans la version utilisée, d'option pour exclure une page
du plan du site ; ce script s'en charge après le rendu, avant la publication
(voir .github/workflows/publish.yml) :

    quarto render
    python3 scripts/nettoyer-sitemap.py            # _site par défaut
    python3 scripts/nettoyer-sitemap.py chemin_du_site

Il ne retire que ces pages : aucune liste à tenir à jour. Pour sortir une
page du plan du site, il suffit qu'elle redirige ou qu'elle porte la balise
noindex (include-in-header dans son en-tête).
"""

import pathlib
import re
import sys
from urllib.parse import urlparse, unquote

REDIRECTION = re.compile(r'<meta\s+http-equiv=["\']refresh["\']', re.I)
NOINDEX = re.compile(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex', re.I)
ENTREE = re.compile(r"[ \t]*<url>\s*<loc>(.*?)</loc>.*?</url>[ \t]*\n?", re.S)


def a_exclure(site, loc):
    chemin = unquote(urlparse(loc.strip()).path).lstrip("/")
    if not chemin or chemin.endswith("/"):
        chemin += "index.html"
    fichier = site / chemin
    if not fichier.is_file() or fichier.suffix != ".html":
        return False
    texte = fichier.read_text(encoding="utf-8", errors="replace")
    return bool(REDIRECTION.search(texte) or NOINDEX.search(texte))


def main():
    site = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    plan = site / "sitemap.xml"
    if not plan.is_file():
        print("nettoyer-sitemap : %s introuvable, rien à faire." % plan)
        return 0
    xml = plan.read_text(encoding="utf-8")
    retirees = []

    def decider(m):
        if a_exclure(site, m.group(1)):
            retirees.append(m.group(1).strip())
            return ""
        return m.group(0)

    nouveau = ENTREE.sub(decider, xml)
    if retirees:
        plan.write_text(nouveau, encoding="utf-8", newline="\n")
    print("nettoyer-sitemap : %d page(s) retirée(s) du plan du site" % len(retirees))
    for loc in retirees:
        print("  - " + loc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
