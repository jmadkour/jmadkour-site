/* Arbre 3D de l'accueil de jmadkour.org (WebGL, Three.js).

   Même principe que l'arbre 2D (assets/arbre.js), en volume :
   - un squelette procédural (graine fixe) : ramification selon l'angle d'or (phyllotaxie),
     angle d'insertion de 40 à 55°, phototropisme, gravitropisme des racines, modèle des tuyaux
     de Léonard pour l'affinement, empattement du tronc, racine pivot ;
   - le bois est un ensemble de tubes ; les feuilles, environ 10 000 copies d'une même feuille
     pliée le long de sa nervure ; l'herbe, des brins qui ondulent ;
   - la croissance (racines, tronc, branches, feuilles qui se déploient, pousses vertes) et le vent
     sont calculés par la carte graphique, à partir de la date de naissance de chaque point ;
   - la terre est un bloc vu en coupe : sa face avant est une fenêtre (tampon de stencil) à
     travers laquelle on voit les racines ;
   - les liens sont les <a> du HTML de la page (data-x, data-y dans le repère 1160 × 940 de
     l'arbre 2D) : on les replace à chaque image en projetant leur point d'ancrage.

   Source lisible ; le fichier publié (assets/arbre3d.js) en est la version regroupée avec la
   partie de Three.js utilisée (licence MIT), produite par :
       npm install three@0.170.0 esbuild@0.24.0
       npx esbuild arbre3d-source.js --bundle --format=esm --minify --legal-comments=inline --outfile=arbre3d.js */
import {
  WebGLRenderer, Scene, PerspectiveCamera, Group, BufferGeometry, BufferAttribute, InstancedMesh,
  InstancedBufferAttribute, Mesh, MeshLambertMaterial, MeshBasicMaterial, HemisphereLight, DirectionalLight,
  PlaneGeometry, CanvasTexture, Color, Matrix4, Vector3, DoubleSide, RepeatWrapping, SRGBColorSpace,
  AlwaysStencilFunc, EqualStencilFunc, ReplaceStencilOp, KeepStencilOp
} from 'three';

const W = 1160, H = 940, GY = 570;
const CY = 322, RX = 392, RY = 205, RZ = 290;        // houppier : ellipsoïde (y vers le haut, sol en y = 0)
const BLOC = { x: 545, z: 330, h: 312 };             // bloc de terre vu en coupe
const ZB = RZ * .42, ZF = RZ * .5, ZR = 150;         // profondeur des ancrages : branches, fruits, racines

/* ---------- outils ---------- */
function hasard(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
const lissee = (x) => { x = x < 0 ? 0 : x > 1 ? 1 : x; return x * x * (3 - 2 * x); };
const lin = (hex) => { const c = new Color(hex); return [c.r, c.g, c.b]; };   // sRVB → linéaire

/* Écarte la direction d d'un angle an, dans le plan repéré par l'azimut phi autour de d. */
function deviation(d, an, phi) {
  let ux, uy, uz;
  if (Math.abs(d[1]) < .9) { ux = -d[2]; uy = 0; uz = d[0]; } else { ux = 0; uy = d[2]; uz = -d[1]; }
  let m = Math.hypot(ux, uy, uz); ux /= m; uy /= m; uz /= m;
  const vx = d[1] * uz - d[2] * uy, vy = d[2] * ux - d[0] * uz, vz = d[0] * uy - d[1] * ux;
  const c = Math.cos(phi), s = Math.sin(phi), px = ux * c + vx * s, py = uy * c + vy * s, pz = uz * c + vz * s;
  const ca = Math.cos(an), sa = Math.sin(an);
  return [d[0] * ca + px * sa, d[1] * ca + py * sa, d[2] * ca + pz * sa];
}

/* ---------- squelette ---------- */
class Squelette {
  constructor(R) { this.R = R; this.n = []; this.c = []; }
  noeud(x, y, z, p, l) {
    const i = this.n.length;
    this.n.push({ x, y, z, p, l, k: [], r: 0, t: 0 });
    if (p >= 0) this.n[p].k.push(i);
    return i;
  }
  pousse(o) {
    const R = this.R, P = o.regles[o.niv], ch = { n: [o.de], niv: o.niv };
    this.c.push(ch);
    const p = this.n[o.de];
    let x = p.x, y = p.y, z = p.z, dx = o.d[0], dy = o.d[1], dz = o.d[2], fait = 0, prec = o.de;
    let phi = R() * 6.283, prochain = P.esp * (.45 + .6 * R()), essais = 0;
    let entre = !o.dedans || o.dedans(x, y, z);
    while (fait < o.lon) {
      dx += (R() - .5) * P.cou; dy += (R() - .5) * P.cou; dz += (R() - .5) * P.cou;
      dy += P.tro;                                     // > 0 : vers la lumière ; < 0 : vers le bas
      if (o.vise) {
        const vx = o.vise.x - x, vy = o.vise.y - y, vz = o.vise.z - z, d = Math.hypot(vx, vy, vz);
        if (d < P.pas * 1.2) break;
        const kv = o.vise.k0 + (o.vise.k1 - o.vise.k0) * Math.min(1, fait / o.lon);
        dx += vx / d * kv; dy += vy / d * kv; dz += vz / d * kv;
      }
      const m = Math.hypot(dx, dy, dz); dx /= m; dy /= m; dz /= m;
      const nx = x + dx * P.pas, ny = y + dy * P.pas, nz = z + dz * P.pas;
      if (o.dedans && !entre && o.dedans(nx, ny, nz)) entre = true;
      if (o.dedans && entre && !o.dedans(nx, ny, nz)) {
        if (o.vise || ++essais > 3) break;
        const ix = o.centre[0] - x, iy = o.centre[1] - y, iz = o.centre[2] - z, im = Math.hypot(ix, iy, iz) || 1;
        dx += ix / im * .7; dy += iy / im * .7; dz += iz / im * .7;
        continue;
      }
      x = nx; y = ny; z = nz; fait += P.pas;
      const i = this.noeud(x, y, z, prec, o.niv); ch.n.push(i); prec = i;
      if (o.niv < o.max && fait >= prochain) {
        const lc = o.lon * P.lf * (.7 + .55 * R()) * (1 - .5 * fait / o.lon);
        if (lc > P.min && R() < P.prob) {
          phi += 2.39996 + (R() - .5) * .5;            // angle d'or
          this.pousse({ de: i, d: deviation([dx, dy, dz], P.ang * (.75 + .5 * R()), phi), lon: lc, niv: o.niv + 1,
            regles: o.regles, dedans: o.dedans, centre: o.centre, max: o.max });
        }
        prochain += P.esp * (.7 + .6 * R());
      }
    }
    ch.bout = prec;
    return ch;
  }
  rayons(rBout, expo, effile, rBase, rMin) {
    const n = this.n;
    for (let i = n.length - 1; i >= 0; i--) {
      const a = n[i];
      if (!a.k.length) { a.r = rBout; continue; }
      let s = 0;
      for (const j of a.k) { const b = n[j]; s += Math.pow(b.r + effile * Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z), expo); }
      a.r = Math.pow(s, 1 / expo);
    }
    const f = rBase / n[0].r;
    for (const a of n) a.r = Math.max(rMin, a.r * f);
  }
  naissances(vit, attente, t0, t1) {
    const n = this.n, R = this.R; let max = 0;
    n[0].t = 0;
    for (let i = 1; i < n.length; i++) {
      const a = n[i], p = n[a.p];
      a.t = p.t + Math.hypot(a.x - p.x, a.y - p.y, a.z - p.z) / vit[a.l] + (a.l !== p.l ? attente * (.4 + R()) : 0);
      if (a.t > max) max = a.t;
    }
    for (const a of n) a.t = t0 + (t1 - t0) * a.t / max;
  }
}

