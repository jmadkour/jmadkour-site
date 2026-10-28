# -*- coding: utf-8 -*-
"""
Mise en forme des fragments de chapitre (contenu central du lecteur).

Fonctions pures : aucune entrée-sortie. generer_lecteur.py les appelle.

Un fragment « brut » est ce que produit le rendu Quarto de l'atelier : il
commence par un bloc-titre (le titre du cours en <h1>, « Chapitre N : … »
en sous-titre, auteur, date), puis les sections du chapitre, dont les titres
sont des <h1> (sections) et des <h2> (sous-sections).

Un fragment « normalisé » (état des pages écrites depuis le 28/10/2026) :

- le bloc-titre a disparu : le titre du chapitre est un <h1> unique, écrit
  par lecteur.py au-dessus du fragment ;
- les titres sont abaissés d'un niveau (<h1> -> <h2>, <h2> -> <h3>), avec la
  classe Bootstrap de leur niveau d'origine (« h1 », « h2 ») pour que
  l'apparence ne change pas ;
- le fragment est encadré par les commentaires MARQUE_DEBUT / MARQUE_FIN,
  qui permettent de le retrouver et de savoir qu'il est déjà normalisé.
"""

import html
import re

MARQUE_DEBUT = "<!-- jm:contenu -->"
MARQUE_FIN = "<!-- /jm:contenu -->"

_ENTETE = re.compile(
    r'<header class="quarto-title-block default" id="title-block-header">.*?</header>\n?',
    re.S)
_SOUS_TITRE = re.compile(r'<p class="subtitle lead">(.*?)</p>', re.S)
_ETIQUETTE = re.compile(r'^\s*(Chapitre\s+\d+|Annexe\s+[A-Z]|Introduction)\s*:')
_BALISE_TITRE = re.compile(r"<(/?)h([1-6])((?:\s[^>]*)?)>")
_SVG = re.compile(r"<svg\b.*?</svg>", re.S)
_PARAGRAPHE = re.compile(r"<p>(.*?)</p>", re.S)
_TABLE = re.compile(r"<table\b.*?</table>", re.S)


def texte_brut(fragment_html):
    """Texte d'un extrait HTML : balises ôtées, entités décodées, espaces réduits."""
    t = re.sub(r"<[^>]+>", "", fragment_html)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def etiquette_depuis_entete(fragment_brut):
    """« Chapitre 14 », « Annexe A », « Introduction » ou None, d'après le
    sous-titre du bloc-titre d'un fragment brut."""
    m = _ENTETE.search(fragment_brut)
    if not m:
        return None
    s = _SOUS_TITRE.search(m.group(0))
    if not s:
        return None
    e = _ETIQUETTE.match(texte_brut(s.group(1)))
    return re.sub(r"\s+", " ", e.group(1)) if e else None


def _abaisser(m):
    ferme, niveau, attrs = m.group(1), int(m.group(2)), m.group(3) or ""
    nouveau = min(niveau + 1, 6)
    if ferme:
        return "</h%d>" % nouveau
    # classe du niveau d'origine, pour conserver l'apparence
    classe = "h%d" % niveau
    if re.search(r'\sclass="', attrs):
        attrs = re.sub(r'\sclass="', ' class="%s ' % classe, attrs, count=1)
    else:
        attrs = ' class="%s"' % classe + attrs
    return "<h%d%s>" % (nouveau, attrs)


def normaliser_fragment(fragment_brut):
    """Fragment brut -> fragment normalisé (sans marques). Idempotence
    assurée par l'appelant : ne pas l'appliquer à un fragment déjà normalisé."""
    f = _ENTETE.sub("", fragment_brut, count=1)
    return _BALISE_TITRE.sub(_abaisser, f)


# ---------------------------------------------------------------------------
# Descriptions (balise <meta name="description">)
# ---------------------------------------------------------------------------

_FIN_PHRASE = re.compile(r"(?<=[.!?…»])\s+(?=[A-ZÀ-ÖØ-Þ«“\"(])")


def tronquer(texte, limite, souple=0):
    """Texte réduit à `limite` caractères au plus, en gardant des phrases
    entières si possible (sinon coupé à un mot, avec « … »). Si `souple` est
    non nul, on accepte jusqu'à `souple` caractères de plus tant que le texte
    gardé fait moins de 100 caractères (évite une description d'une seule
    phrase très courte)."""
    texte = re.sub(r"\s+", " ", texte).strip()
    if len(texte) <= limite:
        return texte
    sortie = ""
    for phrase in _FIN_PHRASE.split(texte):
        candidat = (sortie + " " + phrase).strip()
        plafond = limite + souple if len(sortie) < 100 else limite
        if len(candidat) <= plafond:
            sortie = candidat
        else:
            break
    if len(sortie) >= (100 if souple else 50):
        return sortie
    coupe = texte[: limite - 1].rsplit(" ", 1)[0].rstrip(",;:—-– ")
    return coupe + "…"


# Un paragraphe qui commence ainsi renvoie à ce qui précède : mal placé seul
# dans une description. On le saute tant qu'un autre convient.
_OUVERTURE_ALLUSIVE = re.compile(
    r"^(C[’']est|Ce |Cet |Cette |Ces |Ceci|Cela|Il |Ils |Elle |Elles |Celui|Celle|Ceux"
    r"|S[’']il|Sinon|Mais |Donc |Ainsi|Alors|D[’']où|Dès lors|Et |Au début|À la fin"
    r"|Jusqu[’']ici|Rien |Même |Plus )")


