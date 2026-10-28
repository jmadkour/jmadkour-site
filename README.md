# jmadkour.org — site pédagogique (Quarto)

Site de statistique et d'économétrie : Licence, Master, Doctorat. Contenu en
LaTeX, démonstrations interactives, code exécutable (WebR/Pyodide), déployé
gratuitement sur GitHub Pages avec le domaine **jmadkour.org**.

## Prévisualiser en local

Prérequis : [Quarto](https://quarto.org/docs/get-started/).

```bash
cd jmadkour-site
quarto preview      # ouvre le site en local, se rafraîchit à chaque modification
```

Pour construire le site sans le servir : `quarto render` (résultat dans `_site/`).

## Ajouter du contenu

- Un **cours** = un dossier sous `cours/`. Un **chapitre** = un fichier `.qmd`.
- Reliez chaque cours à la barre latérale dans `_quarto.yml` (section `sidebar`).
- Écrivez les maths en LaTeX (`$...$` en ligne, `$$...$$` en bloc).
- Intégrez une vidéo : `{{< video https://youtu.be/XXXX >}}`.
- Intégrez un PDF de diapositives : lien de téléchargement ou `<embed>`.

## Rendre le code exécutable (interactivité « révolutionnaire »)

Une fois, dans le dossier du site :

```bash
quarto add coatless-templates/quarto-webr       # R dans le navigateur
quarto add coatless-templates/quarto-pyodide    # Python dans le navigateur
```

Puis, dans une page : ajoutez `filters: [webr]` à l'en-tête et écrivez des blocs
` ```{webr-r} ` (voir l'exemple commenté dans
`cours/econometrie-introduction/regression-simple.qmd`).

## Déployer sur GitHub Pages (domaine jmadkour.org)

1. Créez un dépôt GitHub (ex. `jmadkour-site`) et poussez ce dossier :
   ```bash
   cd jmadkour-site
   git init && git add -A && git commit -m "Site initial"
   git branch -M main
   git remote add origin https://github.com/jmadkour/jmadkour-site.git
   git push -u origin main
   ```
2. Le workflow `.github/workflows/publish.yml` rend le site à chaque `git push`
   et le publie sur la branche `gh-pages`.
3. Dans le dépôt : **Settings → Pages** → *Source* = branche `gh-pages`.
4. Toujours dans **Settings → Pages → Custom domain**, saisissez `jmadkour.org`.
   Le fichier `CNAME` est déjà présent.
5. Chez votre **registrar** (DNS de jmadkour.org), ajoutez :
   - un enregistrement `CNAME` `www` → `jmadkour.github.io`, **ou**
   - quatre enregistrements `A` de l'apex `@` vers les IP de GitHub Pages :
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`.
6. Cochez **Enforce HTTPS** une fois le domaine vérifié.

> Astuce contenu léger : gardez les **vidéos sur YouTube** (intégrées, non stockées)
> et optimisez les images — le site reste très en dessous de la limite de 1 Go.

## Accès au parcours Doctorat

Depuis le 28/10/2026, le parcours Doctorat (`doctorat.qmd` et les neuf cours
listés dedans, sous `cours/`) est **en accès libre**, comme le reste du site :
les pages sont publiées en clair, apparaissent dans la recherche et dans le plan
du site, et les moteurs peuvent les indexer.

Auparavant, ces pages étaient chiffrées par mot de passe avec
[staticrypt](https://github.com/robinmoisson/staticrypt) à chaque publication.
Le script est conservé dans `scripts/archives/protect-doctorat.sh` ; le
secret `STATICRYPT_PASSWORD` n'est plus utilisé et peut être supprimé du dépôt
(**Settings → Secrets and variables → Actions**).

**Pour rétablir la protection** (si un jour un cours devait redevenir
réservé) :

1. Recréer le secret `STATICRYPT_PASSWORD` avec le mot de passe à distribuer.
2. Remettre `scripts/archives/protect-doctorat.sh` dans `scripts/`.
3. Dans `.github/workflows/publish.yml`, ajouter après l'étape
   « Retirer du plan du site… » une étape d'installation de Node.js
   (`actions/setup-node`, version 22) puis une étape
   `bash scripts/protect-doctorat.sh _site` avec
   `env: STATICRYPT_PASSWORD: ${{ secrets.STATICRYPT_PASSWORD }}`.

Le script retire alors les pages de l'index de recherche et du plan du site,
puis chiffre le HTML des neuf cours et de `doctorat.html`. Limite connue :
staticrypt ne chiffre que le HTML, pas les PDF.

## Structure

```
jmadkour-site/
├── _quarto.yml          réglages du site (navbar, sidebars, thème, LaTeX)
├── index.qmd            page d'accueil (hero + démo interactive)
├── licence.qmd / master.qmd / doctorat.qmd   parcours
├── about.qmd
├── theme-dark.scss / theme-light.scss        thème sombre / clair
├── cours/
│   ├── statistique-descriptive/index.qmd
│   └── econometrie-introduction/
│       ├── index.qmd
│       └── regression-simple.qmd   chapitre interactif (démo + code R)
├── CNAME                jmadkour.org
├── scripts/             générateurs et contrôles (lecteur de chapitres, accueil, plan du site…)
│   └── archives/        scripts inutilisés (protection du Doctorat par mot de passe)
└── .github/workflows/publish.yml   déploiement automatique (rendu → nettoyage du plan du site → publication)
```