const REG_H = [
  { pas: 8, cou: .045, tro: 0, esp: 0, ang: 0, lf: 0, min: 0, prob: 0 },
  { pas: 8, cou: .08, tro: .004, esp: 27, ang: .8, lf: .56, min: 22, prob: .95 },
  { pas: 6.5, cou: .14, tro: .016, esp: 23, ang: .86, lf: .6, min: 14, prob: .85 },
  { pas: 5.5, cou: .2, tro: .022, esp: 18, ang: .92, lf: .55, min: 9, prob: .72 },
  { pas: 5, cou: .24, tro: .026, esp: 99, ang: 1, lf: .5, min: 99, prob: 0 }
];
const REG_B = [
  null,
  { pas: 7, cou: .13, tro: -.006, esp: 34, ang: .72, lf: .5, min: 18, prob: .8 },
  { pas: 5.5, cou: .2, tro: -.016, esp: 30, ang: .85, lf: .45, min: 12, prob: .5 },
  { pas: 4.5, cou: .26, tro: -.02, esp: 99, ang: 1, lf: .5, min: 99, prob: 0 }
];
function dansHouppier(x, y, z) {
  const u = x / RX, v = (y - CY) / RY, w = z / RZ;
  const th = Math.atan2(u, v), ph = Math.atan2(w, u);
  const lobe = 1 + .06 * Math.sin(3 * th + 1.3) + .045 * Math.sin(5 * th + .4) + .04 * Math.sin(4 * ph + .7);
  return u * u + v * v + w * w <= lobe * lobe && y > 72;
}
const dansSol = (x, y, z) => Math.abs(x) < BLOC.x - 25 && y < -4 && y > -BLOC.h + 70 && Math.abs(z) < BLOC.z - 12;

