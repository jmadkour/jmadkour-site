# -*- coding: utf-8 -*-
"""
=====================================================================
 Détecteur de diapositives qui débordent
=====================================================================

 Beamer ne signale pas visiblement qu'un contenu dépasse du cadre :
 il émet un « Overfull \\vbox » dans un journal que Quarto efface, et
 produit tout de même un PDF. Le texte sort alors par le bas ou par la
 droite de la diapositive, et cela ne se voit qu'à l'écran.

 Ce script rend chaque page en niveaux de gris à basse résolution et
 compte les pixels sombres dans les trois dernières lignes et les trois
 dernières colonnes. Il exige de l'encre sur au moins deux d'entre
 elles : un bloc coupé en laisse sur plusieurs, un simple filet — axe
 d'un graphique posé au ras du cadre — n'en laisse que sur une.

 IMPORTANT : à lancer sur VOS PDF, après « quarto render » et
 « publier.sh ». Les polices de MiKTeX ne sont pas exactement celles
 des autres machines, et une diapositive peut déborder chez vous sans
 déborder ailleurs.

 Usage :
     python scripts/deborde.py                    # les 24 cours du site
     python scripts/deborde.py cours/probabilites # un seul cours
     python scripts/deborde.py ../stats-eco-cours/cours-analyse-donnees
     python scripts/deborde.py --seuil 10 --dpi 48

 Prérequis : PyMuPDF, à installer une fois pour toutes par
     pip install pymupdf
 (à défaut, le script utilise pdftoppm s'il est dans le PATH)

 Code de retour : 0 si tout va bien, 1 si au moins un débordement.
=====================================================================
"""

import sys
import os
import glob
import argparse
import subprocess
import tempfile
import shutil

# ---------------------------------------------------------------------
#  Rendu des pages : deux moteurs possibles, une seule sortie
#  -> liste de (largeur, hauteur, octets en niveaux de gris)
# ---------------------------------------------------------------------

def _moteur_pymupdf():
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    def rendre(pdf, dpi):
        pages = []
        doc = fitz.open(pdf)
        try:
            for page in doc:
                pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
                pages.append((pix.width, pix.height, pix.samples))
        finally:
            doc.close()
        return pages

    return rendre


def _moteur_pdftoppm():
    if shutil.which("pdftoppm") is None:
        return None

    def _lire_pgm(chemin):
        raw = open(chemin, "rb").read()
        i = 2                      # on saute l'entête « P5 »
        vals = []
        for _ in range(3):         # largeur, hauteur, valeur maximale
            while raw[i:i + 1].isspace():
                i += 1
            j = i
            while not raw[j:j + 1].isspace():
                j += 1
            vals.append(int(raw[i:j]))
            i = j
        i += 1                     # l'unique blanc avant les données
        w, h, _ = vals
        return w, h, raw[i:i + w * h]

    def rendre(pdf, dpi):
        dossier = tempfile.mkdtemp()
        try:
            subprocess.run(["pdftoppm", "-gray", "-r", str(dpi), pdf,
                            os.path.join(dossier, "p")],
                           capture_output=True)
            return [_lire_pgm(f)
                    for f in sorted(glob.glob(os.path.join(dossier, "p-*.pgm")))]
        finally:
            shutil.rmtree(dossier, ignore_errors=True)

    return rendre


def choisir_moteur():
    for fabrique, nom in ((_moteur_pymupdf, "PyMuPDF"),
                          (_moteur_pdftoppm, "pdftoppm")):
        rendre = fabrique()
        if rendre is not None:
            return rendre, nom
    sys.exit("Aucun moteur de rendu disponible.\n"
             "Installez PyMuPDF :  pip install pymupdf")


# ---------------------------------------------------------------------
#  Détection
# ---------------------------------------------------------------------

SOMBRE = 200      # un pixel est « de l'encre » en dessous de cette valeur

# Le thème metropolis fait courir sa barre de titre jusqu'au bord droit,
# sur le premier sixième de la hauteur. On exclut cette zone du contrôle
# latéral, sans quoi toutes les diapositives seraient signalées.
HAUT_IGNORE = 0.16

# Un bloc de contenu coupé par le bord laisse de l'encre sur plusieurs
# lignes d'affilée ; un simple filet — bordure de figure, axe d'un
# graphique posé au ras du cadre — n'en laisse que sur une. On exige
# donc au moins deux lignes chargées dans la bande.
#
# Sans cette règle, les moteurs de rendu ne s'accordent pas : pdftoppm
# et PyMuPDF n'arrondissent pas la dernière ligne de la même façon, et
# un filet apparaît chez l'un sans apparaître chez l'autre.
LIGNES_MINI = 2


def _encre(valeurs):
    return sum(1 for b in valeurs if b < SOMBRE)


