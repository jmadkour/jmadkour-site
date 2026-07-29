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
SLIDES6="$HOME/Documents/stats-eco-cours/cours-value-at-risk"
SLIDES7="$HOME/Documents/stats-eco-cours/cours-analyse-donnees"
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

five () {  # $1=source (ex: chapitre11 ou annexeB)  $2=cours  $3=slug   (projet cours-econometrie-avancee)
  local src=$1 c=$2 s=$3
  ( cd "$SLIDES5" && quarto render "$src.qmd" --to revealjs )
  cp "$SLIDES5/$src.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES5" && quarto render "$src.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES5/$src.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   [econometrie-avancee] $src : HTML + PDF ✓"
  else
    echo "   [econometrie-avancee] $src : HTML ✓  (PDF conservé — LaTeX indisponible)"
  fi
}

six () {  # $1=numéro  $2=cours  $3=slug   (projet cours-value-at-risk)
  local n=$1 c=$2 s=$3
  ( cd "$SLIDES6" && quarto render "chapitre$n.qmd" --to revealjs )
  cp "$SLIDES6/chapitre$n.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES6" && quarto render "chapitre$n.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES6/chapitre$n.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   [value-at-risk] chapitre $n : HTML + PDF ✓"
  else
    echo "   [value-at-risk] chapitre $n : HTML ✓  (PDF conservé — LaTeX indisponible)"
  fi
}

seven () {  # $1=numéro  $2=cours  $3=slug   (projet cours-analyse-donnees)
  local n=$1 c=$2 s=$3
  ( cd "$SLIDES7" && quarto render "chapitre$n.qmd" --to revealjs )
  cp "$SLIDES7/chapitre$n.html" "$SITE/cours/$c/slides/$s.html"
  if ( cd "$SLIDES7" && quarto render "chapitre$n.qmd" --to beamer ) >/dev/null 2>&1; then
    cp "$SLIDES7/chapitre$n.pdf" "$SITE/cours/$c/slides/$s.pdf"
    echo "   [analyse-donnees] chapitre $n : HTML + PDF ✓"
  else
    echo "   [analyse-donnees] chapitre $n : HTML ✓  (PDF conservé — LaTeX indisponible)"
  fi
}

echo "Génération et copie des diapositives…"
seven 1 analyse-donnees            description-statistique
seven 2 analyse-donnees            analyse-composantes-principales
seven 3 analyse-donnees            analyse-factorielle-discriminante
seven 4 analyse-donnees            positionnement-multidimensionnel
seven 5 analyse-donnees            classification
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
five chapitre1  econometrie-avancee   nature-econometrie
five chapitre2  econometrie-avancee   regression-simple
five chapitre3  econometrie-avancee   regression-multiple-estimation
five chapitre4  econometrie-avancee   regression-multiple-inference
five chapitre5  econometrie-avancee   proprietes-asymptotiques
five chapitre6  econometrie-avancee   regression-multiple-approfondissements
five chapitre7  econometrie-avancee   variables-qualitatives
five chapitre8  econometrie-avancee   heteroscedasticite
five chapitre9  econometrie-avancee   specification-donnees
five chapitre10 econometrie-avancee   series-temporelles
five chapitre11 econometrie-avancee   series-temporelles-approfondissements
five chapitre12 econometrie-avancee   autocorrelation-heteroscedasticite
five chapitre13 econometrie-avancee   panel-simple
five chapitre14 econometrie-avancee   panel-avance
five chapitre15 econometrie-avancee   variables-instrumentales
five chapitre16 econometrie-avancee   equations-simultanees
five chapitre17 econometrie-avancee   variables-dependantes-limitees
five chapitre18 econometrie-avancee   series-temporelles-avancees
five chapitre19 econometrie-avancee   projet-empirique
five annexeA    econometrie-avancee   outils-mathematiques
five annexeB    econometrie-avancee   rappels-probabilite
five annexeC    econometrie-avancee   rappels-statistique-mathematique
five annexeD    econometrie-avancee   rappels-algebre-matricielle
five annexeE    econometrie-avancee   regression-matricielle
six 1   value-at-risk             var-autres-mesures-risque
six 2   value-at-risk             var-lineaire-parametrique
six 3   value-at-risk             simulation-historique
six 4   value-at-risk             var-monte-carlo
six 5   value-at-risk             var-portefeuille-options
six 6   value-at-risk             risque-modele
six 7   value-at-risk             scenarios-stress-testing
six 8   value-at-risk             allocation-capital
echo "Terminé. Vérifiez :  cd \"$SITE\" && quarto preview"
