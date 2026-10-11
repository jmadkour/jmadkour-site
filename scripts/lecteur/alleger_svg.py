#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Allège les figures SVG intégrées dans le contenu des pages de chapitre.

Les figures viennent de TikZ/pgfplots via dvisvgm, puis sont intégrées en
ligne par Quarto (embed-resources). Deux redondances les font grossir,
surtout pour les nuages de points (un diagramme de bifurcation dépassait
2,9 Mo à lui seul) :

1. Les coordonnées sont écrites avec 6 décimales (au millionième de
   point typographique). On arrondit à 2 décimales — un centième de point,
   soit 3,5 µm à l'impression, invisible à l'écran — et à 3 décimales dans
   les glyphes des caractères (<symbol>), plus petits. Les matrices de
   transformation, elles, sont laissées intactes.
2. Chaque point d'un nuage est un petit cercle, que dvisvgm écrit comme
   quatre arcs de Bézier (130 caractères). Il est réécrit en <circle>
   (une quarantaine de caractères), qui trace le même disque.
3. Chaque élément répète le même attribut style (et transform) : 4 462
   fois la même chaîne de 270 caractères dans la figure ci-dessus. Les
   éléments consécutifs qui partagent exactement le même style et la même
   transformation sont regroupés dans un <g> qui les porte une seule fois.
   C'est sans perte : style et transform s'héritent du groupe.

Le dessin reste vectoriel, net à tous les zooms, et se comporte comme
avant en mode sombre. Seules les figures d'au moins SEUIL octets sont
traitées ; les autres sont laissées telles quelles.

