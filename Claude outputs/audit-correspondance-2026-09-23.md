# Audit de correspondance — atelier local ↔ dépôts GitHub ↔ site en ligne

Date : 23/09/2026. Portée : les 35 cours publiés du site (hors `cours-statistiques`, doublon volontairement non publié).

## 1. État des dépôts git

Le shell distant (device_bash) était indisponible pendant tout cet audit (panne côté machine liée à une mise à jour Windows du 8/09 — installer la mise à jour et redémarrer pour le retrouver). L'état git a donc été lu directement dans les fichiers internes de `.git` (refs, reflog) plutôt que via des commandes `git`.

**Les deux dépôts sont synchronisés avec GitHub** : dans `stats-eco-cours` et dans `jmadkour-site`, `refs/heads/main` est strictement identique à `refs/remotes/origin/main`. Tout ce qui a été commité localement a donc bien été poussé — y compris le commit le plus récent de chaque dépôt, celui de Risque opérationnel & résilience :
- `stats-eco-cours` : `d31600e...` — "Risque opérationnel & résilience : exercices, corrections et applications pour les 24 chapitres"
- `jmadkour-site` : `f0dc1e0...` — "Risque opérationnel & résilience : ressources et applications interactives pour les 24 chapitres, mise à jour de la page du cours"

Le reflog confirme aussi, dans l'ordre, tous les commits des 5 cours de gestion des risques (Value at Risk, Risque marché, Risque liquidité & trésorerie, Risque crédit, Risque opérationnel & résilience) : **les push que ces cours attendaient ont donc déjà été faits.**

Limite de cette vérification : sans shell, je n'ai pas pu faire un `git status` complet pour détecter d'éventuels fichiers modifiés/non commités qui ne seraient pas déjà dans le dernier commit. Rien dans les métadonnées consultées ne suggère de changement en attente, mais ce point n'est pas vérifié à 100 %.

## 2. Correspondance atelier (`stats-eco-cours`) ↔ site publié (`jmadkour-site`)

