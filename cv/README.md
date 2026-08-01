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

3. Produire le PDF :

```bash
cd cv && xelatex CV_Jaouad_Madkour.tex && cd ..
```

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

## Prérequis, à installer une seule fois

**PyYAML**, que lit le générateur :

```bash
pip install pyyaml
```

**Les polices Liberation**, qu'utilise la mise en page. Sans elles, XeLaTeX
s'arrête sur `The font "Liberation Serif" cannot be found`.

Téléchargez-les sur
<https://github.com/liberationfonts/liberation-fonts/releases>, décompressez,
sélectionnez tous les fichiers `.ttf`, clic droit, **Installer pour tous les
utilisateurs**. Il faut au minimum `LiberationSerif-*` et `LiberationSans-*`.

Vérification :

```bash
fc-list | findstr /i liberation
```

## Note sur le moteur LaTeX

Le PDF d'origine avait été produit avec **LuaTeX**, mais l'en-tête du fichier
indiquait XeLaTeX. Les deux fonctionnent. Une correction a été nécessaire :
`\newfontfamily\sffamily` redéfinissait une commande existante et a été remplacé
par `\renewfontfamily`. La compilation ne produit désormais aucune erreur.