Utilisation comme module : alleger_fragment(html) -> html
Utilisation en ligne de commande (sur des pages déjà produites) :

    python scripts/lecteur/alleger_svg.py cours/*/chapitres/*.qmd
    python scripts/lecteur/alleger_svg.py --verifier cours/*/chapitres/*.qmd
"""

import re
import sys

SEUIL = 100_000          # octets ; en dessous, la figure n'est pas touchée
DECIMALES = 2            # tracés, positions, transformations
DECIMALES_GLYPHES = 3    # contours des caractères, dans <symbol>

_SVG = re.compile(r"<svg\b.*?</svg>", re.S)
_NOMBRE = re.compile(r"-?\d+\.\d+")
# Les matrices de transformation ne sont jamais arrondies : leurs facteurs
# d'échelle peuvent être petits (0,0234...), et une erreur relative s'y
# propage à toute la figure.
_ATTR_NUM = re.compile(r'\b(d|x|y|cx|cy|r)="([^"]*)"')
_SYMBOLE = re.compile(r"<symbol\b.*?</symbol>", re.S)


def _arrondir(n, decimales):
    s = ("%." + str(decimales) + "f") % float(n)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s


def _arrondir_attrs(texte, decimales):
    def attr(m):
        valeur = _NOMBRE.sub(lambda n: _arrondir(n.group(0), decimales), m.group(2))
        return '%s="%s"' % (m.group(1), valeur)
    return _ATTR_NUM.sub(attr, texte)


_ELEMENT = re.compile(r'^<(path|use|circle)((?:\s+[\w:-]+="[^"]*")*)\s*>(</\1>)?$')
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')


def _analyser(ligne):
    """(balise, attributs ordonnés, fermeture) d'une ligne <path>/<use>,
    ou None si la ligne n'en est pas une."""
    m = _ELEMENT.match(ligne)
    if not m:
        return None
    return m.group(1), _ATTR.findall(m.group(2)), m.group(3) or ""


def _cle(elt):
    attrs = dict(elt[1])
    if "style" not in attrs:
        return None
    return attrs.get("style"), attrs.get("transform")


def _regrouper(svg):
    """Regroupe les lignes consécutives <path>/<use> de même style et même
    transformation. Le SVG produit par Quarto a un élément par ligne."""
    lignes = svg.split("\n")
    sortie = []
    i = 0
    while i < len(lignes):
        elt = _analyser(lignes[i])
        cle = _cle(elt) if elt else None
        if cle is None:
            sortie.append(lignes[i])
            i += 1
            continue
        j = i + 1
        while j < len(lignes):
            e2 = _analyser(lignes[j])
            if not e2 or _cle(e2) != cle:
                break
            j += 1
        if j - i < 2:
            sortie.append(lignes[i])
            i += 1
            continue
        style, transform = cle
        sortie.append('<g style="%s"%s>' % (style, ' transform="%s"' % transform if transform else ""))
        for k in range(i, j):
            tag, attrs, fermeture = _analyser(lignes[k])
            reste = "".join(' %s="%s"' % (a, v) for a, v in attrs if a not in ("style", "transform"))
            sortie.append("<%s%s>%s" % (tag, reste, fermeture))
        sortie.append("</g>")
        i = j
    return "\n".join(sortie)


_N = r"(-?\d+(?:\.\d+)?)"
_CERCLE = re.compile(
    r'<path d="M ' + _N + " " + _N
    + "".join(r" C " + " ".join([_N] * 6) for _ in range(4))
    + r' Z M ' + _N + " " + _N + r' ?"'
)


def _cercles(svg):
    """Réécrit en <circle> les tracés qui sont des cercles à 4 arcs."""
    def remplace(m):
        v = [float(x) for x in m.groups()]
        x0, y0 = v[0], v[1]                    # point de départ
        x1, y1 = v[6], v[7]                    # fin du 1er arc
        x2 = v[12]                             # fin du 2e arc (abscisse)
        y3 = v[19]                             # fin du 3e arc (ordonnée)
        x4, y4 = v[24], v[25]                  # fin du 4e arc (= départ)
        cx, cy = (x0 + x2) / 2, (y1 + y3) / 2
        rayons = [abs(x0 - cx), abs(x2 - cx), abs(y1 - cy), abs(y3 - cy)]
        r = sum(rayons) / 4
        if r <= 0 or max(rayons) - min(rayons) > 0.01 * r:
            return m.group(0)                  # pas un cercle : inchangé
        if abs(x4 - x0) > 1e-6 or abs(y4 - y0) > 1e-6 or abs(y0 - cy) > 0.01 * r or abs(x1 - cx) > 0.01 * r:
            return m.group(0)
        return '<circle cx="%s" cy="%s" r="%s"' % (
            _arrondir(cx, DECIMALES), _arrondir(cy, DECIMALES), _arrondir(r, DECIMALES_GLYPHES))
    svg = _CERCLE.sub(remplace, svg)
    # <path ...></path> devenu <circle ...></path> : refermer correctement.
    return re.sub(r"(<circle\b[^>]*>)</path>", r"\1</circle>", svg)


def alleger_svg(svg):
    """Version allégée d'un élément <svg>…</svg> (chaîne)."""
    svg = _cercles(svg)
    # Glyphes d'abord, avec plus de décimales ; puis le reste.
    morceaux = []
    pos = 0
    for m in _SYMBOLE.finditer(svg):
        morceaux.append(_arrondir_attrs(svg[pos:m.start()], DECIMALES))
        morceaux.append(_arrondir_attrs(m.group(0), DECIMALES_GLYPHES))
        pos = m.end()
    morceaux.append(_arrondir_attrs(svg[pos:], DECIMALES))
    return _regrouper("".join(morceaux))


def alleger_fragment(html, seuil=SEUIL):
    """Allège chaque <svg> d'au moins `seuil` octets dans un texte HTML."""
    def remplace(m):
        s = m.group(0)
        return alleger_svg(s) if len(s.encode("utf-8")) >= seuil else s
    return _SVG.sub(remplace, html)


def main(argv):
    verifier = "--verifier" in argv
    fichiers = [a for a in argv if not a.startswith("--")]
    avant_total = apres_total = touches = 0
    for chemin in fichiers:
        with open(chemin, encoding="utf-8", newline="") as f:
            texte = f.read()
        nouveau = alleger_fragment(texte)
        avant, apres = len(texte.encode("utf-8")), len(nouveau.encode("utf-8"))
        avant_total += avant
        apres_total += apres
        if nouveau != texte:
            touches += 1
            print("  %-70s %8.0f Ko -> %7.0f Ko" % (chemin, avant / 1024, apres / 1024))
            if not verifier:
                with open(chemin, "w", encoding="utf-8", newline="") as f:
                    f.write(nouveau)
    print()
    print("%d fichier(s) %s ; %.1f Mo -> %.1f Mo au total."
          % (touches, "à alléger" if verifier else "allégé(s)",
             avant_total / 1e6, apres_total / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