/* ---------- construction ---------- */
function construire(graine, liens) {
  const R = hasard(graine), de = (t) => liens.filter((L) => L.t === t);
  const A = new Squelette(R);
  A.noeud(0, 0, 0, -1, 0);
  const tronc = A.pousse({ de: 0, d: [0, 1, 0], lon: 178, niv: 0, regles: REG_H, max: 0,
    vise: { x: 6, y: 178, z: -4, k0: .02, k1: .05 } });
  const cibles = de('branche').map((L) => ({ x: L.x3, y: L.y3, z: ZB, lien: L }));
  const N = 24;                                         // autres charpentières : points répartis sur l'ellipsoïde
  for (let i = 0; i < N; i++) {
    const v = 1 - 2 * (i + .5) / N, rr = Math.sqrt(1 - v * v), th = i * 2.39996;
    if (v < -.45) continue;
    const f = .62 + .24 * R(), c = { x: Math.cos(th) * rr * RX * f, y: CY + v * RY * f, z: Math.sin(th) * rr * RZ * f };
    if (cibles.some((b) => Math.hypot(b.x - c.x, b.y - c.y, b.z - c.z) < 115)) continue;
    cibles.push(c);
  }
  cibles.sort((a, b) => b.y - a.y);
  for (const c of cibles) {
    const h = 108 + 70 * lissee((c.y - (CY - RY * .35)) / (RY * 1.25));
    const k = Math.min(tronc.n.length - 1, Math.round(h / REG_H[0].pas));
    A.limite = Math.min(A.limite || 99, k - 1);
    const s = A.n[tronc.n[k]], vx = c.x - s.x, vy = c.y - s.y + 60, vz = c.z - s.z, d = Math.hypot(vx, vy, vz);
    const ch = A.pousse({ de: tronc.n[k], d: [vx / d, vy / d, vz / d], lon: Math.hypot(c.x - s.x, c.y - s.y, c.z - s.z) * 1.3,
      niv: 1, regles: REG_H, max: 4, dedans: dansHouppier, centre: [0, CY - 40, 0], vise: { x: c.x, y: c.y, z: c.z, k0: .03, k1: .16 } });
    if (c.lien) c.lien.bout = ch.bout;
    for (let j = 0; j < 3; j++) {                       // quelques rameaux autour du bout de la charpentière
      A.pousse({ de: ch.bout, d: deviation([0, 1, 0], .6 + .5 * R(), j * 2.1 + R()), lon: 30 + 25 * R(), niv: 3,
        regles: REG_H, max: 4, dedans: dansHouppier, centre: [0, CY, 0] });
    }
  }
  const fruits = de('fruit').map((L) => {
    const ax = L.x3, ay = L.y3 + 18, az = ZF;
    let best = -1, bd = 1e9;
    for (let j = 0; j < A.n.length; j++) {
      const nd = A.n[j]; if (nd.l < 2 || nd.y < ay + 6) continue;
      const d = Math.hypot(nd.x - ax, nd.y - ay, nd.z - az); if (d < bd) { bd = d; best = j; }
    }
    const s = A.n[best], ch = A.pousse({ de: best, d: [(ax - s.x) / bd, (ay - s.y) / bd, (az - s.z) / bd], lon: bd * 1.5, niv: 3,
      regles: REG_H, max: 3, vise: { x: ax, y: ay, z: az, k0: .2, k1: .4 } });
    L.bout = ch.bout;
    return { lien: L, bout: ch.bout, x: ax, y: L.y3, z: az };
  });
  A.rayons(.55, 2.3, .011, 25, .5);
  for (const i of tronc.n) { const nt = A.n[i]; nt.r *= 1 + .8 * Math.exp(-nt.y / 16); }
  A.naissances([150, 120, 105, 90, 75], .35, .7, 5.6);

  /* racines */
  const Rc = new Squelette(R);
  Rc.noeud(0, -1, 0, -1, 0);
  const visees = de('racine').map((L) => ({ x: L.x3, y: L.y3 + 22, z: ZR, lien: L }));
  for (let i = 0; i < 7; i++) visees.push({ az: i * 2.39996 + .8, pente: i % 3 === 2 ? 1.15 : .15 + .35 * R() });
  for (const v of visees) {
    const pivot = v.lien && Math.abs(v.x) < 40;
    let o = { niv: 1, regles: REG_B, max: 3, dedans: dansSol, centre: [0, -120, 0] };
    if (v.lien) {
      const ex = pivot ? 0 : Math.sign(v.x) * (5 + 16 * R());
      o.de = Rc.noeud(ex, -3 - 3 * R(), 4 * R(), 0, 1);
      const vx = v.x - ex, vy = v.y, vz = v.z, d = Math.hypot(vx, vy, vz);
      o.d = pivot ? [0, -1, .05] : [vx / d + Math.sign(vx) * .5, vy / d * .4 - .25, vz / d];
      const m = Math.hypot(...o.d); o.d = o.d.map((q) => q / m);
      o.lon = d * 1.9; o.vise = { x: v.x, y: v.y, z: v.z, k0: .03, k1: .28 };
      v.lien.bout = Rc.pousse(o).bout;
    } else {
      const cx = Math.cos(v.az), cz = Math.sin(v.az);
      o.de = Rc.noeud(cx * (6 + 14 * R()), -3 - 3 * R(), cz * (6 + 14 * R()), 0, 1);
      o.d = [cx * Math.cos(v.pente), -Math.sin(v.pente), cz * Math.cos(v.pente)];
      o.lon = v.pente > 1 ? 120 + 60 * R() : 210 + 140 * R();
      Rc.pousse(o);
    }
  }
  Rc.rayons(.45, 2.3, .016, 21, .4);
  Rc.naissances([1, 120, 100, 80], .25, 0, 2.6);

  /* feuilles */
  const feuilles = [];
  const sun = [-.5, .72, .48];
  for (const nd of A.n) {
    if (nd.l < 3 || nd.r > 2.2) continue;
    const bout = !nd.k.length, nb = bout ? 6 + Math.floor(R() * 4) : (R() < .6 ? 1 + Math.floor(R() * 2) : 0);
    for (let j = 0; j < nb; j++) {
      const x = nd.x + (R() - .5) * 12, y = nd.y + (R() - .5) * 12, z = nd.z + (R() - .5) * 12;
      const u = x / RX, v = (y - CY) / RY, w = z / RZ, rho = Math.min(1.15, Math.hypot(u, v, w)) || .01;
      const lum = .28 + .36 * rho + .3 * (u * sun[0] + v * sun[1] + w * sun[2]) / rho * Math.sqrt(rho) + (R() - .5) * .26;
      let o = [u + (R() - .5) * 1.4, v + (R() - .5) * 1.4 - .35, w + (R() - .5) * 1.4];
      const mo = Math.hypot(...o) || 1; o = o.map((q) => q / mo);
      feuilles.push({ x, y, z, d: o, e: .75 + .45 * R(), b: Math.max(0, Math.min(1, lum)), t: nd.t + .3 + .6 * R(), ph: R() * 6.28 });
    }
  }
  const PLAFOND = 17000;
  const garde = Math.min(1, PLAFOND / feuilles.length);
  const F = garde < 1 ? feuilles.filter(() => R() < garde) : feuilles;

  /* dates d'apparition des liens */
  let tF = 0; for (const f of F) if (f.t > tF) tF = f.t;
  for (const L of liens) {
    if (L.t === 'racine') L.rev = Rc.n[L.bout].t + .15;
    else if (L.t === 'branche') L.rev = A.n[L.bout].t + .2;
    else if (L.t === 'tronc') L.rev = 1.25;
    else if (L.t === 'sol') L.rev = 2.6;
    else if (L.t === 'deco') L.rev = 2.9;
  }
  fruits.forEach((f, k) => { f.t = tF - .2 + .25 * k; f.lien.rev = f.t + .1; });
  return { A, Rc, F, fruits, fin: tF + 2.8, tronc };
}

