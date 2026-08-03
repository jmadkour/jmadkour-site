#!/usr/bin/env bash
# =====================================================================
#  Protège par mot de passe le parcours Doctorat du site (via staticrypt).
#
#  À exécuter après `quarto render` (qui produit _site/) et avant la
#  publication sur gh-pages. Le pipeline GitHub Actions l'appelle
#  automatiquement (voir .github/workflows/publish.yml) ; ce script
#  peut aussi être lancé en local pour vérifier le résultat avant de
#  pousser :
#
#    export STATICRYPT_PASSWORD="le-mot-de-passe"
#    quarto render
#    ./scripts/protect-doctorat.sh
#    npx serve _site      # ou tout autre serveur local, pour prévisualiser
#
#  Prérequis : Node.js (pour `npx staticrypt`) et la variable d'environnement
#  STATICRYPT_PASSWORD (secret GitHub Actions en CI, export local pour un
#  test manuel).
#
#  Usage : ./scripts/protect-doctorat.sh [chemin_vers_site]
#  (par défaut : _site)
# =====================================================================
set -euo pipefail

SITE="${1:-_site}"

if [ -z "${STATICRYPT_PASSWORD:-}" ]; then
  echo "Erreur : la variable STATICRYPT_PASSWORD n'est pas définie." >&2
  exit 1
fi

if [ ! -d "$SITE" ]; then
  echo "Erreur : le dossier '$SITE' n'existe pas. Lancer 'quarto render' d'abord." >&2
  exit 1
fi

# Sel fixe (non secret) pour que le bouton "Se souvenir de moi" reste valide
# d'un déploiement à l'autre, et que le mot de passe entré sur une page
# déverrouille aussi les autres pages protégées du même domaine.
STATICRYPT_SALT="f189d2816f1f746be1f302629ad6cd95"

# Les répertoires de cours qui composent le parcours Doctorat (voir doctorat.qmd).
# Ne PAS ajouter ici les cours de Licence/Master : seuls ces neuf dossiers, plus
# la page d'accueil doctorat.html, doivent être protégés.
DOCTORAT_DIRS=(
  fondements-gestion-risques
  analyse-quantitative
  marches-produits-financiers
  modeles-evaluation-risque
  risque-marche
  risque-credit
  risque-operationnel-resilience
  risque-liquidite-tresorerie
  gestion-risques-actifs
)

echo "== 1. Retrait des pages Doctorat de l'index de recherche, du sitemap, et robots.txt =="
python3 - "$SITE" <<'PYEOF'
import json
import re
import sys
import pathlib

site = pathlib.Path(sys.argv[1])

doctorat_dirs = [
    "fondements-gestion-risques", "analyse-quantitative",
    "marches-produits-financiers", "modeles-evaluation-risque",
    "risque-marche", "risque-credit", "risque-operationnel-resilience",
    "risque-liquidite-tresorerie", "gestion-risques-actifs",
]
protected_prefixes = ["doctorat.html"] + [f"cours/{d}/" for d in doctorat_dirs]


def is_protected(href):
    return any(href == p or href.startswith(p) for p in protected_prefixes)


# --- search.json : retire les entrées Doctorat de l'index plein texte ---
search_file = site / "search.json"
if search_file.exists():
    data = json.loads(search_file.read_text(encoding="utf-8"))
    before = len(data)
    data = [e for e in data if not is_protected(e.get("href", ""))]
    search_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"  search.json : {before} -> {len(data)} entrées")
else:
    print("  search.json : absent, ignoré")

# --- sitemap.xml : retire les URL Doctorat ---
sitemap_file = site / "sitemap.xml"
if sitemap_file.exists():
    text = sitemap_file.read_text(encoding="utf-8")
    blocks = re.findall(r"<url>.*?</url>", text, flags=re.DOTALL)
    kept = []
    removed = 0
    for b in blocks:
        m = re.search(r"<loc>(.*?)</loc>", b)
        loc = m.group(1) if m else ""
        rel = loc.split("jmadkour-site/")[-1] if "jmadkour-site/" in loc else loc.split("jmadkour.org/")[-1]
        if is_protected(rel):
            removed += 1
        else:
            kept.append(b)
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    footer = "</urlset>\n"
    body = "\n".join(kept)
    sitemap_file.write_text(header + body + ("\n" if body else "") + footer, encoding="utf-8")
    print(f"  sitemap.xml : {removed} URL(s) retirée(s)")
else:
    print("  sitemap.xml : absent, ignoré")

# --- robots.txt : décourage l'indexation des pages Doctorat ---
robots_file = site / "robots.txt"
disallow_lines = "\n".join(f"Disallow: /{p}" for p in protected_prefixes)
if robots_file.exists():
    text = robots_file.read_text(encoding="utf-8")
    if "User-agent: *" in text:
        text = text.replace("User-agent: *", "User-agent: *\n" + disallow_lines, 1)
    else:
        text = f"User-agent: *\n{disallow_lines}\n\n" + text
    robots_file.write_text(text, encoding="utf-8")
    print("  robots.txt : règles Disallow ajoutées")
else:
    print("  robots.txt : absent, ignoré")
PYEOF

echo "== 2. Chiffrement des pages Doctorat (staticrypt) =="

STATICRYPT_ARGS=(
  -p "$STATICRYPT_PASSWORD"
  --salt "$STATICRYPT_SALT"
  --config false
  --short
  --template-title "Accès réservé — Parcours Doctorat"
  --template-instructions "Ce contenu est réservé aux étudiants du parcours Doctorat. Merci de saisir le mot de passe transmis."
)

# Page d'accueil du parcours (doctorat.qmd -> doctorat.html)
if [ -f "$SITE/doctorat.html" ]; then
  npx --yes staticrypt "$SITE/doctorat.html" -d "$SITE" "${STATICRYPT_ARGS[@]}"
  echo "  doctorat.html chiffré"
fi

# Chaque cours du parcours Doctorat (page d'accueil + chapitres + diapositives)
for d in "${DOCTORAT_DIRS[@]}"; do
  dir="$SITE/cours/$d"
  if [ -d "$dir" ]; then
    npx --yes staticrypt "$dir"/* -r -d "$dir" "${STATICRYPT_ARGS[@]}"
    echo "  cours/$d chiffré"
  fi
done

echo "Protection du parcours Doctorat terminée."
echo ""
echo "NOTE : les fichiers PDF des diapositives (slides/*.pdf) ne sont pas"
echo "chiffrables par staticrypt (il ne protège que le HTML). Ils ne sont"
echo "plus référencés dans le sitemap/l'index de recherche et leur URL"
echo "n'apparaît que dans les pages HTML désormais chiffrées, mais un lien"
echo "direct vers un PDF, s'il est deviné ou partagé, resterait accessible."
