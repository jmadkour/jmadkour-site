# Lecteur de chapitres à 3 volets

Les pages de cours du site (27 cours de Licence et de Master à ce jour)
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
| `normaliser.py` | Mise en forme du contenu des chapitres : titres abaissés d'un niveau, descriptions des pages, noms accessibles des figures. Aucune entrée-sortie. |
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

Pour le Doctorat : le parcours est en accès libre depuis le 28/10/2026
(plus de chiffrement), les nouvelles pages `chapitres/` sont donc publiées
comme celles des autres niveaux.

## Les figures

Les figures TikZ arrivent en SVG intégré dans le contenu des chapitres.
`alleger_svg.py` arrondit leurs coordonnées au centième de point, réécrit
les points des nuages en `<circle>` et met en commun les styles répétés.
Le 11/10/2026, appliqué aux 202 figures de plus de 100 Ko, il a ramené les
pages de chapitre de 58 à 45 Mo (le chapitre sur le chaos de 3,1 Mo à
0,5 Mo ; la page la plus lourde est désormais à 1,3 Mo, une surface 3D),
pour une différence de rendu inférieure à 0,03 % des pixels. Les matrices de
transformation ne sont jamais arrondies.

## Ce que les pages contiennent depuis le 28/10/2026

Issu de l'analyse du site du même jour :

- **Un `<title>` et une description par chapitre.** Le titre est
  « Titre du chapitre (Cours) – Jaouad Madkour » ; la description est
  « Cours, chapitre N. » suivi de la première phrase de prose du chapitre
  (`normaliser.description_chapitre`). Une page dont la prose commence par
  un renvoi (« C'est… », « Il… ») passe à la phrase suivante. Si le chapitre
  n'a aucune prose utile, une phrase de repli est écrite : le générateur
  l'indique (« description de repli »).
- **Un seul `<h1>`** : le titre du chapitre, surmonté du nom du cours et du
  numéro (`Chapitre N`, `Annexe X`, `Introduction`). Les sections du contenu
  sont des `<h2>`, les sous-sections des `<h3>` ; la classe `h1` ou `h2`
  d'origine est conservée pour que l'apparence ne change pas. L'en-tête
  de la page n'utilise plus `title:` mais `pagetitle:`, ce qui évite le
  bloc-titre de Quarto (donc un second `<h1>`).
- **Le contenu du chapitre est encadré** par `<!-- jm:contenu -->` et
  `<!-- /jm:contenu -->`. Ces repères permettent de le retrouver tel quel
  à chaque régénération ; ne pas les supprimer.
- **Chaque figure a un nom** (`aria-label`) : « Figure N : titre de la
  section ». Les figures sont des dessins dont les lettres sont des tracés,
  donc sans texte ; ce nom les situe pour un lecteur d'écran, le texte
  voisin les commente. Une description propre à chaque figure reste à
  rédiger si l'on veut aller plus loin (les sources `figsrc/*.tex` de
  l'atelier contiennent les étiquettes des axes).
- **Sur téléphone**, le sommaire est replié, les ressources du chapitre
  sont des puces sous le titre, et le panneau de droite est masqué.

Après toute modification des gabarits ou de `normaliser.py` :

```bash
python scripts/lecteur/generer_lecteur.py --migres      # réécrit les pages
python scripts/lecteur/generer_lecteur.py --migres --verifier   # doit répondre : 0 page à mettre à jour
python scripts/lecteur/verifier_reproduction.py          # doit répondre : 0 écart
```

## Autres scripts liés (racine `scripts/`)

- `generer-accueil.py` écrit la liste « Tous les cours » de la page d'accueil
  d'après `licence.qmd`, `master.qmd`, `doctorat.qmd` et `informatique.qmd`
  (les pages de niveau restent la seule source). À relancer après l'ajout ou
  le renommage d'un cours.
- `nettoyer-sitemap.py` retire du plan du site les pages de redirection et
  les pages `noindex` ; appelé par le workflow de publication.
