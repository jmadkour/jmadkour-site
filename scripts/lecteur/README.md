# Lecteur de chapitres à 3 volets

Les pages de cours du site (26 cours de Licence et de Master à ce jour)
présentent chaque chapitre dans un lecteur à trois volets : le sommaire à
gauche, le contenu détaillé au centre, les ressources du chapitre à droite.
Ce dossier contient tout ce qui les produit.

Ces scripts ont été reconstruits le 11/10/2026 : les originaux, écrits en
septembre dans l'espace de travail de Claude, n'avaient jamais été
versionnés et ont disparu avec lui. Les gabarits reproduisent octet pour
octet les 399 pages qu'ils avaient produites (`verifier_reproduction.py`).

## Les fichiers

| Fichier | Rôle |
|---|---|
| `lecteur.py` | Les gabarits des pages (accueil du cours, page de chapitre). Aucune entrée-sortie. |
| `generer_lecteur.py` | Écrit les pages d'un cours dans `cours/<cours>/`. |
| `rendre_atelier.py` | Produit, depuis l'atelier `stats-eco-cours`, le contenu central des chapitres, les polycopiés et les PDF « exercices corrigés ». |
| `alleger_svg.py` | Allège les figures SVG intégrées (sans perte visible ; appelé automatiquement). |
| `verifier_reproduction.py` | Contrôle que les gabarits reproduisent exactement les pages en place. |

Le style et le rendu des formules sont dans `_includes/lecteur.html`.
L'ordre et le titre des chapitres viennent de `cours/chapitres.yml`, le
titre du cours de l'entête de `cours/<cours>/index.qmd`, les liens vidéo de
`cours/liens-video.yml`.

## Usage courant : remettre les pages à jour

Après avoir déposé des diapositives, polycopiés, exercices ou applications,
modifié un titre dans `chapitres.yml` ou déclaré une vidéo :

```bash
python scripts/lecteur/generer_lecteur.py --migres            # tous les cours au lecteur
python scripts/lecteur/generer_lecteur.py algebre-lineaire    # un seul cours
python scripts/lecteur/generer_lecteur.py --migres --verifier # ce qui changerait, sans écrire
```

Le volet droit ne lie une ressource que si le fichier existe **au moment
où la page est écrite** ; sinon il l'affiche grisée. D'où l'ordre à
respecter : déposer les fichiers d'abord, régénérer les pages ensuite.
`tout-publier.sh` (atelier) le fait dans cet ordre.

## Passer un nouveau cours au lecteur (par exemple un cours du Doctorat)

1. **Atelier, une fois par cours** — aligner le cours sur ceux de la
   Licence (modèle : `cours-algebre-lineaire/`) :
   `_quarto.yml` avec les formats `pdf` (polycopié) et `html` (contenu
   central), `preamble-article.tex`, version récente de
   `pedago-blocks.lua` (encadrés repliables en HTML), `publier.sh` à jour.
2. **Diapositives** : `quarto render` puis `./publier.sh <site>` dans le
   dossier du cours.
3. **Le reste**, depuis la racine du site :

   ```bash
   python scripts/lecteur/rendre_atelier.py risque-credit \
       --atelier ../stats-eco-cours --fragments /tmp/frag-risque-credit \
       --polycopies --exercices --outils
   ```

   Le script vérifie d'abord que chaque chapitre de l'atelier correspond au
   bon slug (nombre de chapitres et titres) ; au moindre désaccord, il
   s'arrête sans rien produire.
   Ajouter `--outils` pour copier aussi les applications interactives
   (`outils/<cours>-app-<unité>.html` de l'atelier vers
   `cours/<cours>/outils/<slug>.html`).
4. **Vérifier** que `cours/<cours>/{slides,ressources,outils}/` contient
   bien, pour chaque slug, les quatre fichiers attendus.
5. **Les pages** :

   ```bash
   python scripts/lecteur/generer_lecteur.py risque-credit --fragments /tmp/frag-risque-credit
   python scripts/lecteur/verifier_reproduction.py risque-credit
   ```

   `index.qmd` garde sa présentation et son syllabus ; le tableau est
   remplacé par le lecteur.

Pour le Doctorat : `scripts/protect-doctorat.sh` chiffre récursivement tout
le HTML des neuf dossiers de cours, donc le nouveau dossier `chapitres/`
le sera sans rien changer. Les PDF (diapositives, polycopiés, exercices),
eux, ne sont pas chiffrables par staticrypt.

## Les figures

Les figures TikZ arrivent en SVG intégré dans le contenu des chapitres.
`alleger_svg.py` arrondit leurs coordonnées au centième de point, réécrit
les points des nuages en `<circle>` et met en commun les styles répétés.
Le 11/10/2026, appliqué aux 202 figures de plus de 100 Ko, il a ramené les
pages de chapitre de 58 à 45 Mo (le chapitre sur le chaos de 3,1 Mo à
0,5 Mo ; la page la plus lourde est désormais à 1,3 Mo, une surface 3D),
pour une différence de rendu inférieure à 0,03 % des pixels. Les matrices de
transformation ne sont jamais arrondies.
