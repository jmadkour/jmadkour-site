/* Arbre de l'accueil de jmadkour.org : un arbre procédural qui pousse.

   Le dessin n'est pas une image : à chaque chargement, le même arbre (même graine) est
   construit en mémoire puis peint sur deux canevas, au fil d'une croissance d'environ
   sept secondes. Les liens (racines, tronc, branches, fruits) sont de vrais <a> du
   HTML de la page ; leurs attributs data-x et data-y (repère de 1160 × 940) servent
   à la fois à les placer et à orienter la racine, la branche ou le rameau qui les porte.

   Ce que le générateur reprend des arbres réels :
   - ramification alternée, angle d'insertion de 40 à 55°, rameaux de plus en plus courts ;
   - modèle des tuyaux (Léonard de Vinci) : le rayon d'une branche est la somme, à la
     puissance 2,3, de celles de ses filles, d'où un affinement continu du tronc aux brindilles ;
   - phototropisme (les rameaux se redressent vers la lumière), gravitropisme des racines ;
   - empattement du tronc au collet, écorce fissurée, pousses de l'année vertes ;
   - feuilles groupées au bout des rameaux, plus sombres au cœur du houppier, éclairées
     en haut à gauche ; racines aussi étalées que le houppier.

   Paramètre d'adresse facultatif : ?graine=N pour voir un autre arbre. */
