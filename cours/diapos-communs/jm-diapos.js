/* =====================================================================
   Intégration des diaporamas au site jmadkour.org
   1. accorde le diaporama au thème choisi par le visiteur sur le site
   2. ajoute deux liens de retour discrets, en bas à gauche
   Chargé par tous les diaporamas via scripts/integrer-diapos.py.
   ===================================================================== */

(function () {
  "use strict";

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
    document.body.classList.toggle("jm-dark", themeVoulu() === "dark");
  }

  appliquer();

  // Le visiteur peut basculer le thème dans un autre onglet du site.
  window.addEventListener("storage", function (e) {
    if (e.key === "jm-theme") appliquer();
  });

  /* ---------- 2. Liens de retour ----------
     Les cibles se déduisent du chemin : un diaporama vit toujours dans
     cours/<cours>/slides/<chapitre>.html, donc le cours est deux niveaux
     au-dessus. Rien à paramétrer diaporama par diaporama. */

  function poserLiens() {
    if (document.querySelector(".jm-retour")) return;

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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", poserLiens);
  } else {
    poserLiens();
  }
})();
