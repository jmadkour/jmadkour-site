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

## Protection par mot de passe du parcours Doctorat

Le parcours Doctorat (`doctorat.qmd` et les neuf cours listés dedans, sous
`cours/`) est chiffré par mot de passe avec [staticrypt](https://github.com/robinmoisson/staticrypt),
qui chiffre les pages HTML côté client (AES) — aucune page ni diapositive ne
sort en clair de la chaîne de publication. Le reste du site (Licence, Master,
Informatique, etc.) n'est pas concerné.

**Mise en place (une seule fois) :** dans le dépôt GitHub, allez dans
**Settings → Secrets and variables → Actions → New repository secret**, et
créez un secret nommé `STATICRYPT_PASSWORD` avec le mot de passe à distribuer
aux étudiants du Doctorat. C'est tout — le pipeline s'occupe du reste à chaque
publication.

**Comment ça marche :**

1. Le workflow rend le site (`quarto render`) sans le publier.
2. `scripts/protect-doctorat.sh` retire les pages Doctorat de l'index de
   recherche (`search.json`) et du plan du site (`sitemap.xml`), ajoute des
   règles `Disallow` dans `robots.txt`, puis chiffre chaque page HTML du
   parcours avec le mot de passe du secret `STATICRYPT_PASSWORD`.
3. Le site (désormais protégé) est publié sur `gh-pages`.

Pour changer le mot de passe : modifiez simplement la valeur du secret
`STATICRYPT_PASSWORD`, puis relancez le workflow (`Actions` → *Publier le
site* → *Run workflow*, ou un nouveau `git push`).

Pour prévisualiser le résultat en local avant de pousser :

```bash
export STATICRYPT_PASSWORD="le-mot-de-passe"
quarto render
./scripts/protect-doctorat.sh
npx serve _site   # ou tout autre serveur statique local
```

**Limite connue :** staticrypt ne chiffre que le HTML. Les PDF des
diapositives (`cours/<dossier>/slides/*.pdf`) ne sont donc pas chiffrés — ils
ne sont plus référencés nulle part en clair (recherche, plan du site, pages
HTML désormais protégées), mais un lien direct vers un PDF, s'il était deviné
ou partagé, resterait accessible sans mot de passe.

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
├── scripts/
│   └── protect-doctorat.sh   chiffrement du parcours Doctorat (staticrypt)
└── .github/workflows/publish.yml   déploiement automatique (render → protection → publication)
```
