#!/usr/bin/env bash
# Régénère les diapositives des 13 chapitres et les copie dans le site.
# - le HTML (reveal.js) est toujours régénéré (ne nécessite pas LaTeX) ;
# - le PDF est régénéré s'il le peut (nécessite LaTeX + polices Fira) ; sinon on
#   garde le PDF déjà présent. Le script ne s'arrête jamais sur une erreur de PDF.
# Usage :  bash sync-diapos.sh
SLIDES="$HOME/Documents/stats-eco-cours/cours-statistiques"
SLIDES2="$HOME/Documents/stats-eco-cours/cours-analyse-mathematique"
SLIDES3="$HOME/Documents/stats-eco-cours/cours-algebre-lineaire"
SLIDES4="$HOME/Documents/stats-eco-cours/cours-econometrie-financiere"
SLIDES5="$HOME/Documents/stats-eco-cours/cours-econometrie-avancee"
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

three () {  # $1=numéro  $2=cours  $3=slug   (projet cours-algebre-lineaire)
  local n=$1 c=$2 s=$3
  ( cd "$SLIDES3" && quarto render "chapitre$n.qmd" --to revealjs )
  cp "$SLIDES3/chapitre$n.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES3" && quarto render "chapitre$n.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES3/chapitre$n.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   [algebre-lineaire] chapitre $n : HTML + PDF ✓"
  else
    echo "   [algebre-lineaire] chapitre $n : HTML ✓  (PDF conservé — LaTeX indisponible)"
  fi
}

four () {  # $1=numéro  $2=cours  $3=slug   (projet cours-econometrie-financiere)
  local n=$1 c=$2 s=$3
  ( cd "$SLIDES4" && quarto render "chapitre$n.qmd" --to revealjs )
  cp "$SLIDES4/chapitre$n.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES4" && quarto render "chapitre$n.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES4/chapitre$n.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   [econometrie-financiere] chapitre $n : HTML + PDF ✓"
  else
    echo "   [econometrie-financiere] chapitre $n : HTML ✓  (PDF conservé — LaTeX indisponible)"
  fi
}

five () {  # $1=numéro  $2=cours  $3=slug   (projet cours-econometrie-avancee)
  local n=$1 c=$2 s=$3
  ( cd "$SLIDES5" && quarto render "chapitre$n.qmd" --to revealjs )
  cp "$SLIDES5/chapitre$n.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES5" && quarto render "chapitre$n.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES5/chapitre$n.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   [econometrie-avancee] chapitre $n : HTML + PDF ✓"
  else
    echo "   [econometrie-avancee] chapitre $n : HTML ✓  (PDF conservé — LaTeX indisponible)"
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
three 1 algebre-lineaire          operations-matrices
three 2 algebre-lineaire          matrices-particulieres
three 3 algebre-lineaire          trace-determinant-rang
three 4 algebre-lineaire          inversion-matrices
three 5 algebre-lineaire          systemes-lineaires
three 6 algebre-lineaire          diagonalisation
three 7 algebre-lineaire          formes-quadratiques
four 1  econometrie-financiere    modeles-factoriels
four 2  econometrie-financiere    composantes-principales
four 3  econometrie-financiere    volatilite-correlation-classiques
four 4  econometrie-financiere    modeles-garch
four 5  econometrie-financiere    series-temporelles-cointegration
four 6  econometrie-financiere    copules
four 7  econometrie-financiere    modeles-avances
four 8  econometrie-financiere    prevision-evaluation
five 1  econometrie-avancee       nature-econometrie
five 2  econometrie-avancee       regression-simple
five 3  econometrie-avancee       regression-multiple-estimation
five 4  econometrie-avancee       regression-multiple-inference
five 5  econometrie-avancee       proprietes-asymptotiques
five 6  econometrie-avancee       regression-multiple-approfondissements
five 7  econometrie-avancee       variables-qualitatives
five 8  econometrie-avancee       heteroscedasticite
five 9  econometrie-avancee       specification-donnees
five 10 econometrie-avancee       series-temporelles
five 11 econometrie-avancee       rappels-probabilite
five 12 econometrie-avancee       rappels-statistique-mathematique
five 13 econometrie-avancee       rappels-algebre-matricielle
five 14 econometrie-avancee       regression-matricielle
five 15 econometrie-avancee       equations-simultanees
five 16 econometrie-avancee       variables-dependantes-limitees
five 17 econometrie-avancee       series-temporelles-avancees
five 18 econometrie-avancee       projet-empirique
five 19 econometrie-avancee       outils-mathematiques
echo "Terminé. Vérifiez :  cd \"$SITE\" && quarto preview"
