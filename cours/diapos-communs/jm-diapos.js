/* =====================================================================
   Intégration des diaporamas au site jmadkour.org
   1. accorde le diaporama au thème choisi par le visiteur sur le site
   2. ajoute un bouton de bascule clair / sombre, en haut à droite
   3. ajoute deux liens de retour discrets, en bas à gauche
   Chargé par tous les diaporamas via scripts/integrer-diapos.py.
   ===================================================================== */

(function () {
  "use strict";

  var SOLEIL =
    '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">' +
    '<circle cx="8" cy="8" r="3.2" fill="currentColor"/>' +
    '<path d="M8 0v2.1M8 13.9V16M0 8h2.1M13.9 8H16' +
    'M2.34 2.34l1.5 1.5M12.16 12.16l1.5 1.5' +
    'M13.66 2.34l-1.5 1.5M3.84 12.16l-1.5 1.5" ' +
    'stroke="currentColor" stroke-width="1.4" stroke-linecap="round" fill="none"/>' +
    "</svg>";

  var LUNE =
    '<svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true">' +
    '<path d="M6 .278a.77.77 0 0 1 .08.858 7.2 7.2 0 0 0-.878 3.46c0 4.021 ' +
    "3.278 7.277 7.318 7.277q.792-.001 1.533-.16a.79.79 0 0 1 .81.316.73.73 " +
    "0 0 1-.031.893A8.35 8.35 0 0 1 8.344 16C3.734 16 0 12.286 0 7.71 0 4.266 " +
    '2.114 1.312 5.124.06A.75.75 0 0 1 6 .278"/>' +
    "</svg>";

  /* ---------- 1. Thème ----------
     Le site écrit le thème réellement appliqué dans « jm-theme »
     (voir _includes/theme-sync.html). À défaut — visiteur arrivé
     directement sur un diaporama — on suit la préférence du système. */

  function themeVoulu() {
    var t = null;
    try { t = localStorage.getItem("jm-theme"); } catch (e) {}
    if (t === "dark" || t === "light") return t;
    return window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark" : "light";
  }

  function appliquer() {
    var sombre = themeVoulu() === "dark";
    document.body.classList.toggle("jm-dark", sombre);
    var b = document.querySelector(".jm-theme");
    if (b) {
      // Le bouton annonce ce vers quoi il fait basculer.
      b.innerHTML = sombre ? SOLEIL : LUNE;
      b.setAttribute(
        "title", sombre ? "Passer au thème clair" : "Passer au thème sombre"
      );
      b.setAttribute("aria-label", b.getAttribute("title"));
    }
  }

  function basculer() {
    var nouveau = themeVoulu() === "dark" ? "light" : "dark";
    try { localStorage.setItem("jm-theme", nouveau); } catch (e) {}
    appliquer();
  }

  appliquer();

  // Le visiteur peut basculer le thème dans un autre onglet du site.
  window.addEventListener("storage", function (e) {
    if (e.key === "jm-theme") appliquer();
  });

  /* ---------- 2 et 3. Boutons ----------
     Les cibles des liens se déduisent du chemin : un diaporama vit
     toujours dans cours/<cours>/slides/<chapitre>.html, donc le cours est
     deux niveaux au-dessus. Rien à paramétrer diaporama par diaporama. */

  function poserBoutons() {
    if (!document.querySelector(".jm-theme")) {
      var b = document.createElement("button");
      b.className = "jm-theme";
      b.type = "button";
      b.addEventListener("click", basculer);
      document.body.appendChild(b);
    }

    if (!document.querySelector(".jm-retour")) {
      var nav = document.createElement("nav");
      nav.className = "jm-retour";
      nav.setAttribute("aria-label", "Retour au site");
      [
        { href: "../index.html", texte: "↩ Le cours" },
        { href: "../ressources.html", texte: "Ressources" }
      ].forEach(function (l) {
        var a = document.createElement("a");
        a.href = l.href;
        a.textContent = l.texte;
        nav.appendChild(a);
      });
      document.body.appendChild(nav);
    }

    appliquer(); // renseigne l'icône du bouton qui vient d'être créé
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", poserBoutons);
  } else {
    poserBoutons();
  }

  /* ---------- 4. Ajustement des diapositives qui débordent ----------
     reveal.js travaille dans une boîte de taille fixe (1280 x 720 ici) et
     ne réduit rien : une diapositive plus haute que la boîte voit sa fin
     passer sous le bord de l'écran, définitivement invisible. Beamer, lui,
     scinde ou comprime le cadre — d'où un PDF correct et un HTML tronqué
     à partir de la même source.

     On mesure donc la diapositive affichée et, si elle dépasse, on réduit
     sa taille de texte juste assez pour qu'elle rentre. Les marges et les
     interlignes de reveal étant exprimés en em, ils suivent. Les autres
     diapositives ne sont pas touchées. */

  // Plancher : en deçà, le texte deviendrait illisible. Fixé assez bas
  // pour qu'aucune diapositive n'ait besoin de défiler — une barre de
  // défilement au bord d'une diapositive n'a pas de sens et abîme la
  // lecture. Une diapositive qui atteindrait ce plancher relève de la
  // réécriture, pas de la mise en page.
  var PLANCHER = 0.42;
  var MARGE = 8;         // évite de frôler le bord au pixel près

  function boite() {
    var s = document.querySelector(".reveal .slides");
    return s ? s.clientHeight : 0;
  }

  function baseEnPx() {
    var v = getComputedStyle(document.documentElement)
              .getPropertyValue("--r-main-font-size");
    var n = parseFloat(v);
    return isNaN(n) ? 32 : n;
  }

  function ajuster(section) {
    if (!section) return;
    var dispo = boite();
    if (!dispo) return;

    section.style.fontSize = "";
    section.removeAttribute("data-jm-ajuste");

    var base = baseEnPx();
    var taille = base;

    // Deux passes suffisent : la hauteur ne décroît pas exactement en
    // proportion de la police (images, formules), une seconde mesure
    // corrige le résidu.
    for (var i = 0; i < 4; i++) {
      var haut = section.scrollHeight;
      if (haut <= dispo - MARGE) break;
      var k = (dispo - MARGE) / haut;
      taille = Math.max(taille * k, base * PLANCHER);
      section.style.fontSize = taille.toFixed(2) + "px";
      section.setAttribute("data-jm-ajuste", "");
    }
  }

  function ajusterCourante() {
    if (!window.Reveal || !Reveal.getCurrentSlide) return;
    ajuster(Reveal.getCurrentSlide());
  }

  function brancher() {
    if (!window.Reveal || !Reveal.on) return false;
    Reveal.on("ready", ajusterCourante);
    Reveal.on("slidechanged", ajusterCourante);
    Reveal.on("resize", ajusterCourante);
    // Une diapositive déjà affichée au moment où ce script s'exécute.
    ajusterCourante();
    return true;
  }

  if (!brancher()) {
    // reveal.js n'est pas encore initialisé : on réessaie brièvement.
    var essais = 0;
    var minuteur = setInterval(function () {
      if (brancher() || ++essais > 40) clearInterval(minuteur);
    }, 150);
  }

  window.addEventListener("resize", function () {
    clearTimeout(window.__jmRedim);
    window.__jmRedim = setTimeout(ajusterCourante, 150);
  });
})();