def _borde(profil, seuil):
    """Renvoie l'encre maximale si le bord est vraiment chargé, sinon 0."""
    charges = [c for c in profil if c > seuil]
    return max(profil) if len(charges) >= LIGNES_MINI else 0


def pages_debordantes(rendre, pdf, dpi, seuil, bande):
    """Renvoie [(numéro de page, pixels en bas, pixels à droite), ...]."""
    resultats = []
    for numero, (w, h, buf) in enumerate(rendre(pdf, dpi), start=1):
        profil_bas = [_encre(buf[(h - k) * w:(h - k + 1) * w])
                      for k in range(1, bande + 1)]
        bas = _borde(profil_bas, seuil)

        y0 = int(h * HAUT_IGNORE)
        profil_droite = [_encre([buf[y * w + (w - k)]
                                 for y in range(y0, h - bande)])
                         for k in range(1, bande + 1)]
        droite = _borde(profil_droite, seuil)

        if bas > seuil or droite > seuil:
            resultats.append((numero, bas, droite))
    return resultats


def gravite(pixels, seuil):
    if pixels <= seuil:
        return ""
    if pixels < 4 * seuil:
        return "leger"
    return "NET"


# ---------------------------------------------------------------------
#  Programme principal
# ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Détecte les diapositives dont le contenu sort du cadre.")
    ap.add_argument("chemins", nargs="*", default=None,
                    help="dossiers ou fichiers PDF ; par défaut, tous les cours du site")
    ap.add_argument("--dpi", type=int, default=36,
                    help="résolution du rendu (défaut 36 : rapide et suffisant)")
    ap.add_argument("--seuil", type=int, default=5,
                    help="nombre de pixels d'encre toléré dans la bande (défaut 5)")
    ap.add_argument("--bande", type=int, default=3,
                    help="épaisseur de la bande examinée, en pixels (défaut 3)")
    args = ap.parse_args()

    rendre, moteur = choisir_moteur()

    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if args.chemins:
        fichiers = []
        for c in args.chemins:
            if os.path.isdir(c):
                trouves = sorted(glob.glob(os.path.join(c, "**", "*.pdf"),
                                           recursive=True))
                # Un dossier source contient aussi fig/ et figsrc/ : ce sont
                # des figures, pas des diaporamas, et elles touchent leur
                # propre bord par construction.
                fichiers += [f for f in trouves
                             if not any(p in ("fig", "figsrc")
                                        for p in f.replace("\\", "/").split("/"))]
            elif c.lower().endswith(".pdf"):
                fichiers.append(c)
    else:
        fichiers = sorted(glob.glob(
            os.path.join(racine, "cours", "*", "slides", "*.pdf")))

    if not fichiers:
        sys.exit("Aucun PDF trouvé.")

    print(f"Moteur : {moteur}   —   {len(fichiers)} diaporamas   "
          f"—   {args.dpi} dpi, seuil {args.seuil} px\n")

    total_pages = 0
    total_deb = 0
    cours_courant = None
    lignes_rapport = []

    for pdf in fichiers:
        cours = os.path.basename(os.path.dirname(os.path.dirname(pdf)))
        chapitre = os.path.splitext(os.path.basename(pdf))[0]

        try:
            deb = pages_debordantes(rendre, pdf, args.dpi, args.seuil, args.bande)
        except Exception as e:                       # PDF illisible, etc.
            print(f"  !! {chapitre} : {e}")
            continue

        total_pages += 1
        if not deb:
            continue

        if cours != cours_courant:
            print(f"\n{cours}")
            cours_courant = cours
        for numero, bas, droite in deb:
            ou = []
            if bas > args.seuil:
                ou.append(f"bas {bas} px ({gravite(bas, args.seuil)})")
            if droite > args.seuil:
                ou.append(f"droite {droite} px ({gravite(droite, args.seuil)})")
            detail = " et ".join(ou)
            print(f"    {chapitre:<42s} page {numero:>3d}   {detail}")
            lignes_rapport.append(f"{cours}\t{chapitre}\t{numero}\t{detail}")
            total_deb += 1

    print()
    if total_deb == 0:
        print(f"Aucun débordement sur {len(fichiers)} diaporamas.")
        return 0

    rapport = os.path.join(racine, "debordements.txt")
    with open(rapport, "w", encoding="utf-8") as f:
        f.write("cours\tchapitre\tpage\tdetail\n")
        f.write("\n".join(lignes_rapport) + "\n")

    print(f"{total_deb} diapositive(s) à corriger, sur {len(fichiers)} diaporamas.")
    print(f"Détail écrit dans {rapport}")
    print("\nPour corriger : ouvrir le chapitre concerné dans le dépôt source,")
    print("scinder la diapositive en deux (un second titre de niveau ##),")
    print("ou réduire la largeur d'une figure.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
