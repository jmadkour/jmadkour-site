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
└── .github/workflows/publish.yml   déploiement automatique
```