(function () {
  'use strict';
  var W = 1160, H = 940, GY = 570, CX = 580;          // repère logique ; GY : niveau du sol
  var HAUT = GY + 6, BAS0 = GY - 16;                  // le canevas du haut s'arrête un peu sous le sol
  var ECX = 580, ECY = 250, ERX = 392, ERY = 202;     // enveloppe du houppier (ellipse)
  var hero = document.getElementById('ab-hero');
  var stage = document.getElementById('ab-stage');
  var cvH = document.getElementById('ab-cv-haut'), cvB = document.getElementById('ab-cv-bas');
  if (!hero || !stage || !cvH || !cvB || !cvH.getContext) return;
  var cap = document.getElementById('ab-cap');
  var places = Array.prototype.slice.call(stage.querySelectorAll('[data-t]'));
  var nds = places.filter(function (e) { return e.tagName === 'A'; });
  var q = /[?&]graine=(\d+)/.exec(location.search);
  var GRAINE = q ? parseInt(q[1], 10) : 20261119;
  var calme = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  hero.classList.add('ab-js');

  /* ---------- hasard reproductible ---------- */
  function hasard(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function lissee(x) { x = x < 0 ? 0 : x > 1 ? 1 : x; return x * x * (3 - 2 * x); }
  function rebond(x) { x = x < 0 ? 0 : x > 1 ? 1 : x; var c = 1.6; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); }

  /* ---------- squelette : nœuds et chaînes ---------- */
  function Squelette(R) { this.R = R; this.n = []; this.c = []; }
  Squelette.prototype.noeud = function (x, y, p, l) {
    var i = this.n.length;
    this.n.push({ x: x, y: y, p: p, l: l, k: [], r: 0, t: 0 });
    if (p >= 0) this.n[p].k.push(i);
    return i;
  };
  /* Fait pousser une chaîne à partir du nœud o.de, dans la direction (o.dx, o.dy).
     Les règles du niveau fixent le pas, l'ondulation, le tropisme et la ramification. */
  Squelette.prototype.pousse = function (o) {
    var R = this.R, P = o.regles[o.niv], ch = { n: [o.de], niv: o.niv, vise: !!o.vise };
    this.c.push(ch);
    var p = this.n[o.de], x = p.x, y = p.y, dx = o.dx, dy = o.dy, fait = 0, prec = o.de;
    var cote = R() < .5 ? -1 : 1, prochain = P.esp * (.45 + .6 * R()), essais = 0, entre = !o.dedans || o.dedans(x, y);
    while (fait < o.lon) {
      var a = (R() - .5) * P.cou, ca = Math.cos(a), sa = Math.sin(a);
      var ex = dx * ca - dy * sa; dy = dx * sa + dy * ca; dx = ex;
      dy -= P.tro;                                    // > 0 : vers le haut ; < 0 : vers le bas
      if (o.vise) {
        var vx = o.vise.x - x, vy = o.vise.y - y, d = Math.sqrt(vx * vx + vy * vy);
        if (d < P.pas * 1.2) break;
        var kv = o.vise.k0 + (o.vise.k1 - o.vise.k0) * Math.min(1, fait / o.lon);
        dx += vx / d * kv; dy += vy / d * kv;
      }
      var m = Math.sqrt(dx * dx + dy * dy); dx /= m; dy /= m;
      var nx = x + dx * P.pas, ny = y + dy * P.pas;
      if (o.dedans && !entre && o.dedans(nx, ny)) entre = true;
      if (o.dedans && entre && !o.dedans(nx, ny)) {  // hors de l'enveloppe : on se replie vers l'intérieur
        if (o.vise || ++essais > 3) break;
        var ix = o.centre[0] - x, iy = o.centre[1] - y, im = Math.sqrt(ix * ix + iy * iy) || 1;
        dx += ix / im * .7; dy += iy / im * .7;
        continue;
      }
      x = nx; y = ny; fait += P.pas;
      var i = this.noeud(x, y, prec, o.niv); ch.n.push(i); prec = i;
      if (o.niv < o.max && fait >= prochain) {
        var lc = o.lon * P.lf * (.7 + .55 * R()) * (1 - .5 * fait / o.lon);
        if (lc > P.min && R() < P.prob) {
          cote = R() < .82 ? -cote : cote;
          var an = cote * P.ang * (.75 + .5 * R()), c2 = Math.cos(an), s2 = Math.sin(an);
          this.pousse({ de: i, dx: dx * c2 - dy * s2, dy: dx * s2 + dy * c2, lon: lc, niv: o.niv + 1,
            regles: o.regles, dedans: o.dedans, centre: o.centre, max: o.max });
        }
        prochain += P.esp * (.7 + .6 * R());
      }
    }
    ch.bout = prec;
    return ch;
  };
  /* Modèle des tuyaux : le rayon d'un nœud vient de ceux de ses enfants. Les enfants ont
     toujours un indice plus grand que leur parent : un parcours à rebours suffit. */
  Squelette.prototype.rayons = function (rBout, expo, effile, rBase, rMin) {
    var n = this.n, i, j;
    for (i = n.length - 1; i >= 0; i--) {
      var a = n[i];
      if (!a.k.length) { a.r = rBout; continue; }
      var s = 0;
      for (j = 0; j < a.k.length; j++) {
        var b = n[a.k[j]], d = Math.sqrt((b.x - a.x) * (b.x - a.x) + (b.y - a.y) * (b.y - a.y));
        s += Math.pow(b.r + effile * d, expo);
      }
      a.r = Math.pow(s, 1 / expo);
    }
    var f = rBase / n[0].r;
    for (i = 0; i < n.length; i++) n[i].r = Math.max(rMin, n[i].r * f);
  };
  /* Dates de naissance : chaque nœud naît après son parent, à la vitesse de son niveau ;
     une chaîne fille attend un court instant avant de partir. */
  Squelette.prototype.naissances = function (vit, attente, t0, t1) {
    var n = this.n, R = this.R, i, max = 0;
    n[0].t = 0;
    for (i = 1; i < n.length; i++) {
      var a = n[i], p = n[a.p], d = Math.sqrt((a.x - p.x) * (a.x - p.x) + (a.y - p.y) * (a.y - p.y));
      a.t = p.t + d / vit[a.l] + (a.l !== p.l ? attente * (.4 + R()) : 0);
      if (a.t > max) max = a.t;
    }
    for (i = 0; i < n.length; i++) n[i].t = t0 + (t1 - t0) * n[i].t / max;
  };

  /* ---------- les liens de la page ---------- */
  var liens = places.map(function (a) {
    return { el: a, t: a.getAttribute('data-t'), x: +a.getAttribute('data-x'), y: +a.getAttribute('data-y'), rev: 0 };
  });
  liens.forEach(function (L) {
    L.el.style.left = (L.x / W * 100) + '%';
    L.el.style.top = (L.y / H * 100) + '%';
  });
  function liensDe(t) { return liens.filter(function (L) { return L.t === t; }); }

  /* ---------- construction de l'arbre ---------- */
  var MASSES_ON = false, PLAFOND = 6000, A, Rc, FEUILLES, ARRIERE, MASSES, FISSURES, HERBE, CAILLOUX, FRUITS, T_FIN;
  var REG_H = [
    { pas: 8, cou: .045, tro: 0, esp: 0, ang: 0, lf: 0, min: 0, prob: 0 },               // 0 tronc
    { pas: 8, cou: .08, tro: .004, esp: 27, ang: .78, lf: .56, min: 22, prob: .95 },      // 1 charpentières
    { pas: 6.5, cou: .14, tro: .014, esp: 25, ang: .86, lf: .6, min: 14, prob: .85 },     // 2 branches
    { pas: 5.5, cou: .2, tro: .02, esp: 19, ang: .92, lf: .55, min: 9, prob: .7 },        // 3 rameaux
    { pas: 5, cou: .24, tro: .024, esp: 99, ang: 1, lf: .5, min: 99, prob: 0 }            // 4 brindilles
  ];
  var REG_B = [
    null,
    { pas: 7, cou: .13, tro: -.006, esp: 34, ang: .72, lf: .5, min: 18, prob: .8 },       // 1 racines maîtresses
    { pas: 5.5, cou: .2, tro: -.016, esp: 30, ang: .85, lf: .45, min: 12, prob: .5 },     // 2
    { pas: 4.5, cou: .26, tro: -.02, esp: 99, ang: 1, lf: .5, min: 99, prob: 0 }          // 3 radicelles
  ];
  function dansHouppier(x, y) {
    var u = (x - ECX) / ERX, v = (y - ECY) / ERY, th = Math.atan2(u, -v);
    var lobe = 1 + .06 * Math.sin(3 * th + 1.3) + .045 * Math.sin(5 * th + .4) + .03 * Math.sin(9 * th + 2.1);
    return u * u + v * v <= lobe * lobe && y < GY - 70;
  }
  function dansSol(x, y) { return x > 70 && x < W - 70 && y > GY + 4 && y < 806; }

  function construire(graine) {
    var R = hasard(graine), i;
    /* --- partie aérienne --- */
    A = new Squelette(R);
    A.noeud(CX, GY, -1, 0);
    var tronc = A.pousse({ de: 0, dx: 0, dy: -1, lon: 178, niv: 0, regles: REG_H, max: 0,
      vise: { x: CX + 8, y: GY - 178, k0: .02, k1: .05 } });
    // cibles des charpentières : les branches du Master, puis des lobes pour remplir le houppier
    var cibles = liensDe('branche').map(function (L) { return { x: L.x, y: L.y, lien: L }; });
    [-122, -98, -74, -50, -26, -2, 22, 46, 70, 94, 118].forEach(function (deg) {
      var th = deg * Math.PI / 180, f = .6 + .26 * R();
      var c = { x: ECX + Math.sin(th) * ERX * f, y: ECY - Math.cos(th) * ERY * f };
      for (var j = 0; j < cibles.length; j++) if (Math.hypot(cibles[j].x - c.x, cibles[j].y - c.y) < 95) return;
      cibles.push(c);
    });
    cibles.sort(function (a, b) { return a.y - b.y; });
    cibles.forEach(function (c) {
      var h = 108 + 70 * lissee((ECY + ERY * .35 - c.y) / (ERY * 1.25));   // hauteur du départ sur le tronc
      var k = Math.min(tronc.n.length - 1, Math.round(h / REG_H[0].pas));
      A.limite = Math.min(A.limite || 99, k - 1);
      var s = A.n[tronc.n[k]], vx = c.x - s.x, vy = c.y - s.y - 60, d = Math.hypot(vx, vy);
      var ch = A.pousse({ de: tronc.n[k], dx: vx / d, dy: vy / d, lon: Math.hypot(c.x - s.x, c.y - s.y) * 1.3,
        niv: 1, regles: REG_H, max: 4, dedans: dansHouppier, centre: [ECX, ECY + 40],
        vise: { x: c.x, y: c.y, k0: .03, k1: .16 } });
      if (c.lien) c.lien.bout = ch.bout;
      // quelques rameaux autour du bout de la charpentière
      for (var j = 0; j < 3; j++) {
        var an = (j - 1) * 1.1 + (R() - .5) * .4;
        A.pousse({ de: ch.bout, dx: Math.sin(an), dy: -Math.cos(an), lon: 30 + 25 * R(), niv: 3,
          regles: REG_H, max: 4, dedans: dansHouppier, centre: [ECX, ECY] });
      }
    });
    // rameaux porteurs des fruits
    FRUITS = liensDe('fruit').map(function (L) {
      var ax = L.x, ay = L.y - 24, best = -1, bd = 1e9;
      for (var j = 0; j < A.n.length; j++) {
        var nd = A.n[j]; if (nd.l < 2 || nd.y > ay - 6) continue;
        var d = Math.hypot(nd.x - ax, nd.y - ay); if (d < bd) { bd = d; best = j; }
      }
      var s = A.n[best], ch = A.pousse({ de: best, dx: (ax - s.x) / bd, dy: (ay - s.y) / bd, lon: bd * 1.5, niv: 3,
        regles: REG_H, max: 3, vise: { x: ax, y: ay, k0: .2, k1: .4 } });
      return { lien: L, bout: ch.bout, x: L.x, y: L.y };
    });
    A.rayons(.55, 2.3, .011, 25, .5);
    for (i = 0; i < tronc.n.length; i++) {                // empattement au collet
      var nt = A.n[tronc.n[i]];
      nt.r *= 1 + .8 * Math.exp(-(GY - nt.y) / 16);
    }
    A.naissances([150, 120, 105, 90, 75], .35, .7, 5.6);

    /* --- racines --- */
    Rc = new Squelette(R);
    Rc.noeud(CX, GY + 1, -1, 0);
    var visees = liensDe('racine').map(function (L) { return { x: L.x, y: L.y - 22, lien: L }; });
    [[-1, .16], [1, .14], [-1, 1.15], [1, 1.2]].forEach(function (v) {
      visees.push({ cote: v[0], pente: v[1] });
    });
    visees.forEach(function (v) {
      var cote = v.lien ? (v.x < CX ? -1 : 1) : v.cote;
      var pivot = v.lien && Math.abs(v.x - CX) < 40;      // cible sous le tronc : racine pivot
      var col = Rc.noeud(pivot ? CX : CX + cote * (5 + 16 * R()), GY + 3 + 3 * R(), 0, 1);
      var o = { de: col, niv: 1, regles: REG_B, max: 3, dedans: dansSol, centre: [CX, GY + 120] };
      if (v.lien) {
        var vx = v.x - CX, vy = v.y - GY, d = Math.hypot(vx, vy);
        o.dx = pivot ? 0 : vx / d + cote * .5; o.dy = pivot ? 1 : vy / d * .4 + .25;
        var m = Math.hypot(o.dx, o.dy); o.dx /= m; o.dy /= m;
        o.lon = d * 1.45; o.vise = { x: v.x, y: v.y, k0: .02, k1: .2 };
        v.lien.bout = Rc.pousse(o).bout;
      } else {
        o.dx = cote * Math.cos(v.pente); o.dy = Math.sin(v.pente);
        o.lon = v.pente > 1 ? 120 + 60 * R() : 210 + 140 * R();
        Rc.pousse(o);
      }
    });
    Rc.rayons(.45, 2.3, .016, 21, .4);
    Rc.naissances([1, 120, 100, 80], .25, 0, 2.6);

    /* --- feuilles et masses d'ombre --- */
    FEUILLES = []; MASSES = [];
    var sx = -.55, sy = -.83;                            // direction de la lumière (haut gauche)
    for (i = 0; i < A.n.length; i++) {
      var nd = A.n[i];
      if (nd.l < 3 || nd.r > 2.2) continue;
      var bout = !nd.k.length, nb = bout ? 5 + Math.floor(R() * 3) : (R() < .45 ? 1 : 0);
      var um = (nd.x - ECX) / ERX, vm = (nd.y - ECY) / ERY;
      if (bout && R() < .7 && um * um + vm * vm < .8 && MASSES_ON) MASSES.push({ x: nd.x, y: nd.y + 4, r: 10 + 8 * R(), t: nd.t + .2 });
      for (var j = 0; j < nb; j++) {
        var u = (nd.x - ECX) / ERX, v = (nd.y - ECY) / ERY, rho = Math.min(1.15, Math.sqrt(u * u + v * v));
        var ox = (R() - .5) * 11, oy = (R() - .5) * 11;
        var dehors = Math.atan2(nd.y - ECY + 60, nd.x - ECX);
        var ang = dehors + (R() - .5) * 2.6 + .35;       // les feuilles pendent un peu
        var cl = .26 + .4 * rho + .32 * (u * sx + v * sy) * Math.sqrt(rho) + (R() - .5) * .26;
        FEUILLES.push({ x: nd.x + ox, y: nd.y + oy, c: Math.cos(ang), s: Math.sin(ang), e: .72 + .45 * R(),
          b: Math.max(0, Math.min(1, cl)), f: R() < .5 ? 0 : 1, t: nd.t + .3 + .6 * R() });
      }
    }
    /* Feuillage d'arrière-plan : la moitié du houppier qui est derrière les branches, plus sombre.
       Peint avant le bois, il donne la profondeur (feuilles derrière, branches, feuilles devant). */
    ARRIERE = [];
    var essai = 0;
    while (ARRIERE.length < 3800 && essai++ < 60000) {
      var xa = ECX + (R() * 2 - 1) * ERX * 1.08, ya = ECY + (R() * 2 - 1) * ERY * 1.08;
      if (!dansHouppier(xa, ya)) continue;
      var ua = (xa - ECX) / ERX, va = (ya - ECY) / ERY, ra = Math.sqrt(ua * ua + va * va);
      if (R() > .45 + .55 * ra) continue;
      var aa = R() * 6.283;
      ARRIERE.push({ x: xa, y: ya, c: Math.cos(aa), s: Math.sin(aa), e: .95 + .5 * R(), f: R() < .5 ? 0 : 1,
        b: Math.max(0, Math.min(.55, .06 + .3 * ra + .2 * (ua * sx + va * sy) + (R() - .5) * .16)),
        t: 3.3 + 2.6 * ra + .8 * R() });
    }
    ARRIERE.sort(function (a, b) { return a.b - b.b; });
    if (FEUILLES.length > PLAFOND) {                   // budget de dessin : on éclaircit au hasard
      var garde = PLAFOND / FEUILLES.length;
      FEUILLES = FEUILLES.filter(function () { return R() < garde; });
    }
    FEUILLES.sort(function (a, b) { return a.b - b.b; });

    /* --- écorce : fissures du tronc et des grosses branches --- */
    FISSURES = {};
    A.c.forEach(function (ch, ic) {
      var r0 = A.n[ch.n[1] !== undefined ? ch.n[1] : ch.n[0]].r;
      if (r0 < 4) return;
      var nb = Math.min(13, Math.floor(r0 / 2.3));
      for (var j = 0; j < nb; j++) {
        var tirets = [];
        for (var k = 0; k < 6; k++) tirets.push(6 + 20 * R(), 3 + 9 * R());
        (FISSURES[ic] = FISSURES[ic] || []).push({ u: (j + .5) / nb * 1.7 - .85 + (R() - .5) * .12, tirets: tirets, dec: 30 * R(),
          l: .7 + .9 * R(), clair: R() < .3 });
      }
    });

    /* --- herbe et cailloux --- */
    HERBE = [];
    var foyers = [];
    for (i = 0; i < 16; i++) foyers.push(90 + R() * (W - 180));
    for (i = 0; i < 135; i++) {
      var x = foyers[Math.floor(R() * foyers.length)] + (R() - .5) * 90 * (1 + R());
      if (x < 70 || x > W - 70 || (Math.abs(x - CX) < 34 && R() < .7)) continue;
      var touffe = [], nb2 = 3 + Math.floor(R() * 7), h0 = (5 + 13 * R() * R()) * (R() < .08 ? 2 : 1);
      for (var j2 = 0; j2 < nb2; j2++) touffe.push({ dx: (R() - .5) * 8, h: h0 * (.6 + .6 * R()), pench: (R() - .5) * 1.2,
        c: ['#2c6e38', '#3b8d48', '#245a31', '#4ea457'][Math.floor(R() * 4)] });
      HERBE.push({ x: x, b: touffe });
    }
    CAILLOUX = [];
    for (i = 0; i < 70; i++) CAILLOUX.push({ x: 40 + R() * (W - 80), y: GY + 12 + R() * (H - GY - 70), rx: 1.5 + 5 * R() * R(),
      ry: 1 + 3 * R() * R(), a: R() * 3, c: ['#6e604f', '#857565', '#5d5043', '#4a4036'][Math.floor(R() * 4)] });

    /* --- dates d'apparition des liens --- */
    liens.forEach(function (L) {
      if (L.t === 'racine') L.rev = Rc.n[L.bout].t + .15;
      else if (L.t === 'branche') L.rev = A.n[L.bout].t + .2;
      else if (L.t === 'tronc') L.rev = 1.25;
      else if (L.t === 'sol') L.rev = 2.6;
      else if (L.t === 'deco') L.rev = 2.9;
    });
    var tF = 0; FEUILLES.forEach(function (f) { if (f.t > tF) tF = f.t; });
    FRUITS.forEach(function (F, k) { F.t = tF - .2 + .25 * k; F.lien.rev = F.t + .1; });
    T_FIN = tF + 2.8;                                  // le temps que les branches finissent d'épaissir
  }

  /* ---------- peinture ---------- */
  var s = 1, ctxH, ctxB, SPR = [], SPR_M, SOL, CUIT_F, CUIT_M, CUIT_A, cuitT = -1;
  var NC = 18, LW = 13, LH = 7;                     // feuilles : nuances, longueur, largeur
  var TEINTES = [[11, 51, 32], [20, 90, 51], [34, 131, 74], [63, 167, 90], [124, 201, 93], [185, 226, 122]];
  function teinte(x) {
    x = Math.max(0, Math.min(1, x)) * (TEINTES.length - 1);
    var i = Math.min(TEINTES.length - 2, Math.floor(x)), f = x - i, a = TEINTES[i], b = TEINTES[i + 1];
    return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * f) + ',' + Math.round(a[1] + (b[1] - a[1]) * f) + ',' + Math.round(a[2] + (b[2] - a[2]) * f) + ')';
  }
  function sprites() {
    SPR = [];
    for (var i = 0; i < NC; i++) {
      var pair = [];
      for (var f = 0; f < 2; f++) {
        var c = document.createElement('canvas'), k = s * 1.25;
        c.width = Math.ceil(LW * k) + 2; c.height = Math.ceil(LH * k) + 2;
        var g = c.getContext('2d'); g.scale(k, k); g.translate(.5, LH / 2 + .4);
        var w = LW, h = LH / 2 * (f ? .78 : 1);
        g.beginPath(); g.moveTo(0, 0);
        g.bezierCurveTo(w * .22, -h * 1.05, w * .72, -h * .95, w, 0);
        g.bezierCurveTo(w * .72, h * .95, w * .22, h * 1.05, 0, 0);
        g.fillStyle = teinte(i / (NC - 1)); g.fill();
        g.beginPath(); g.moveTo(0, 0);                 // moitié ombrée
        g.bezierCurveTo(w * .22, h * 1.05, w * .72, h * .95, w, 0); g.lineTo(0, 0);
        g.fillStyle = 'rgba(0,25,10,.22)'; g.fill();
        g.beginPath(); g.moveTo(.5, 0); g.lineTo(w * .92, 0);   // nervure
        g.strokeStyle = 'rgba(230,255,200,.28)'; g.lineWidth = .5; g.stroke();
        pair.push(c);
      }
      SPR.push(pair);
    }
    SPR_M = document.createElement('canvas'); SPR_M.width = SPR_M.height = 64;
    var gm = SPR_M.getContext('2d'), rg = gm.createRadialGradient(32, 32, 0, 32, 32, 32);
    rg.addColorStop(0, 'rgba(12,58,32,.8)'); rg.addColorStop(.6, 'rgba(14,62,35,.45)'); rg.addColorStop(1, 'rgba(14,62,35,0)');
    gm.fillStyle = rg; gm.fillRect(0, 0, 64, 64);
  }

  /* Sol : couches, cailloux, grains ; bords fondus. Peint une fois par taille d'écran. */
  function peindreSol() {
    SOL = document.createElement('canvas'); SOL.width = cvB.width; SOL.height = cvB.height;
    var g = SOL.getContext('2d'), R = hasard(GRAINE + 7), i;
    g.setTransform(s, 0, 0, s, 0, -BAS0 * s);
    var lg = g.createLinearGradient(0, GY, 0, H);
    lg.addColorStop(0, '#5e442a'); lg.addColorStop(.08, '#46321e'); lg.addColorStop(.5, '#2f2214'); lg.addColorStop(1, '#1b1209');
    g.fillStyle = lg;
    g.beginPath(); g.moveTo(0, H);
    for (i = 0; i <= 116; i++) { var x = i * 10; g.lineTo(x, GY - 1.5 + 1.6 * Math.sin(x * .05) + 1.1 * Math.sin(x * .13 + 1)); }
    g.lineTo(W, H); g.closePath(); g.fill();
    for (i = 0; i < 4; i++) {                          // strates
      var y0 = GY + 40 + i * 70 + 20 * R();
      g.beginPath(); g.moveTo(0, y0);
      for (var x2 = 0; x2 <= W; x2 += 20) g.lineTo(x2, y0 + 7 * Math.sin(x2 * .011 + i * 2));
      g.lineWidth = 10 + 12 * R(); g.strokeStyle = 'rgba(255,220,170,.035)'; g.stroke();
    }
    for (i = 0; i < 900; i++) {                        // grains
      g.fillStyle = R() < .5 ? 'rgba(10,6,2,.45)' : 'rgba(150,120,85,.18)';
      g.fillRect(R() * W, GY + 4 + R() * (H - GY), .8 + 1.4 * R(), .8 + 1.4 * R());
    }
    CAILLOUX.forEach(function (c) {
      g.save(); g.translate(c.x, c.y); g.rotate(c.a);
      g.beginPath(); g.ellipse(0, 0, c.rx, c.ry, 0, 0, 7); g.fillStyle = c.c; g.fill();
      g.beginPath(); g.ellipse(-c.rx * .3, -c.ry * .35, c.rx * .4, c.ry * .3, 0, 0, 7); g.fillStyle = 'rgba(255,240,220,.18)'; g.fill();
      g.restore();
    });
    g.globalCompositeOperation = 'destination-in';     // bords gauche, droit et bas fondus
    g.setTransform(s, 0, 0, s, 0, -BAS0 * s);
    var fx = g.createLinearGradient(0, 0, W, 0);
    fx.addColorStop(0, 'rgba(0,0,0,0)'); fx.addColorStop(.09, '#000'); fx.addColorStop(.91, '#000'); fx.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = fx; g.fillRect(0, BAS0, W, H - BAS0);
    var fy = g.createLinearGradient(0, H - 34, 0, H);
    fy.addColorStop(0, '#000'); fy.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = fy; g.fillRect(0, BAS0, W, H - BAS0);
  }

  /* Vide les couches cuites ; avec tout=true, y repeint d'un coup tout ce qui est déployé, dans
     l'ordre exact (du plus sombre au plus clair), ce qui sert à la fin et après un redimensionnement. */
  function cuire(tout, t) {
    if (!CUIT_F || CUIT_F.width !== cvH.width || CUIT_F.height !== cvH.height) {
      CUIT_F = document.createElement('canvas'); CUIT_M = document.createElement('canvas'); CUIT_A = document.createElement('canvas');
    }
    CUIT_F.width = CUIT_M.width = CUIT_A.width = cvH.width; CUIT_F.height = CUIT_M.height = CUIT_A.height = cvH.height;
    var i;
    for (i = 0; i < MASSES.length; i++) MASSES[i].cuit = false;
    for (i = 0; i < FEUILLES.length; i++) FEUILLES[i].cuit = false;
    for (i = 0; i < ARRIERE.length; i++) ARRIERE[i].cuit = false;
    cuitT = -1;
    if (!tout) return;
    var gm = CUIT_M.getContext('2d'), gf = CUIT_F.getContext('2d');
    gm.setTransform(s, 0, 0, s, 0, 0);
    for (i = 0; i < MASSES.length; i++) {
      var M = MASSES[i]; if (t - M.t < 1.2) continue;
      M.cuit = true; gm.drawImage(SPR_M, M.x - M.r, M.y - M.r, 2 * M.r, 2 * M.r);
    }
    [[ARRIERE, CUIT_A], [FEUILLES, CUIT_F]].forEach(function (c) {
      var L = c[0], gx = c[1].getContext('2d');
      for (var j = 0; j < L.length; j++) {
        var f = L[j]; if (t - f.t < 1.6) continue;
        f.cuit = true;
        var ix = Math.min(NC - 1, Math.round(f.b * (NC - 1)));
        gx.setTransform(s * f.c * f.e, s * f.s * f.e, -s * f.s * f.e, s * f.c * f.e, s * f.x, s * f.y);
        gx.drawImage(SPR[ix][f.f], 0, -LH / 2, LW, LH);
      }
    });
    cuitT = t;
  }

  /* Tracé d'une chaîne : polygone dont la demi-largeur suit le rayon des nœuds.
     dec : décalage latéral vers la lumière (en rayons) ; lf : facteur de largeur. */
  var PX = new Float32Array(4096), PY = new Float32Array(4096), PR = new Float32Array(4096);
  var NX = new Float32Array(4096), NY = new Float32Array(4096), OF = new Float32Array(4096);
  function rayonA(nd, t) { return nd.r * (.22 + .78 * lissee((t - nd.t) / 2.4)); }
  function recueillir(S, ch, t, depuis) {
    var m = 0, n = S.n, i;
    for (i = 0; i < ch.n.length; i++) {
      var a = n[ch.n[i]];
      if (a.t <= t) { PX[m] = a.x; PY[m] = a.y; PR[m] = rayonA(a, t); m++; continue; }
      if (i > 0) {                                     // nœud en train de naître : pointe interpolée
        var p = n[ch.n[i - 1]], f = (t - p.t) / (a.t - p.t);
        if (f > 0) { PX[m] = p.x + (a.x - p.x) * f; PY[m] = p.y + (a.y - p.y) * f; PR[m] = PR[m - 1] * .7; m++; }
      }
      break;
    }
    if (depuis) {                                      // ne garder que la fin (pousses de l'année)
      var k = 0; for (i = depuis; i < m; i++) { PX[k] = PX[i]; PY[k] = PY[i]; PR[k] = PR[i]; k++; } m = k;
    }
    return m;
  }
  function tracer(g, m, dec, lf) {
    if (m < 2) return false;
    var i, Lx = -.55, Ly = -.83;
    g.beginPath();
    for (i = 0; i < m; i++) {
      var a = i > 0 ? i - 1 : 0, b = i < m - 1 ? i + 1 : m - 1;
      var tx = PX[b] - PX[a], ty = PY[b] - PY[a], tl = Math.sqrt(tx * tx + ty * ty) || 1;
      var nx = -ty / tl, ny = tx / tl;
      NX[i] = nx; NY[i] = ny;
      var cote = Math.max(-1, Math.min(1, (nx * Lx + ny * Ly) * 4));
      OF[i] = dec * cote * PR[i];
    }
    for (i = 0; i < m; i++) g.lineTo(PX[i] + NX[i] * (OF[i] + PR[i] * lf), PY[i] + NY[i] * (OF[i] + PR[i] * lf));
    var e = m - 1, tx2 = PX[e] - PX[e - 1], ty2 = PY[e] - PY[e - 1], t2 = Math.sqrt(tx2 * tx2 + ty2 * ty2) || 1;
    g.lineTo(PX[e] + NX[e] * OF[e] + tx2 / t2 * PR[e] * lf * .8, PY[e] + NY[e] * OF[e] + ty2 / t2 * PR[e] * lf * .8);
    for (i = m - 1; i >= 0; i--) g.lineTo(PX[i] + NX[i] * (OF[i] - PR[i] * lf), PY[i] + NY[i] * (OF[i] - PR[i] * lf));
    g.closePath();
    return true;
  }
  /* Fissures de l'écorce, sur les m points recueillis de la chaîne (à partir du point d0 :
     on épargne la fourche, où la branche se fond dans le tronc). */
  function fissures(g, L, m, d0) {
    if (m - d0 < 3) return;
    for (var i = 0; i < L.length; i++) {
      var F = L[i];
      g.beginPath();
      for (var j = d0; j < m; j++) {
        var a = j > 0 ? j - 1 : 0, b = j < m - 1 ? j + 1 : m - 1;
        var tx = PX[b] - PX[a], ty = PY[b] - PY[a], tl = Math.sqrt(tx * tx + ty * ty) || 1;
        var w = F.u + .06 * Math.sin(j * .9 + F.dec);
        g.lineTo(PX[j] - ty / tl * PR[j] * w, PY[j] + tx / tl * PR[j] * w);
      }
      g.setLineDash(F.tirets); g.lineDashOffset = F.dec;
      g.lineWidth = F.l; g.strokeStyle = F.clair ? 'rgba(170,132,92,.3)' : 'rgba(20,11,4,.55)';
      g.stroke();
    }
    g.setLineDash([]);
  }
  var ECORCE = ['#4d3322', '#503524', '#5a3e2a', '#664934', '#735641'];
  /* Bois : les chaînes épaisses sont des polygones ombrés ; les fines, de loin les plus
     nombreuses, sont regroupées par épaisseur et tracées d'un seul trait par groupe. */
  var GROUPES = [.7, 1.1, 1.6, 2.3];
  function peindreBois(g, S, t, racine) {
    var i, o, ordre = S.ordre, fins = [[], [], [], []], jeunes = [[], [], [], []], tronc = null;
    for (o = 0; o < ordre.length; o++) {
      var ch = S.c[ordre[o]], b0 = S.n[ch.n[1] !== undefined ? ch.n[1] : ch.n[0]];
      if (b0.t > t) continue;
      if (b0.r < 1.25) {                               // chaîne fine : à grouper
        var gi = 0, ep = rayonA(b0, t) * 2;
        while (gi < 3 && ep > (GROUPES[gi] + GROUPES[gi + 1]) / 2) gi++;
        (!racine && t - S.n[ch.bout].t < 1.1 ? jeunes : fins)[gi].push(ch);
        continue;
      }
      var m = recueillir(S, ch, t, 0);
      if (!tracer(g, m, 0, 1)) continue;
      var r0 = PR[0];
      g.fillStyle = racine ? '#a9783f' : ECORCE[Math.min(4, ch.niv)];
      g.fill();
      if (!racine && ch.niv === 0) { tronc = ch; continue; }
      if (racine ? r0 > 2.2 : ch.niv === 0) { g.lineWidth = .8; g.strokeStyle = racine ? 'rgba(40,22,8,.5)' : 'rgba(22,12,5,.6)'; g.stroke(); }
      var d0 = 0;
      if (r0 > 2.4) {
        if (ch.niv && !racine) {                       // pas de modelé sur la fourche
          var rp = S.n[ch.n[0]].r * 1.25;
          while (d0 < m - 2 && Math.hypot(PX[d0] - PX[0], PY[d0] - PY[0]) < rp) d0++;
        }
        var m4 = d0 ? recueillir(S, ch, t, d0) : m;
        if (tracer(g, m4, .5, .45)) { g.fillStyle = racine ? 'rgba(45,25,8,.35)' : 'rgba(18,10,4,.42)'; g.fill(); }
        if (tracer(g, m4, -.42, .32)) { g.fillStyle = racine ? 'rgba(238,200,140,.42)' : 'rgba(176,136,94,.36)'; g.fill(); }
        if (d0) m = recueillir(S, ch, t, 0);
      }
      if (!racine && FISSURES[ordre[o]]) fissures(g, FISSURES[ordre[o]], m, Math.max(2, d0 || 0));
      if (!racine) {                                   // pousses de l'année : vertes
        var dep = -1;
        for (i = 1; i < m; i++) if (t - S.n[ch.n[Math.min(i, ch.n.length - 1)]].t < 1.1) { dep = i - 1; break; }
        if (dep >= 0 && m - dep >= 2) {
          var m2 = recueillir(S, ch, t, dep);
          if (tracer(g, m2, 0, 1.02)) { g.fillStyle = 'rgba(122,156,62,.85)'; g.fill(); }
        }
      }
    }
    g.lineCap = 'round'; g.lineJoin = 'round';
    for (var k = 0; k < 2; k++) {
      var lots = k ? jeunes : fins;
      for (i = 0; i < 4; i++) {
        if (!lots[i].length) continue;
        g.beginPath();
        for (o = 0; o < lots[i].length; o++) {
          var mm = recueillir(S, lots[i][o], t, 0);
          if (mm < 2) continue;
          g.moveTo(PX[0], PY[0]);
          for (var j = 1; j < mm; j++) g.lineTo(PX[j], PY[j]);
        }
        g.lineWidth = GROUPES[i];
        g.strokeStyle = k ? '#7f9e42' : racine ? '#b88d58' : '#6e523c';
        g.stroke();
      }
    }
    if (tronc) {
      var mt = recueillir(S, tronc, t, 0);
      if (tracer(g, mt, .5, .45)) { g.fillStyle = 'rgba(18,10,4,.42)'; g.fill(); }
      if (tracer(g, mt, -.42, .32)) { g.fillStyle = 'rgba(176,136,94,.36)'; g.fill(); }
      fissures(g, FISSURES[S.c.indexOf(tronc)] || [], mt, 0);
      tracer(g, mt, 0, 1);                             // contour, seulement sous la première fourche
      var lim = Math.min(mt, S.limite || mt);
      g.beginPath();
      for (i = 0; i < lim; i++) g.lineTo(PX[i] + NX[i] * PR[i], PY[i] + NY[i] * PR[i]);
      for (i = 0; i < lim; i++) g[i ? 'lineTo' : 'moveTo'](PX[i] - NX[i] * PR[i], PY[i] - NY[i] * PR[i]);
      g.lineWidth = .8; g.strokeStyle = 'rgba(22,12,5,.6)'; g.stroke();
    }
  }

  /* Feuilles d'une liste : celles qui se déploient sont peintes sur g, celles qui viennent de
     finir sont cuites dans leur couche (gc). */
  function feuilles(g, gc, L, t) {
    for (var i = 0; i < L.length; i++) {
      var f = L[i], age = t - f.t;
      if (f.cuit || age <= 0) continue;
      var dest = g;
      if (age >= 1.6) { f.cuit = true; dest = gc; }
      var sc = f.e * rebond(age / .75), jeune = 1 - lissee(age / 1.6);
      var ix = Math.min(NC - 1, Math.round(f.b * (NC - 1) + jeune * 4));
      dest.setTransform(s * f.c * sc, s * f.s * sc, -s * f.s * sc, s * f.c * sc, s * f.x, s * f.y);
      dest.drawImage(SPR[ix][f.f], 0, -LH / 2, LW, LH);
    }
  }

  function peindre(t) {
    var g = ctxB, i;
    /* sous terre */
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cvB.width, cvB.height);
    g.drawImage(SOL, 0, 0);
    g.setTransform(s, 0, 0, s, 0, -BAS0 * s);
    var pc = lissee(t / .8);                            // collet : naissance des racines sous le tronc
    if (pc > 0) {
      var rt = A.n[0].r * (.25 + .75 * lissee((t - A.n[0].t) / 2.4));
      g.save(); g.translate(CX, GY + 2); g.scale(1, .45);
      var cg = g.createRadialGradient(-rt * .3, -rt * .4, 0, 0, 0, rt * 1.05);
      cg.addColorStop(0, '#c99a5c'); cg.addColorStop(.7, '#a9783f'); cg.addColorStop(1, 'rgba(120,80,38,0)');
      g.fillStyle = cg; g.globalAlpha = pc; g.beginPath(); g.arc(0, 0, rt * 1.05, 0, 7); g.fill(); g.restore();
    }
    peindreBois(g, Rc, t, true);
    /* radicelles au bout des racines fines */
    g.strokeStyle = 'rgba(214,180,128,.45)'; g.lineWidth = .6; g.beginPath();
    for (i = 0; i < Rc.c.length; i++) {
      var ch = Rc.c[i]; if (ch.niv < 3) continue;
      var b = Rc.n[ch.bout]; if (t - b.t < .4) continue;
      for (var k = 0; k < 3; k++) { var an = (b.x * 7 + k * 2.1) % 6.28; g.moveTo(b.x, b.y); g.lineTo(b.x + Math.cos(an) * 6, b.y + Math.abs(Math.sin(an)) * 6); }
    }
    g.stroke();

    /* au-dessus du sol */
    g = ctxH;
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cvH.width, cvH.height);
    g.setTransform(s, 0, 0, s, 0, 0);
    var pf = lissee((t - 4.2) / 2.5);                   // progression du feuillage
    if (pf > 0) {                                      // ombre portée au pied
      g.save(); g.translate(CX + 30, GY + 1); g.scale(1, .035);
      var og = g.createRadialGradient(0, 0, 0, 0, 0, 380);
      og.addColorStop(0, 'rgba(0,0,0,' + (.42 * pf) + ')'); og.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = og; g.fillRect(-380, -380, 760, 760); g.restore();
    }
    if (t < cuitT) cuire(false);
    cuitT = t;
    g.setTransform(1, 0, 0, 1, 0, 0); g.drawImage(CUIT_A, 0, 0);
    feuilles(g, CUIT_A.getContext('2d'), ARRIERE, t);
    g.setTransform(s, 0, 0, s, 0, 0);
    peindreBois(g, A, t, false);
    for (i = 0; i < FRUITS.length; i++) {              // pédoncules des fruits
      var F = FRUITS[i], nb = A.n[F.bout];
      if (t < F.t - .3) continue;
      g.beginPath(); g.moveTo(nb.x, nb.y); g.quadraticCurveTo(nb.x + 4, F.y - 18, F.x, F.y - 13);
      g.strokeStyle = '#4a3018'; g.lineWidth = 2; g.stroke();
    }
    /* Masses d'ombre et feuilles. Une feuille tout à fait déployée ne change plus : elle est
       « cuite » une fois pour toutes dans une couche à part, qu'on recopie à chaque image. */
    var gm = CUIT_M.getContext('2d'), gf = CUIT_F.getContext('2d');
    gm.setTransform(s, 0, 0, s, 0, 0);
    for (i = 0; i < MASSES.length; i++) {
      var M = MASSES[i], am = t - M.t; if (M.cuit || am <= 0) continue;
      if (am >= 1.2) { M.cuit = true; gm.drawImage(SPR_M, M.x - M.r, M.y - M.r, 2 * M.r, 2 * M.r); continue; }
      var e = M.r * lissee(am / 1.2);
      g.drawImage(SPR_M, M.x - e, M.y - e, 2 * e, 2 * e);
    }
    g.setTransform(1, 0, 0, 1, 0, 0); g.drawImage(CUIT_M, 0, 0); g.drawImage(CUIT_F, 0, 0);
    feuilles(g, gf, FEUILLES, t);
    /* herbe */
    g.setTransform(s, 0, 0, s, 0, 0);
    var ph = lissee((t - .9) / 2.2);
    if (ph > 0) {
      for (i = 0; i < HERBE.length; i++) {
        var T2 = HERBE[i];
        for (var j = 0; j < T2.b.length; j++) {
          var bl = T2.b[j], x = T2.x + bl.dx, h = bl.h * ph;
          g.beginPath(); g.moveTo(x - 1.1, GY + 1);
          g.quadraticCurveTo(x + bl.pench * h * .2, GY - h * .6, x + bl.pench * h * .55, GY - h);
          g.quadraticCurveTo(x + bl.pench * h * .2 + 1, GY - h * .55, x + 1.1, GY + 1);
          g.fillStyle = bl.c; g.fill();
        }
      }
    }
  }

  /* ---------- liens : apparition, légende, clavier ---------- */
  function majLiens(t) {
    for (var i = 0; i < liens.length; i++) if (t >= liens[i].rev) liens[i].el.classList.add('on');
  }
  var petit = false, arme = null;
  function legende(a) { if (cap) cap.textContent = '→ ' + a.getAttribute('data-p'); }
  nds.forEach(function (a) {
    a.addEventListener('mouseenter', function () { legende(a); });
    a.addEventListener('focus', function () { legende(a); a.classList.add('on'); });
    a.addEventListener('click', function (e) {          // sur écran tactile étroit : 1er toucher = nom, 2e = ouverture
      if (!petit || !window.matchMedia('(hover: none)').matches || arme === a) return;
      e.preventDefault();
      if (arme) arme.classList.remove('arme');
      arme = a; a.classList.add('arme');
      if (cap) {
        cap.textContent = '→ ' + a.getAttribute('data-p') + ' ';
        var o = document.createElement('a'); o.href = a.getAttribute('href'); o.textContent = 'Ouvrir';
        o.className = 'ab-ouvrir'; cap.appendChild(o);
      }
    });
  });

  /* ---------- dimensions, animation ---------- */
  var t0 = 0, raf = 0, tCourant = 1e9;
  function dimensionner() {
    var lw = stage.clientWidth || W, dpr = Math.min(2, window.devicePixelRatio || 1);
    petit = lw < 860;
    stage.classList.toggle('ab-petit', petit);
    stage.style.setProperty('--u', (lw / W).toFixed(4));
    var pw = Math.round(lw * dpr);
    s = pw / W;
    cvH.width = pw; cvH.height = Math.round(HAUT * s);
    cvB.width = pw; cvB.height = Math.round((H - BAS0) * s);
    ctxH = cvH.getContext('2d'); ctxB = cvB.getContext('2d');
    sprites(); peindreSol(); cuire(false);
  }
  function image(now) {
    var t = (now - t0) / 1000;
    tCourant = t;
    peindre(t); majLiens(t);
    if (t < T_FIN) raf = requestAnimationFrame(image);
    else { tCourant = 1e9; cuire(true, 1e9); peindre(1e9); majLiens(1e9); hero.classList.add('ab-fini'); }
  }
  function lancer() {
    cancelAnimationFrame(raf);
    hero.classList.remove('ab-fini');
    liens.forEach(function (L) { L.el.classList.remove('on'); });
    if (calme) { tCourant = 1e9; cuire(true, 1e9); peindre(1e9); majLiens(1e9); hero.classList.add('ab-fini'); return; }
    cuire(false); t0 = performance.now(); raf = requestAnimationFrame(image);
  }
  window.abReplay = lancer;

  construire(GRAINE);
  [A, Rc].forEach(function (S) {                       // ordre de peinture : du plus épais au plus fin
    S.ordre = S.c.map(function (c, i) { return i; }).sort(function (a, b) { return S.c[a].niv - S.c[b].niv || a - b; });
  });
  dimensionner();
  var attente = 0;
  window.addEventListener('resize', function () {
    clearTimeout(attente);
    attente = setTimeout(function () {
      if (Math.abs(stage.clientWidth * Math.min(2, window.devicePixelRatio || 1) - cvH.width) < 2) return;
      dimensionner(); cuire(true, tCourant); peindre(tCourant);
    }, 150);
  });
  if (/[?&]debogage/.test(location.search)) window.abArbre = { stop: function () { cancelAnimationFrame(raf); }, A: function () { return A; }, Rc: function () { return Rc; }, F: function () { return FEUILLES; }, feuilles: function () { return FEUILLES.length; }, noeuds: function () { return A.n.length + Rc.n.length; },
    chaines: function () { return A.c.length + Rc.c.length; }, peindre: function (t) { peindre(t); majLiens(t); }, cuire: function (t) { cuire(true, t); }, fin: function () { return T_FIN; } };
  lancer();
})();