/* ---------- textures peintes ---------- */
function toile(w, h, peindre) { const c = document.createElement('canvas'); c.width = w; c.height = h; peindre(c.getContext('2d'), w, h); return c; }
function texEcorce() {
  const c = toile(256, 256, (g, w, h) => {
    g.fillStyle = '#b8b0a6'; g.fillRect(0, 0, w, h);
    const R = hasard(5);
    for (let i = 0; i < 46; i++) {                     // fissures verticales, raccordées en haut et en bas
      let x = R() * w; g.beginPath(); g.moveTo(x, -10);
      for (let y = 0; y <= h + 10; y += 16) { x += (R() - .5) * 7; g.lineTo(x, y); }
      g.lineWidth = 1.5 + 3.5 * R(); g.strokeStyle = `rgba(40,30,22,${.25 + .4 * R()})`; g.stroke();
    }
    for (let i = 0; i < 500; i++) { g.fillStyle = R() < .5 ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.1)'; g.fillRect(R() * w, R() * h, 2 + 4 * R(), 1 + 6 * R()); }
  });
  const t = new CanvasTexture(c); t.wrapS = t.wrapT = RepeatWrapping; t.colorSpace = SRGBColorSpace; return t;
}
function texCoupe() {                                  // face avant du bloc de terre
  const c = toile(1090, 380, (g, w, h) => {
    const R = hasard(7);
    const lg = g.createLinearGradient(0, 0, 0, h);
    lg.addColorStop(0, '#5e442a'); lg.addColorStop(.06, '#46321e'); lg.addColorStop(.5, '#2f2214'); lg.addColorStop(1, '#1b1209');
    g.fillStyle = lg; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 4; i++) {
      const y0 = 40 + i * 75 + 20 * R(); g.beginPath(); g.moveTo(0, y0);
      for (let x = 0; x <= w; x += 20) g.lineTo(x, y0 + 7 * Math.sin(x * .011 + i * 2));
      g.lineWidth = 10 + 12 * R(); g.strokeStyle = 'rgba(255,220,170,.04)'; g.stroke();
    }
    for (let i = 0; i < 1400; i++) { g.fillStyle = R() < .5 ? 'rgba(10,6,2,.45)' : 'rgba(150,120,85,.18)'; g.fillRect(R() * w, R() * h, .8 + 1.6 * R(), .8 + 1.6 * R()); }
    for (let i = 0; i < 80; i++) {
      const x = R() * w, y = 10 + R() * (h - 20), rx = 1.5 + 6 * R() * R(), ry = 1 + 3.5 * R() * R();
      g.save(); g.translate(x, y); g.rotate(R() * 3);
      g.beginPath(); g.ellipse(0, 0, rx, ry, 0, 0, 7); g.fillStyle = ['#6e604f', '#857565', '#5d5043', '#4a4036'][Math.floor(R() * 4)]; g.fill();
      g.beginPath(); g.ellipse(-rx * .3, -ry * .35, rx * .4, ry * .3, 0, 0, 7); g.fillStyle = 'rgba(255,240,220,.18)'; g.fill();
      g.restore();
    }
    const bord = g.createLinearGradient(0, 0, 0, 10); bord.addColorStop(0, 'rgba(110,85,55,.9)'); bord.addColorStop(1, 'rgba(110,85,55,0)');
    g.fillStyle = bord; g.fillRect(0, 0, w, 10);
  });
  const t = new CanvasTexture(c); t.colorSpace = SRGBColorSpace; return t;
}
function texDessus() {                                 // dessus du bloc : terre et mousse
  const c = toile(512, 320, (g, w, h) => {
    const R = hasard(9);
    g.fillStyle = '#4a3a22'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 2600; i++) {
      const v = R(); g.fillStyle = v < .55 ? `rgba(${40 + 40 * R()},${90 + 60 * R()},${40 + 30 * R()},.55)` : v < .8 ? 'rgba(90,70,40,.5)' : 'rgba(20,14,6,.4)';
      g.beginPath(); g.arc(R() * w, R() * h, 1 + 4 * R(), 0, 7); g.fill();
    }
    const om = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w * .32);
    om.addColorStop(0, 'rgba(0,0,0,.45)'); om.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = om; g.fillRect(0, 0, w, h);           // ombre portée du houppier
  });
  const t = new CanvasTexture(c); t.colorSpace = SRGBColorSpace; return t;
}

