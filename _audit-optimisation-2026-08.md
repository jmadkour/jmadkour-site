# Audit d'optimisation — jmadkour.org

Analyse du 7 août 2026. Porte sur les dépôts `jmadkour-site` et
`stats-eco-cours`, et sur le site publié.

Le préfixe `_` de ce fichier le tient hors du site : Quarto ignore les
fichiers dont le nom commence par un tiret bas.

---

## Ce qui a été corrigé

### 1. La police des diaporamas pesait quatre fois son nécessaire

`cours/diapos-communs/polices.css` embarquait chaque variante de Source
Sans Pro en **trois formats** : EOT, TrueType et WOFF. L'EOT ne sert qu'à
Internet Explorer 8, le TrueType à des navigateurs antérieurs à 2012 ;
aucun navigateur en service aujourd'hui n'en a l'usage.

En ne conservant que le WOFF : **2,76 Mo → 0,58 Mo**.

Ce fichier est chargé à l'ouverture du premier diaporama, puis mis en
cache. L'économie porte donc sur la première visite de chaque lecteur,
là où elle compte le plus.

Contrôle : les quatre variantes (normale, italique, demi-grasse, demi-grasse
italique) sont intactes et décodent bien en fichiers WOFF valides.

### 2. Les bibliothèques de Quarto étaient versionnées

`site_libs/` — 21 fichiers, 2,3 Mo — contenait Bootstrap, le moteur de
recherche, jQuery et **video.js** (572 ko à lui seul, alors qu'aucune page
du site n'utilise de vidéo intégrée).

Quarto reconstruit ce dossier à chaque rendu. Le versionner ne servait à
rien et figeait des versions que Quarto remplacerait de lui-même. Retiré
du suivi et ajouté au `.gitignore`, comme l'avaient été les rendus égarés.

Un cache Python (`__pycache__`) traînait également dans le dépôt.

### 3. Le site s'annonçait sous une adresse que personne ne voit

`site-url` déclarait `https://jmadkour.github.io/jmadkour-site/` alors que
le site est servi sur `jmadkour.org` (fichier `CNAME`).

C'était le défaut le plus coûteux en référencement : Quarto inscrivait
cette adresse dans le plan du site et dans les liens canoniques de chaque
page. Les moteurs indexaient donc un domaine que le visiteur n'atteint
jamais, et l'autorité du site se dispersait entre deux adresses pour un
contenu identique.

Corrigé, et complété par les métadonnées de partage — `open-graph` et
`twitter-card` — qui donnent un titre, une description et une image
lisibles lorsqu'un lien du site est partagé sur un réseau ou une
messagerie. Sans elles, un partage n'affiche qu'une adresse nue.

### 4. La chaîne de publication

Trois changements dans `.github/workflows/publish.yml` :

- `actions/checkout` et `actions/setup-node` passent de v4 à **v7**. Les
  v4 s'exécutent sur Node 20, que GitHub force déjà vers Node 24 et
  retirera de ses machines le 16 septembre 2026. L'avertissement visible
  à chaque exécution disparaît, et la chaîne est à l'abri de l'échéance.
- Node passe de 20 à **22** (version au support long terme).
- Ajout d'un verrou de **concurrence**. Deux poussées rapprochées
  lançaient deux rendus simultanés qui se disputaient la branche
  `gh-pages` : le plus lent écrasait le plus récent, ou échouait. Les
  rendus devenus inutiles sont désormais annulés au profit du dernier
  commit, qui contient de toute façon les précédents. C'est le mécanisme
  qui manquait lors des échecs en série de la semaine.

---

## Ce qui reste à décider

### Les 224 PDF de diapositives — 14 Mo

Chaque chapitre a son PDF, dupliquant le contenu du diaporama HTML. C'est
un service réel pour qui veut imprimer ou travailler hors ligne, mais
c'est un sixième du poids du dépôt.

Une solution intermédiaire existe : les déplacer vers les *releases*
GitHub, qui ne comptent pas dans la taille du dépôt ni du site publié, et
faire pointer les pages Ressources vers ces adresses. Le lecteur ne voit
aucune différence.

### Les descriptions de page — 170 pages sans

Aucune page ne déclare de `description`. Les moteurs de recherche
composent alors eux-mêmes un extrait, souvent maladroit, à partir des
premiers mots de la page. Depuis la réécriture des pages de cours, la
première phrase de chaque présentation ferait une description
convenable — elles pourraient être reprises automatiquement.

Les pages qui gagneraient le plus à en avoir : l'accueil, les trois
parcours, Publications, et les 19 pages de cours.

### Les trois pages « À propos » traduites

`en/about.qmd`, `es/about.qmd` et `ar/about.qmd` existent mais aucun lien
n'y mène : le sélecteur de langue ne propose que la page d'accueil de
chaque version. Soit les relier, soit les retirer.

### L'historique Git — 91 Mo

Les 785 Mo de diaporamas autonomes retirés la semaine dernière restent
dans l'historique, compressés. Sans conséquence pratique aujourd'hui : on
est très loin des seuils de GitHub. Une réécriture d'historique
ramènerait le dépôt sous 20 Mo, mais casse tous les clones existants —
disproportionné tant que rien ne gêne.

---

## Ce qui a été vérifié et se révèle sain

| Contrôle | Résultat |
|---|---|
| Liens internes | 699 vérifiés, aucun cassé |
| Front matter YAML | 170 pages, toutes valides |
| Barre latérale | 366 cibles, toutes résolues |
| Ressources des diaporamas | 224 diaporamas, toutes résolues |
| Textes alternatifs des images | aucune image sans alternative |
| Titres des cadres intégrés | tous renseignés |
| Libellés de liens | aucun « cliquez ici » |
| Contraste, thème sombre | 6,1:1 à 14,9:1 — niveau AA ou AAA |
| Contraste, thème clair | 5,3:1 à 14,8:1 — niveau AA ou AAA |
| Langue déclarée | globale en français, surchargée par version |

Sur le contraste, une alerte initiale s'est révélée fausse : la couleur
secondaire du thème clair (`#1d9e75`) donne 3,4:1 sur fond blanc, mais
elle ne sert que sur la barre de menu sombre, où elle atteint 4,7:1.

---

## Bilan chiffré

| | Avant | Après |
|---|---|---|
| Dépôt suivi | 91 Mo | 85 Mo |
| Police des diaporamas | 2,76 Mo | 0,58 Mo |
| Bibliothèques versionnées | 2,3 Mo | 0 |
| Fichiers suivis | 698 | 676 |

Rapporté au point de départ de la semaine — 806 Mo — le dépôt a été
divisé par plus de neuf.