Méthode : pour chacun des 35 cours, comptage exact des fichiers dans `cours-<cours>/{exercices,outils}` (atelier) et `cours/<cours>/{ressources,outils}` (site), comparé au nombre de chapitres déclaré dans `chapitres.yml`. Travail réalisé par 3 sous-agents en parallèle (10 cours chacun) puis vérifié indépendamment par sondage direct sur plusieurs cours (algèbre linéaire, économétrie spatiale, modèles d'évaluation du risque, probabilités) — tous les écarts rapportés ont été confirmés.

| Cours | Atelier (`stats-eco-cours`) | Site (`jmadkour-site`) |
|---|---|---|
| Value at Risk | ✅ complet | ✅ complet |
| Risque marché | ✅ complet | ✅ complet |
| Risque liquidité & trésorerie | ✅ complet | ✅ complet |
| Risque crédit | ✅ complet | ✅ complet |
| Risque opérationnel & résilience | ✅ complet | ✅ complet |
| Économétrie financière | ✅ complet | ✅ complet |
| Économétrie introduction | ✅ complet | ✅ complet |
| Fondements gestion des risques | ✅ complet | ✅ complet |
| Gestion des risques actifs | ✅ complet | ✅ complet |
| Histoire de la pensée économique | ✅ complet | ✅ complet |
| Macroéconomie | ✅ complet | ✅ complet |
| Marchés & produits financiers | ✅ complet | ✅ complet |
| Microéconomie | ✅ complet | ✅ complet |
| Modélisation ARMA | ✅ complet | ✅ complet |
| Modélisation GARCH | ✅ complet | ✅ complet |
| Principes d'économie | ✅ complet | ✅ complet |
| Économétrie spatiale | ✅ complet | ✅ complet, **+ 10 fichiers `-poly.pdf` inattendus** (voir §3) |
| Économétrie avancée | ⚠️ 19/24 chapitres (ch.19 à 23 jamais produits) | ⚠️ 19/24, à l'identique de l'atelier |
| Modèles d'évaluation du risque | ✅ complet (16/16) | ⚠️ seulement 8/16 chapitres publiés |
| Algèbre linéaire | ✅ complet | ❌ rien publié (`ressources/` et `outils/` inexistants) |
| Analyse de données avancée | ✅ complet | ❌ rien publié |
| Analyse dynamique | ✅ complet | ❌ rien publié |
| Analyse mathématique | ✅ complet | ❌ rien publié |
| Analyse quantitative | ✅ complet | ❌ rien publié |
| Apprentissage profond | ✅ complet | ❌ rien publié |
| Apprentissage statistique | ✅ complet | ❌ rien publié |
| Calcul stochastique | ✅ complet | ❌ rien publié |
| Inférence causale | ✅ complet | ❌ rien publié |
| Introduction à l'analyse de données | ✅ complet | ❌ rien publié |
| Maths de gestion | ✅ complet | ❌ rien publié |
| Probabilités | ✅ complet | ❌ rien publié |
| Recherche opérationnelle | ✅ complet | ❌ rien publié |
| Statistique descriptive | ✅ complet | ❌ rien publié |
| Statistique inférentielle | ✅ complet | ❌ rien publié |
| Théorie des réseaux | ✅ complet | ❌ rien publié |

**Résumé : 16/35 cours parfaitement conformes des deux côtés** (les 5 cours de gestion des risques tout juste terminés + 11 cours plus anciens). **16 cours ont un atelier intégralement complet mais un site qui n'a jamais reçu leurs exercices/corrections/applis** (seules les diapositives y sont, via le pipeline automatique). **2 cours ont un écart de contenu** (Modèles d'évaluation du risque : publication interrompue à mi-parcours ; Économétrie avancée : construction elle-même inachevée, atelier et site à l'identique).

C'est une correction importante par rapport au constat du 10/09/2026 consigné dans `claude/overview.md` : ce constat ("31 cours sur 36 complets") ne portait que sur l'atelier `stats-eco-cours`, pas sur ce qui est réellement publié sur `jmadkour-site`. Sur ce critère-là, **16 cours seulement sont réellement complets en ligne**, le reste attend une étape de publication (renommage par slug + copie vers `jmadkour-site` + régénération du tableau via `generer-ressources.py`) qui n'a jamais été faite pour 16 d'entre eux et a été laissée à mi-chemin pour 1 autre.

## 3. Anomalies structurelles relevées

- **Page orpheline `jmadkour-site/cours/analyse-donnees/`** : ce dossier existe sur disque et sa page est publiquement accessible en ligne (`jmadkour.org/cours/analyse-donnees/`), mais son contenu est un doublon exact de "Introduction à l'analyse des données" (le cours réellement actif, sous le slug `introduction-analyse-donnees`, présent dans `chapitres.yml`). `analyse-donnees` n'est référencé nulle part dans `chapitres.yml` — c'est vraisemblablement un reliquat de l'ancien nom du cours avant renommage. Il reste une URL publique dupliquée, invisible au script de régénération du tableau (donc gelée). À supprimer ou rediriger.
- **Économétrie spatiale** : présente 10 fichiers `-poly.pdf` dans `ressources/` (un par chapitre), et ils sont bien branchés dans le tableau public (colonne "Polycopié" affiche "PDF" pour les 10 chapitres) — contrairement à ce que `claude/overview.md` indiquait ("colonne Polycopié jamais encore produite pour aucun cours"). Ce constat est donc à mettre à jour. En revanche, ce même cours n'a **aucune diapositive publiée** (`slides/` vide sur disque et "—" pour les 10 chapitres en ligne) : probablement une étape du pipeline `tout-publier.sh`/`sync-diapos.sh` jamais lancée pour ce cours.
- **Accès protégé (Parcours Doctorat)** : `risque-operationnel-resilience` et `modeles-evaluation-risque` (et vraisemblablement les autres cours du bloc doctoral) sont derrière le mot de passe staticrypt — comportement attendu, pas une anomalie. Cela a empêché une vérification directe des liens en ligne pour ces cours par navigation ; la vérification pour ceux-ci s'est donc appuyée sur la correspondance exacte des fichiers de part et d'autre (§2), pas sur un chargement de page.

## 4. Vérification du site en ligne

`WebFetch` est bloqué par le `robots.txt` de jmadkour.org (toute récupération automatisée est refusée) — conformément aux règles de cette session, je n'ai pas contourné ce blocage par une requête `curl`/script (qui aurait de toute façon été rejetée par la politique réseau du bac à sable). La vérification en ligne a donc été faite avec le navigateur intégré (chargement de pages réelles, comme un visiteur), en sondage sur plusieurs cours représentatifs plutôt qu'en testant systématiquement les ~500 liens de ressources des 35 cours :

- `algebre-lineaire`, `econometrie-spatiale`, `analyse-donnees` (orpheline) : pages publiques, chargées avec succès, tableaux de ressources conformes aux constats du §2 (liens absents affichés "—", liens présents affichés "PDF"/"Ouvrir").
- `risque-operationnel-resilience`, `modeles-evaluation-risque` : redirigent vers la page de mot de passe (Parcours Doctorat), cohérent avec la protection attendue.

Aucun lien cassé (404) n'a été observé parmi les liens effectivement présents sur les pages sondées — là où un cours n'a pas de ressources publiées, le site l'indique proprement par un tiret plutôt que par un lien mort.

## 5. Recommandations

1. Publier les 16 cours dont l'atelier est prêt mais dont rien n'est en ligne (même étape que celle appliquée aux 5 cours de gestion des risques : renommage par slug, copie vers `jmadkour-site/cours/<cours>/{ressources,outils}/`, régénération du tableau).
2. Terminer la publication de Modèles d'évaluation du risque (8 chapitres restants, contenu déjà prêt côté atelier) et décider du sort d'Économétrie avancée (5 chapitres jamais construits, ch.19-23).
3. Supprimer ou rediriger la page orpheline `cours/analyse-donnees/`.
4. Décider si les `-poly.pdf` d'Économétrie spatiale sont le début d'un chantier "Polycopié" à généraliser, ou un essai isolé à retirer ; publier ses diapositives manquantes dans tous les cas.
5. Mettre à jour `claude/overview.md` pour distinguer clairement, à l'avenir, "atelier complet" et "publié en ligne" — ce sont deux états différents (ce qui a causé la confusion initiale sur les "31 cours déjà complets").

Je peux me charger de tout ou partie de ces publications manquantes (c'est exactement le travail déjà fait pour les 5 cours de gestion des risques) — dis-moi lesquelles prioriser.