/* ---------- maillages ---------- */
const DECL = `
attribute vec3 aCentre; attribute vec3 aPrec; attribute float aNaiss; attribute float aNaissPrec;
uniform float uT; uniform float uTemps; uniform float uVent; varying float vAge;
vec3 vent(vec3 p) { float h = max(p.y, 0.0) / 520.0; h *= h;
  return uVent * h * vec3(sin(uTemps * .9 + p.y * .004 + p.z * .002) * 7.0, 0.0, cos(uTemps * .7 + p.x * .003) * 5.0); }`;
function croissance(mat, U, jeune, stencil) {
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\n' + DECL)
      .replace('#include <begin_vertex>', `
        float age = uT - aNaiss; vec3 ctr; float ech;
        if (age >= 0.0) { ctr = aCentre; ech = 0.22 + 0.78 * smoothstep(0.0, 1.0, age / 2.4); }
        else { float f = clamp((uT - aNaissPrec) / max(aNaiss - aNaissPrec, 1e-4), 0.0, 1.0); ctr = mix(aPrec, aCentre, f); ech = 0.0; }
        vec3 transformed = ctr + (position - aCentre) * ech; vAge = age;`)
      .replace('#include <project_vertex>', `
        vec4 mvPosition = vec4(transformed, 1.0); mvPosition.xyz += vent(mvPosition.xyz);
        mvPosition = modelViewMatrix * mvPosition; gl_Position = projectionMatrix * mvPosition;`);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vAge;')
      .replace('#include <color_fragment>', `#include <color_fragment>
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(.16, .26, .04), (1.0 - smoothstep(0.0, 1.1, vAge)) * ${jeune.toFixed(2)});`);
  };
  // Three.js réutilise un programme dont la clé est identique : sans cette clé, le bois et les racines
  // (même fonction, réglages différents) partageraient le même shader.
  mat.customProgramCacheKey = () => 'croissance-' + jeune + (stencil ? '-coupe' : '');
  if (stencil) {                                        // racines : visibles seulement dans la fenêtre de coupe
    mat.stencilWrite = true; mat.stencilRef = 1; mat.stencilFunc = EqualStencilFunc;
    mat.stencilFail = mat.stencilZFail = mat.stencilZPass = KeepStencilOp;
  }
  return mat;
}
/* Tubes d'un squelette : un anneau par nœud, repère transporté le long de la chaîne. */
function tubes(S, couleur, ecorce) {
  const P = [], Nm = [], C = [], UV = [], Ce = [], Pr = [], Na = [], Np = [], I = [];
  let base = 0;
  for (const ch of S.c) {
    const m = ch.n.length; if (m < 2) continue;
    const r1 = S.n[ch.n[1]].r, cotes = r1 > 6 ? 12 : r1 > 2.5 ? 8 : r1 > 1.2 ? 5 : 3;
    const col = lin(couleur(ch)); let ux = 0, uy = 0, uz = 0, long = 0;
    for (let k = 0; k < m; k++) {
      const a = S.n[ch.n[k]], pa = S.n[ch.n[Math.max(0, k - 1)]], na = S.n[ch.n[Math.min(m - 1, k + 1)]];
      let tx = na.x - pa.x, ty = na.y - pa.y, tz = na.z - pa.z; const tl = Math.hypot(tx, ty, tz) || 1; tx /= tl; ty /= tl; tz /= tl;
      if (k === 0) { if (Math.abs(ty) < .9) { ux = -tz; uy = 0; uz = tx; } else { ux = 0; uy = tz; uz = -ty; } }
      const dp = ux * tx + uy * ty + uz * tz; ux -= tx * dp; uy -= ty * dp; uz -= tz * dp;
      const um = Math.hypot(ux, uy, uz) || 1; ux /= um; uy /= um; uz /= um;
      const vx = ty * uz - tz * uy, vy = tz * ux - tx * uz, vz = tx * uy - ty * ux;
      const r = k === 0 ? r1 : a.r, prev = k === 0 ? a : pa;
      if (k > 0) long += Math.hypot(a.x - pa.x, a.y - pa.y, a.z - pa.z);
      for (let s = 0; s <= cotes; s++) {
        const an = s / cotes * 6.2832, c = Math.cos(an), sn = Math.sin(an);
        const nx = ux * c + vx * sn, ny = uy * c + vy * sn, nz = uz * c + vz * sn;
        P.push(a.x + nx * r, a.y + ny * r, a.z + nz * r); Nm.push(nx, ny, nz); C.push(...col);
        UV.push(s / cotes * Math.max(1, Math.round(r / 3)), long / (ecorce ? 26 : 40));
        Ce.push(a.x, a.y, a.z); Pr.push(prev.x, prev.y, prev.z); Na.push(a.t); Np.push(prev.t);
      }
      if (k > 0) {
        const r0 = base + (k - 1) * (cotes + 1), r1b = base + k * (cotes + 1);
        for (let s = 0; s < cotes; s++) I.push(r0 + s, r1b + s, r0 + s + 1, r0 + s + 1, r1b + s, r1b + s + 1);
      }
    }
    base += m * (cotes + 1);
  }
  const g = new BufferGeometry();
  g.setAttribute('position', new BufferAttribute(new Float32Array(P), 3));
  g.setAttribute('normal', new BufferAttribute(new Float32Array(Nm), 3));
  g.setAttribute('color', new BufferAttribute(new Float32Array(C), 3));
  g.setAttribute('uv', new BufferAttribute(new Float32Array(UV), 2));
  g.setAttribute('aCentre', new BufferAttribute(new Float32Array(Ce), 3));
  g.setAttribute('aPrec', new BufferAttribute(new Float32Array(Pr), 3));
  g.setAttribute('aNaiss', new BufferAttribute(new Float32Array(Na), 1));
  g.setAttribute('aNaissPrec', new BufferAttribute(new Float32Array(Np), 1));
  g.setIndex(base > 65535 ? new BufferAttribute(new Uint32Array(I), 1) : new BufferAttribute(new Uint16Array(I), 1));
  g.computeBoundingSphere();
  return g;
}
const TEINTES = ['#0b3320', '#145a33', '#22834a', '#3fa75a', '#7cc95d', '#b9e27a'].map((h) => new Color(h));
function teinte(x, out) {
  x = Math.max(0, Math.min(1, x)) * (TEINTES.length - 1);
  const i = Math.min(TEINTES.length - 2, Math.floor(x));
  return out.copy(TEINTES[i]).lerp(TEINTES[i + 1], x - i);
}
function maillageFeuilles(F, U) {
  const g = new BufferGeometry();
  const v = [0, 0, 0, .25, .2, .035, .6, .26, .045, 1, 0, 0, .6, -.26, .045, .25, -.2, .035, .5, 0, -.03];
  g.setAttribute('position', new BufferAttribute(new Float32Array(v), 3));
  g.setIndex([0, 1, 6, 1, 2, 6, 2, 3, 6, 3, 4, 6, 4, 5, 6, 5, 0, 6]);
  g.computeVertexNormals();
  const mat = new MeshLambertMaterial({ side: DoubleSide });
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
        attribute float aNaiss; attribute float aPhase; uniform float uT; uniform float uTemps; uniform float uVent; varying float vJeune;
        vec3 vent(vec3 p) { float h = max(p.y, 0.0) / 520.0; h *= h;
          return uVent * h * vec3(sin(uTemps * .9 + p.y * .004 + p.z * .002) * 7.0, 0.0, cos(uTemps * .7 + p.x * .003) * 5.0); }
        float rebond(float x) { float c = 1.6, y = x - 1.0; return 1.0 + (c + 1.0) * y * y * y + c * y * y; }   // pow() est indéfini pour une base négative`)
      .replace('#include <begin_vertex>', `
        float age = uT - aNaiss;
        vec3 transformed = position * (age <= 0.0 ? 0.0 : rebond(clamp(age / 0.75, 0.0, 1.0)));
        vJeune = 1.0 - smoothstep(0.0, 1.6, age);`)
      .replace('#include <project_vertex>', `
        vec4 mvPosition = instanceMatrix * vec4(transformed, 1.0);
        mvPosition.xyz += vent(mvPosition.xyz) + vec3(0.0, sin(uTemps * 2.7 + aPhase) * 1.1, cos(uTemps * 2.3 + aPhase) * .8) * uVent;
        mvPosition = modelViewMatrix * mvPosition; gl_Position = projectionMatrix * mvPosition;`);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vJeune;')
      .replace('#include <color_fragment>', '#include <color_fragment>\n diffuseColor.rgb = mix(diffuseColor.rgb, vec3(.42, .62, .10), vJeune * .55);');
  };
  const im = new InstancedMesh(g, mat, F.length);
  const M = new Matrix4(), X = new Vector3(), Y = new Vector3(), Z = new Vector3(), c = new Color();
  const na = new Float32Array(F.length), ph = new Float32Array(F.length);
  F.forEach((f, i) => {
    X.set(f.d[0], f.d[1], f.d[2]);
    Z.set(-f.d[0] * .3 + (Math.sin(f.ph * 3) * .6), 1, -f.d[2] * .3 + Math.cos(f.ph * 5) * .6);
    Z.addScaledVector(X, -Z.dot(X)).normalize();
    Y.crossVectors(Z, X).normalize();
    const e = 15 * f.e;
    M.makeBasis(X.clone().multiplyScalar(e), Y.clone().multiplyScalar(e), Z.clone().multiplyScalar(e));
    M.setPosition(f.x, f.y, f.z);
    im.setMatrixAt(i, M);
    im.setColorAt(i, teinte(f.b, c));
    na[i] = f.t; ph[i] = f.ph;
  });
  g.setAttribute('aNaiss', new InstancedBufferAttribute(na, 1));
  g.setAttribute('aPhase', new InstancedBufferAttribute(ph, 1));
  im.frustumCulled = false;
  return im;
}
function maillageHerbe(U, R) {
  const g = new BufferGeometry();
  const v = [], idx = [];
  const hs = [0, .35, .7, 1], ws = [1, .78, .45, 0];
  hs.forEach((h, k) => { v.push(-ws[k] / 2 + h * h * .25, h, 0, ws[k] / 2 + h * h * .25, h, 0); });
  for (let k = 0; k < 3; k++) { const a = 2 * k; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  g.setAttribute('position', new BufferAttribute(new Float32Array(v), 3));
  g.setIndex(idx); g.computeVertexNormals();
  const mat = new MeshLambertMaterial({ side: DoubleSide });
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uT; uniform float uTemps; uniform float uVent;')
      .replace('#include <begin_vertex>', 'vec3 transformed = vec3(position.x, position.y * smoothstep(0.0, 1.0, (uT - 0.9) / 2.2), position.z);')
      .replace('#include <project_vertex>', `
        vec4 mvPosition = instanceMatrix * vec4(transformed, 1.0);
        mvPosition.x += sin(uTemps * 1.7 + mvPosition.x * .05 + mvPosition.z * .03) * position.y * position.y * 3.0 * uVent;
        mvPosition = modelViewMatrix * mvPosition; gl_Position = projectionMatrix * mvPosition;`);
  };
  const n = 4200, im = new InstancedMesh(g, mat, n), M = new Matrix4(), c = new Color(), q = new Matrix4();
  const verts = ['#2c6e38', '#3b8d48', '#245a31', '#4ea457', '#5f8f3a'];
  for (let i = 0; i < n; i++) {
    let x = (R() * 2 - 1) * (BLOC.x - 6), z = (R() * 2 - 1) * (BLOC.z - 6);
    if (Math.hypot(x, z) < 34) { x += 40; }
    const h = (5 + 13 * R() * R()) * (R() < .06 ? 2 : 1);
    M.makeRotationY(R() * 6.28); q.makeScale(1.7, h, 1.7); M.multiply(q); M.setPosition(x, 0, z);
    im.setMatrixAt(i, M); im.setColorAt(i, c.set(verts[Math.floor(R() * verts.length)]));
  }
  im.frustumCulled = false;
  return im;
}

