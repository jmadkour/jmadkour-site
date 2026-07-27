#!/usr/bin/env bash
# Régénère les diapositives des 13 chapitres et les copie dans le site.
# - le HTML (reveal.js) est toujours régénéré (ne nécessite pas LaTeX) ;
# - le PDF est régénéré s'il le peut (nécessite LaTeX + polices Fira) ; sinon on
#   garde le PDF déjà présent. Le script ne s'arrête jamais sur une erreur de PDF.
# Usage :  bash sync-diapos.sh
SLIDES="$HOME/Documents/stats-eco-cours/cours-statistiques"
SLIDES2="$HOME/Documents/stats-eco-cours/cours-analyse-mathematique"
SITE="$HOME/Documents/jmadkour-site"

one () {  # $1=numéro  $2=cours  $3=slug
  local n=$1 c=$2 s=$3
  ( cd "$SLIDES" && quarto render "chapitre$n.qmd" --to revealjs )
  cp "$SLIDES/chapitre$n.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES" && quarto render "chapitre$n.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES/chapitre$n.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   chapitre $n : HTML + PDF ✓"
  else
    echo "   chapitre $n : HTML ✓  (PDF conservé — LaTeX indisponible)"
  fi
}

two () {  # $1=numéro  $2=cours  $3=slug   (projet cours-analyse-mathematique)
  local n=$1 c=$2 s=$3
  ( cd "$SLIDES2" && quarto render "chapitre$n.qmd" --to revealjs )
  cp "$SLIDES2/chapitre$n.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES2" && quarto render "chapitre$n.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES2/chapitre$n.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   [analyse-math] chapitre $n : HTML + PDF ✓"
  else
    echo "   [analyse-math] chapitre $n : HTML ✓  (PDF conservé — LaTeX indisponible)"
  fi
}

echo "Génération et copie des diapositives…"
one 1  statistique-descriptive    donnees-et-statistiques
one 2  statistique-descriptive    tableaux-et-graphiques
one 3  statistique-descriptive    methodes-numeriques
one 4  probabilites               theorie-probabiliste
one 5  probabilites               distributions-discretes
one 6  probabilites               distributions-continues
one 7  statistique-inferentielle  echantillonnage
one 8  statistique-inferentielle  estimation-intervalle
one 9  statistique-inferentielle  test-hypotheses
one 10 statistique-inferentielle  comparaisons-moyennes-anova
one 11 statistique-inferentielle  proportions-independance
one 12 econometrie-introduction   regression-lineaire-simple
one 13 econometrie-introduction   regression-multiple
two 1  analyse-mathematique       rappels-ensembles-fonctions
two 2  analyse-mathematique       fonctions-une-variable
two 3  analyse-mathematique       optimisation-une-variable
two 4  analyse-mathematique       fonctions-plusieurs-variables
two 5  analyse-mathematique       optimisation-plusieurs-variables
echo "Terminé. Vérifiez :  cd \"$SITE\" && quarto preview"
