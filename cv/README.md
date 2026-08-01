# CV — source unique

Ce dossier contient le CV de Jaouad Madkour. Il alimente **deux sorties** :

- le **PDF** `cv/CV_Jaouad_Madkour.pdf`, que le bouton du site propose au téléchargement ;
- la page **`profile.qmd`**, c'est-à-dire la page « Jaouad Madkour » de jmadkour.org.

Une seule modification, deux résultats. Le CV et le site ne peuvent plus diverger.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `cv.yml` | **la source unique** — c'est le seul fichier à modifier |
| `modele.tex` | la mise en page LaTeX : couleurs, polices, macros, bandeau |
| `build.py` | le générateur — lit `cv.yml`, écrit le `.tex` et `../profile.qmd` |
| `CV_Jaouad_Madkour.tex` | **généré**, ne pas modifier à la main |
| `CV_Jaouad_Madkour.pdf` | **généré**, mais **versionné** — voir ci-dessous |

## Mettre le CV à jour

1. Ouvrir `cv.yml` et modifier le contenu — ajouter une publication, changer une date.
2. Régénérer :

```bash
python cv/build.py
```

3. Produire le PDF — **trois passes**, ce n'est pas une précaution inutile :

```bash
cd cv
xelatex CV_Jaouad_Madkour.tex
xelatex CV_Jaouad_Madkour.tex
xelatex CV_Jaouad_Madkour.tex
cd ..
```

Le bandeau bleu est posé par TikZ en `remember picture, overlay`, et les
rubriques sont des `longtable`. Les deux mécanismes écrivent des repères dans
le fichier `.aux` et ne les relisent qu'à la passe suivante. **Une seule passe
produit un CV sans bandeau et mal paginé.**

4. Vérifier, puis publier :

```bash
quarto render
git add cv profile.qmd
git commit -m "Mise à jour du CV"
git push
```

Le bouton « Télécharger le CV » de la page pointe directement sur
`cv/CV_Jaouad_Madkour.pdf` : aucune copie à faire ailleurs.

## Comment écrire dans `cv.yml`

Le texte est saisi en **LaTeX**, parce que c'est lui qui produit le PDF. Le générateur
le traduit automatiquement pour la page web.

| Vous écrivez | PDF | Page web |
|---|---|---|
| `\&` | & | & |
| `---` | — | — |
| `~` | espace insécable | espace insécable |
| `\ ` | espace fine après une abréviation | espace |
| `n\textsuperscript{o}` | n° | n° |
| `\href{url}{texte}` | lien | lien |
| `\textbf{\color{navy}X}` | X en gras bleu | **X** |

Les caractères `& % _ # $` doivent être précédés d'une barre oblique inversée.
Le `%` non échappé fait disparaître la fin de la ligne, sans le moindre message.

## Structure de `cv.yml`

```yaml
identite:      nom, titre, affiliation, contacts        → bandeau du CV
profil:        les paragraphes d'introduction
sections:      le corps du CV
  - titre: "Évolution professionnelle"
    blocs:
      - sous_titre: "Fonctions"
        type: liste                    # entrées {texte, date}
        entrees: [...]
      - sous_titre: "Publications..."
        type: publications             # entrées {titre, source, lien}
        entrees: [...]
competences:   les trois colonnes du bas
web:           blocs présents sur le site mais absents du CV papier
```

La clé `web.encarts` permet d'insérer un texte libre après un sous-titre donné —
c'est ainsi qu'apparaissent l'encart RiskoMetrics et le renvoi vers la page Publications.

## Pourquoi le PDF est versionné

GitHub Actions construit le site mais **ne compile pas de LaTeX**. Le PDF doit donc
être présent dans le dépôt, déjà produit. Les fichiers auxiliaires (`.aux`, `.log`,
`.out`) sont en revanche ignorés par git.

Conséquence : après chaque modification, **recompilez et committez le PDF**, sinon
le site continuera de proposer l'ancienne version au téléchargement.

## Vérification

Le générateur a été validé par un aller-retour : les données ont été extraites du
`.tex` d'origine, puis réémises depuis `cv.yml`. Le PDF obtenu est **textuellement
identique** à celui compilé depuis le fichier initial.

## Prérequis

**PyYAML**, que lit le générateur :

```bash
pip install pyyaml
```

C'est tout. **Aucune police à installer** : voir ci-dessous.

## Les polices

Le dossier `cv/fonts/` contient les quatre fichiers de **Liberation Serif**
(licence SIL OFL, redistribuable). `modele.tex` les charge par leur chemin,
avec l'option `Path=fonts/` de fontspec. Le CV a donc exactement le même aspect
sur n'importe quelle machine, sans installation système et sans repli silencieux
vers une autre police.

Le sans empattement — le bandeau, les titres de rubrique, les dates — est
**Latin Modern Sans**, présente dans toute distribution LaTeX.

### Pourquoi ce n'est pas Liberation Sans

Le fichier `.tex` d'origine demandait Liberation Sans. Il ne l'a jamais obtenue.
`\newfontfamily\sffamily{Liberation Sans}` échouait, la commande `\sffamily`
étant déjà définie ; et Liberation Sans n'était pas installée sur la machine de
compilation. Tout le sans empattement retombait donc sur Latin Modern Sans.

C'est cet accident qui donne au CV son aspect caractéristique. Il est désormais
inscrit explicitement dans `modele.tex`, et ne dépend plus de rien.

## Note sur le moteur LaTeX

Le PDF d'origine avait été produit avec **LuaTeX**. `modele.tex` est compilé ici
avec **XeLaTeX**, qui donne un résultat identique — à une réserve près, corrigée :
LuaTeX espaçait les lignes des rubriques de 21,1 pt, XeLaTeX de 14,2 pt. Le
`\arraystretch` de l'environnement `cvlist` rétablit ce pas quel que soit le
moteur.