def _paragraphes_de_prose(fragment):
    """Textes des paragraphes de prose du chapitre, dans l'ordre : sans
    formule, sans tableau ni figure, d'au moins 60 caractères."""
    f = _TABLE.sub("", _SVG.sub("", fragment))
    for m in _PARAGRAPHE.finditer(f):
        brut = m.group(1)
        if 'class="math' in brut or "<img" in brut:
            continue
        t = texte_brut(brut)
        if len(t) >= 60 and not t.startswith(("Chapitre ", "Figure ")):
            yield t


def premiere_phrase_utile(fragment):
    """Premier paragraphe de prose du chapitre qui se lise seul : sans
    formule, tableau ni figure, d'au moins 60 caractères, ne commençant pas
    par un renvoi à ce qui précède (« C'est… », « Il… »). À défaut d'un tel
    paragraphe, le premier de prose. None s'il n'y en a pas."""
    candidats = list(_paragraphes_de_prose(fragment))
    for t in candidats:
        if not _OUVERTURE_ALLUSIVE.match(t) and t.rstrip().endswith((".", "!", "?", "»", "…")):
            return t
    return candidats[0] if candidats else None


def description_chapitre(titre_cours, etiquette, titre, fragment, limite=200):
    """Description d'une page de chapitre : « Cours, chapitre N. » suivi de
    la première phrase de prose du chapitre ; à défaut, du titre."""
    debut = titre_cours
    if etiquette:
        debut += ", " + (etiquette[0].lower() + etiquette[1:])
    debut += "."
    corps = premiere_phrase_utile(fragment)
    if corps:
        return debut + " " + tronquer(corps, max(60, limite - len(debut) - 1))
    return "%s %s. Diapositives, polycopié, exercices corrigés et application interactive." % (debut, titre)


def _markdown_en_texte(md):
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)          # [texte](lien)
    t = re.sub(r"[*_`]+", "", t)                              # emphase, code
    return re.sub(r"\s+", " ", t).strip()


def description_cours(presentation_md, limite=200):
    """Description de la page d'accueil d'un cours : premier paragraphe de
    sa présentation, sans formule, réduit à `limite` caractères."""
    for bloc in re.split(r"\n\s*\n", presentation_md.strip()):
        if bloc.lstrip().startswith(("#", "|", ":", "`", "<")):
            continue
        if "$" in bloc:
            continue
        t = _markdown_en_texte(bloc)
        if len(t) >= 70:
            return tronquer(t, limite, souple=60)
    return None


# ---------------------------------------------------------------------------
# Noms accessibles des figures
# ---------------------------------------------------------------------------

_TITRE_SECTION = re.compile(r"<h([2-6])\b[^>]*>(.*?)</h\1>", re.S)
_SVG_FIGURE = re.compile(r'<svg\b[^>]*\brole="img"[^>]*>')
_MATH = re.compile(r'<span class="math[^"]*">(.*?)</span>', re.S)
_GREC = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "varepsilon": "ε",
    "epsilon": "ε", "theta": "θ", "lambda": "λ", "mu": "μ", "nu": "ν",
    "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "chi": "χ",
    "psi": "ψ", "omega": "ω", "Delta": "Δ", "Sigma": "Σ", "Omega": "Ω",
}
_EXPOSANT = {"2": "²", "3": "³"}


def _tex_en_texte(tex):
    """Formule TeX très simple -> texte lisible (\\alpha -> α, R^2 -> R²)."""
    t = re.sub(r"\\([A-Za-z]+)", lambda m: _GREC.get(m.group(1), m.group(1)), tex)
    t = re.sub(r"\^\{?(\d)\}?", lambda m: _EXPOSANT.get(m.group(1), "^" + m.group(1)), t)
    return re.sub(r"[{}\\]", "", t).strip()


def _titre_lisible(fragment_titre):
    avec_formules = _MATH.sub(lambda m: _tex_en_texte(html.unescape(m.group(1))), fragment_titre)
    return texte_brut(avec_formules)


def nommer_figures(fragment):
    """Donne un nom accessible (aria-label) à chaque figure <svg role="img">
    du fragment : « Figure N : titre de la section où elle se trouve ».

    Les figures sont des dessins sans texte (les caractères y sont des
    tracés) ; sans nom, un lecteur d'écran annonce seulement « image ». Ce
    nom situe la figure ; le texte qui l'entoure la commente. Le calcul est
    déterministe : un nom déjà présent est remplacé, jamais doublé."""
    titres = [(m.end(), _titre_lisible(m.group(2))) for m in _TITRE_SECTION.finditer(fragment)]
    morceaux, dernier, n = [], 0, 0
    for m in _SVG_FIGURE.finditer(fragment):
        n += 1
        balise = re.sub(r'\saria-label="[^"]*"', "", m.group(0))
        titre = ""
        for fin, texte in titres:
            if fin > m.start():
                break
            titre = texte
        nom = "Figure %d" % n + (" : " + titre if titre else "")
        balise = balise[:-1] + ' aria-label="%s">' % html.escape(nom, quote=True)
        morceaux.append(fragment[dernier:m.start()])
        morceaux.append(balise)
        dernier = m.end()
    morceaux.append(fragment[dernier:])
    return "".join(morceaux)