/* ---------- mise en scène ---------- */
export function lancer() {
  try { return demarrer(); } catch (e) { if (window.console) console.warn('arbre 3D indisponible', e); return false; }
}
function demarrer() {
  const hero = document.getElementById('ab-hero'), stage = document.getElementById('ab-stage');
  if (!hero || !stage) return false;
  const cap = document.getElementById('ab-cap');
  const places = [...stage.querySelectorAll('[data-t]')];
  const nds = places.filter((e) => e.tagName === 'A');
  const q = /[?&]graine=(\d+)/.exec(location.search), graine = q ? +q[1] : 20261119;
  const liens = places.map((el) => {
    const x = +el.getAttribute('data-x'), y = +el.getAttribute('data-y');
    const t = el.getAttribute('data-t');
    let y3 = GY - y;                                     // la coupe est moins haute que le sol de l'arbre 2D
    if (t === 'sol') y3 = -236; else if (t === 'deco' && y3 < -250) y3 = -286;
    return { el, t, x3: x - W / 2, y3, rev: 0 };
  });

  const toileGL = document.createElement('canvas');
  toileGL.id = 'ab-cv-3d'; toileGL.setAttribute('aria-hidden', 'true');
  const renderer = new WebGLRenderer({ canvas: toileGL, antialias: true, alpha: true, stencil: true, powerPreference: 'high-performance' });
  renderer.setClearColor(0x000000, 0);
  stage.insertBefore(toileGL, stage.firstChild);
  hero.classList.add('ab-js', 'ab-3d');

  const { A, Rc, F, fin } = construire(graine, liens);
  const U = { uT: { value: 0 }, uTemps: { value: 0 }, uVent: { value: 0 } };
  const scene = new Scene(), plante = new Group();
  scene.add(plante);
  scene.add(new HemisphereLight(0xe8f4ff, 0x6b5a3e, 2.2));
  const soleil = new DirectionalLight(0xfff1da, 2.7); soleil.position.set(-520, 900, 640); scene.add(soleil);
  const face = new DirectionalLight(0xffffff, .9); face.position.set(0, 150, 1000); scene.add(face);

  const ecorce = texEcorce();
  const ECORCE = ['#5a3e2a', '#5d402b', '#664831', '#70523b', '#7c5e46'];
  const bois = new Mesh(tubes(A, (ch) => ECORCE[Math.min(4, ch.niv)], true),
    croissance(new MeshLambertMaterial({ vertexColors: true, map: ecorce }), U, .9, false));
  plante.add(bois);
  const racines = new Mesh(tubes(Rc, (ch) => ch.niv >= 3 ? '#d8b07a' : '#c8955a', false),
    croissance(new MeshLambertMaterial({ vertexColors: true, map: ecorce, emissive: 0x5a3a18 }), U, 0, true));
  racines.renderOrder = 2;
  plante.add(racines);
  plante.add(maillageFeuilles(F, U));

  /* bloc de terre : dessus, herbe, face de coupe (fenêtre) */
  const dessus = new Mesh(new PlaneGeometry(BLOC.x * 2, BLOC.z * 2), new MeshLambertMaterial({ map: texDessus() }));
  dessus.rotation.x = -Math.PI / 2; scene.add(dessus);
  scene.add(maillageHerbe(U, hasard(graine + 3)));
  const coupe = new Mesh(new PlaneGeometry(BLOC.x * 2, BLOC.h), new MeshBasicMaterial({ map: texCoupe(), depthWrite: false }));
  coupe.position.set(0, -BLOC.h / 2, BLOC.z);
  Object.assign(coupe.material, { stencilWrite: true, stencilRef: 1, stencilFunc: AlwaysStencilFunc, stencilZPass: ReplaceStencilOp });
  coupe.renderOrder = 1; scene.add(coupe);

  /* caméra : presque de face, légèrement au-dessus (4,5°), de loin pour que le cadrage reprenne celui de l'arbre 2D */
  const D = 3000, el = 4.5 * Math.PI / 180, yc = 104;
  const camera = new PerspectiveCamera(2 * Math.atan(H * 1.06 / 2 / D) * 180 / Math.PI, W / H, 100, 9000);
  camera.position.set(0, yc + D * Math.sin(el), D * Math.cos(el)); camera.lookAt(0, yc, 0);

  /* liens : projection des ancrages */
  const ancres = liens.map((L) => {
    let p;
    if (L.t === 'racine' || L.t === 'branche' || L.t === 'fruit') {
      const S = L.t === 'racine' ? Rc : A, b = S.n[L.bout];
      p = new Vector3(b.x, b.y - 18, b.z);                 // fruit : sous le bout de son rameau
      if (L.t === 'branche') p.set(L.x3, L.y3, ZB);       // étiquettes : à leur place prévue, pour ne jamais se chevaucher
      if (L.t === 'racine') p.set(L.x3, L.y3, ZR);
      return { L, p, tourne: true };
    }
    if (L.t === 'tronc') return { L, p: new Vector3(0, L.y3, 40), tourne: true };
    return { L, p: new Vector3(L.x3, L.y3, BLOC.z), tourne: false };   // sol, légendes : sur la face de coupe
  });
  const v = new Vector3();
  function placer() {
    plante.updateMatrixWorld();
    for (const a of ancres) {
      v.copy(a.p); if (a.tourne) plante.localToWorld(v);
      const z = v.z; v.project(camera);
      a.L.el.style.left = ((v.x + 1) * 50).toFixed(2) + '%';
      a.L.el.style.top = ((1 - v.y) * 50).toFixed(2) + '%';
      a.L.el.style.setProperty('--vis', a.tourne && z < -60 ? '.55' : '1');
    }
  }
  function majLiens(t) { for (const L of liens) if (t >= L.rev) L.el.classList.add('on'); }

  /* interactions : survol, toucher en deux temps sur petit écran, glisser pour tourner */
  let petit = false, arme = null;
  const legende = (a) => { if (cap) cap.textContent = '→ ' + a.getAttribute('data-p'); };
  for (const a of nds) {
    a.addEventListener('mouseenter', () => legende(a));
    a.addEventListener('focus', () => { legende(a); a.classList.add('on'); });
    a.addEventListener('click', (e) => {
      if (!petit || !window.matchMedia('(hover: none)').matches || arme === a) return;
      e.preventDefault();
      if (arme) arme.classList.remove('arme');
      arme = a; a.classList.add('arme');
      if (cap) {
        cap.textContent = '→ ' + a.getAttribute('data-p') + ' ';
        const o = document.createElement('a'); o.href = a.getAttribute('href'); o.textContent = 'Ouvrir'; o.className = 'ab-ouvrir'; cap.appendChild(o);
      }
    });
  }
  let glisse = null, decal = 0, elan = 0;
  toileGL.addEventListener('pointerdown', (e) => { glisse = { x: e.clientX, d: decal }; toileGL.setPointerCapture(e.pointerId); });
  toileGL.addEventListener('pointermove', (e) => {
    if (!glisse) return;
    const nd = glisse.d + (e.clientX - glisse.x) / Math.max(200, stage.clientWidth) * 3.2;
    elan = nd - decal; decal = nd;
  });
  const lacher = () => { glisse = null; };
  toileGL.addEventListener('pointerup', lacher); toileGL.addEventListener('pointercancel', lacher);

  /* dimensions */
  function dimensionner() {
    const lw = stage.clientWidth || W;
    petit = lw < 860; stage.classList.toggle('ab-petit', petit);
    stage.style.setProperty('--u', (lw / W).toFixed(4));
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, lw < 700 ? 1.5 : 2));
    renderer.setSize(lw, lw * H / W, false);
  }
  dimensionner();
  let attente = 0;
  window.addEventListener('resize', () => { clearTimeout(attente); attente = setTimeout(dimensionner, 150); });

  /* animation */
  let t0 = performance.now(), raf = 0, visible = true, fini = false, tPause = 0, derniere = 0;
  function image(now) {
    const t = (now - t0) / 1000;
    if (fini && !glisse && now - derniere < 31) { raf = requestAnimationFrame(image); return; }   // 30 images/s une fois l'arbre poussé
    derniere = now;
    U.uT.value = t; U.uTemps.value = now / 1000;
    const apres = lissee((t - fin + 1.5) / 3);       // la rotation et le vent s'installent après la croissance
    U.uVent.value = .35 + .65 * apres;
    if (!glisse) { decal += elan; elan *= .92; }
    plante.rotation.y = decal + .5 * apres * Math.sin((t - fin) * 2 * Math.PI / 46);
    placer(); majLiens(t);
    if (!fini && t > fin) { fini = true; hero.classList.add('ab-fini'); }
    renderer.render(scene, camera);
    raf = visible && !document.hidden ? requestAnimationFrame(image) : 0;
  }
  function reprendre() { if (!raf && visible && !document.hidden) { t0 += performance.now() - tPause; raf = requestAnimationFrame(image); } }
  function suspendre() { if (raf) { cancelAnimationFrame(raf); raf = 0; } tPause = performance.now(); }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((e) => { visible = e[0].isIntersecting; if (visible) reprendre(); else suspendre(); }).observe(stage);
  }
  document.addEventListener('visibilitychange', () => { if (document.hidden) suspendre(); else reprendre(); });
  window.abReplay = () => {
    for (const L of liens) L.el.classList.remove('on');
    hero.classList.remove('ab-fini'); fini = false; decal = 0; elan = 0;
    t0 = performance.now();
    if (!raf) raf = requestAnimationFrame(image);
  };
  if (/[?&]debogage/.test(location.search)) {
    window.abArbre3d = { renderer, scene, camera, plante, U, fin, feuilles: F.length,
      sommets: () => bois.geometry.attributes.position.count + racines.geometry.attributes.position.count,
      fige: (t, angle) => { cancelAnimationFrame(raf); raf = 0; U.uT.value = t; U.uVent.value = 0; plante.rotation.y = angle || 0; placer(); majLiens(t); renderer.render(scene, camera); } };
  }
  raf = requestAnimationFrame(image);
  return true;
}
