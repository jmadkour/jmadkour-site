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
})();
