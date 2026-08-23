# Audit du site — 23 août 2026

Portée : les 164 pages du site, les 467 diaporamas publiés (8 285 pages de
diapositives), et la cohérence entre les deux dépôts.

---

## 1. Les débordements de diapositives

**430 diapositives sur 8 285 débordent du cadre**, soit 5,2 %. Le contenu y
descend sous le pied de page, chevauche le numéro de page, et dans les cas les
plus nets se trouve coupé en pleine phrase.

### Comment la mesure est faite

Le pied de page se dessine à 246,8 pt sur une page de 255,1 pt de haut. Une
diapositive est comptée en débordement dès qu'un mot de contenu — le numéro de
page exclu — descend sous 246 pt. La méthode lit les boîtes englobantes des
mots dans le PDF publié : elle mesure ce que le lecteur voit, non ce que la
source laisse supposer.

### L'ampleur du dépassement

| Dépassement au-delà de 240 pt | Diapositives |
|---|---:|
| une ligne (4 à 8 pt) | 42 |
| deux lignes (8 à 16 pt) | 362 |
| plus de deux lignes | 26 |

Médiane : 11 pt. Maximum : 17,3 pt. **Le dépassement est donc d'une à deux
lignes**, jamais davantage — ce qui écarte l'hypothèse de diapositives
massivement trop longues et désigne un excédent modeste mais systématique.

### Où ils se trouvent

| | Diapositives | Débordements | Taux |
|---|---:|---:|---:|
| Cours écrits en août 2026 | 1 387 | **189** | **13,6 %** |
| Cours antérieurs | 6 898 | 241 | 3,5 % |

Les huit cours écrits ou réécrits en août — *Principes d'économie*,
*Microéconomie*, *Macroéconomie*, *Apprentissage statistique*, *Apprentissage
profond*, *Inférence causale*, *Introduction à l'analyse des données*,
*Analyse des données avancée* — débordent **quatre fois plus** que les autres.

C'est imputable à leur rédaction : ils ont été écrits sans que le rendu soit
jamais examiné. La densité des blocs pédagogiques y a été poussée d'un cran
au-delà de ce que le cadre accepte.

### Les dix cours les plus touchés

| Cours | Pages | Débordements | Taux |
|---|---:|---:|---:|
| Introduction à l'analyse des données | 175 | 35 | 20,0 % |
| Macroéconomie | 138 | 25 | 18,1 % |
| Risque de liquidité et de trésorerie | 292 | 49 | 16,8 % |
| Apprentissage statistique | 144 | 23 | 16,0 % |
| Microéconomie | 152 | 23 | 15,1 % |
| Inférence causale | 152 | 22 | 14,5 % |
| Apprentissage profond | 145 | 20 | 13,8 % |
| Gestion des risques d'actifs | 178 | 23 | 12,9 % |
| Principes d'économie | 156 | 19 | 12,2 % |
| Risque de crédit | 411 | 37 | 9,0 % |

*Calcul stochastique* est le seul cours sans aucun débordement.

Le détail diapositive par diapositive — cours, chapitre source, titre, page,
position du bas de contenu — se trouve dans `debordements.csv`.

### Ce qui ne réglera pas le problème

Les réglages typographiques ont été essayés : resserrer l'espacement des blocs
ne rend qu'environ 4 pt, contre 11 pt à récupérer en médiane. Descendre le
corps de 10 à 9 pt suffirait, mais rendrait plus dense un texte qui l'est déjà
trop — le remède aggraverait ce qu'il soigne.

**Le dépassement étant d'une à deux lignes, la correction juste est
éditoriale** : retrancher une phrase, ou couper la diapositive en deux. C'est
aussi la seule qui améliore le cours plutôt que de masquer le symptôme.

---

## 2. Les liens

**Aucun lien mort du côté français.** Les 164 pages ont été parcourues et
toutes leurs cibles vérifiées.

**39 liens morts dans les pages traduites** — treize en anglais, treize en
espagnol, treize en arabe. Ils pointent vers des diaporamas dont le nom a
changé lors de la refonte (`regression-lineaire-simple.pdf`,
`distributions-continues.pdf`, etc.).

Ces pages datent d'avant la mise en pause de la traduction, signalée dans
`_quarto.yml` :

```yaml
# pre-render: translate-langs.py   # TRADUCTION EN PAUSE
```

Elles restent servies en ligne avec leurs liens cassés. Deux options : retirer
les liens vers les diaporamas de ces pages, ou dépublier les trois versions
jusqu'à la reprise de la traduction.

---

## 3. Une page orpheline

`cours/econometrie-introduction/regression-simple.qmd` — 94 lignes, rendue
dans `_site`, mais atteignable depuis aucune page ni aucune barre latérale.
C'est un vestige de l'époque où les chapitres étaient des pages HTML plutôt
que des diaporamas.

---

## 4. Ce qui est cohérent

Vérifié sans anomalie :

- **31 cours à diaporamas** déclarés dans `cours/chapitres.yml`, tous dotés
  d'une barre latérale, d'une entrée `resources` et d'un `index.qmd`.
- **467 PDF** publiés, correspondant exactement aux chapitres annoncés : aucun
  manquant, aucun orphelin.
- Aucune barre latérale citée par une page sans être définie.
- Les six dossiers hors `chapitres.yml` sont normaux : les cinq cours d'outils
  (`latex`, `python`, `r`, `matlab`, `eviews`), dont les chapitres sont des
  pages HTML, et `analyse-donnees`, réduit à une redirection.
- Plus aucune trace de la rubrique « Où en sommes-nous » dans les 467 PDF.
- La section « Prérequis » est présente au chapitre 1 de chaque cours.

---

## 5. Deux points de maintenance

**Le dépôt pèse 172 Mo**, dont 32 Mo de PDF en état courant. Chaque campagne de
rendu réécrit les 467 fichiers et l'historique en conserve toutes les versions.
Le dépôt grossira d'environ 30 Mo à chaque rendu complet. À surveiller ; une
purge de l'historique des PDF est envisageable si le clonage devient pénible.

**Le site pèse 43 Mo une fois construit**, dont les diaporamas. C'est
confortable pour un hébergement statique.
