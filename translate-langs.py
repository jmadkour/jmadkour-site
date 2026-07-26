#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traduction automatique FR -> EN / ES / AR pour TOUT le site (moteurs hybrides).

  • EN et ES  -> DeepL API Free  (gratuit, 500 000 caractères/mois)
  • AR        -> API Claude (Anthropic)  (meilleure qualité en arabe)

Le FRANÇAIS est la source unique de vérité. Vous éditez les .qmd français
(accueil, Licence/Master/Doctorat/À propos, et tout le dossier cours/) ; ce
script régénère les miroirs en/, es/, ar/.

Utilisation
-----------
    python3 translate-langs.py            # traduit les pages FR modifiées (incrémental)
    python3 translate-langs.py --all      # force la retraduction de tout
    python3 translate-langs.py --index-only   # régénère seulement l'accueil (sans API)

Il tourne aussi en « pre-render » de Quarto. Sans clé, rien ne casse : l'accueil
traduit est régénéré et les pages non encore traduites sont créées en français
(provisoire) pour que le site s'affiche dans les quatre langues.

Pré-requis (sur votre machine)
------------------------------
    pip install deepl anthropic
    setx DEEPL_API_KEY     "xxxxxxxx:fx"      # EN + ES   (clé gratuite DeepL)
    setx ANTHROPIC_API_KEY "sk-ant-..."       # AR        (clé API Claude)
    (rouvrir le terminal ensuite)

Geler une page relue à la main : `i18n-lock: true` dans son en-tête YAML.
"""
import os, sys, re, json, hashlib, pathlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT   = pathlib.Path(__file__).resolve().parent
LANGS  = {"en": "English", "es": "Spanish (español)", "ar": "Arabic (العربية) — right-to-left"}
ENGINE = {"en": "deepl", "es": "deepl", "ar": "claude"}     # moteur par langue
DEEPL_TARGET = {"en": "EN-US", "es": "ES"}
STATE  = ROOT / ".i18n-state.json"
MODEL  = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
SIDEBAR_IDS = ("descriptive", "probabilites", "inferentielle", "econometrie")

def content_sources():
    roots = [p.name for p in ROOT.glob("*.qmd") if p.name != "index.qmd"]
    cours = [str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.glob("cours/**/*.qmd")]
    return sorted(roots) + sorted(cours)

# --- prompt système pour Claude (arabe) ---
SYSTEM = """You are a professional translator for an academic website on statistics and econometrics.
Translate the Quarto Markdown (.qmd) document below from French into {target}.

STRICT OUTPUT RULES — follow exactly:
- Output ONLY the translated .qmd document. No preamble, no code fence around the whole file.
- Keep the YAML front matter and its keys unchanged; translate ONLY the values of `title` and `subtitle`.
- NEVER translate or modify: URLs, file paths, link destinations inside (...), image paths, LaTeX math ($...$, $$...$$, \\(...\\), \\[...\\]), inline code, fenced code blocks, HTML tags/attributes, and Quarto fenced-div syntax such as ::: {.callout-note} or ::: {.grid}.
- DO translate: prose, headings, list items, link labels [like this], and button labels like "▶ Ouvrir les diapositives" / "⬇ Télécharger le PDF" (keep the symbol).
- Preserve all Markdown formatting identically. Use precise academic terminology."""


# ----------------------------------------------------------------------------
# Accueil (arbre SVG) — déterministe, sans API
# ----------------------------------------------------------------------------
LABELS = {
 "SOL : SCIENCES ÉCONOMIQUES":{"en":"SOIL: ECONOMIC SCIENCES","es":"SUELO: CIENCIAS ECONÓMICAS","ar":"التربة: العلوم الاقتصادية"},
 "Analyse mathématique":{"en":"Mathematical analysis","es":"Análisis matemático","ar":"التحليل الرياضي"},
 "Algèbre linéaire":{"en":"Linear algebra","es":"Álgebra lineal","ar":"الجبر الخطي"},
 "Statistique inférentielle":{"en":"Inferential statistics","es":"Estadística inferencial","ar":"الإحصاء الاستدلالي"},
 "Statistique descriptive":{"en":"Descriptive statistics","es":"Estadística descriptiva","ar":"الإحصاء الوصفي"},
 "Probabilités":{"en":"Probability","es":"Probabilidad","ar":"الاحتمالات"},
 "Prévisions":{"en":"Forecasting","es":"Previsiones","ar":"التنبؤات"},
 "Risque financier":{"en":"Financial risk","es":"Riesgo financiero","ar":"المخاطر المالية"},
 "Politiques publiques":{"en":"Public policy","es":"Políticas públicas","ar":"السياسات العمومية"},
 "Séries temporelles":{"en":"Time series","es":"Series temporales","ar":"السلاسل الزمنية"},
 "Variables qualitatives":{"en":"Qualitative variables","es":"Variables cualitativas","ar":"المتغيرات النوعية"},
 "Données de panel":{"en":"Panel data","es":"Datos de panel","ar":"بيانات البانل"},
 "Modèles de durée":{"en":"Duration models","es":"Modelos de duración","ar":"نماذج المدة"},
 "introduction à l'économétrie":{"en":"introduction to econometrics","es":"introducción a la econometría","ar":"مدخل إلى الاقتصاد القياسي"},
 "— racines et tronc":{"en":"— roots and trunk","es":"— raíces y tronco","ar":"— الجذور والجذع"},
 "— branches":{"en":"— branches","es":"— ramas","ar":"— الأغصان"},
 "— fruits":{"en":"— fruits","es":"— frutos","ar":"— الثمار"},
 "Licence":{"en":"Bachelor's","es":"Grado","ar":"الإجازة"},
 "Master":{"en":"Master's","es":"Máster","ar":"الماستر"},
 "Doctorat":{"en":"Doctorate","es":"Doctorado","ar":"الدكتوراه"},
}
CAP={"en":"Hover or click a part of the tree to open its page…","es":"Pase el cursor o haga clic en una parte del árbol para abrir su página…","ar":"مرّر المؤشر أو انقر على جزء من الشجرة لفتح صفحتها…"}
BTN={"en":"↻ Replay the growth","es":"↻ Repetir el crecimiento","ar":"↻ إعادة تشغيل النمو"}
PT ={"en":"jmadkour.org — Statistics & econometrics","es":"jmadkour.org — Estadística y econometría","ar":"jmadkour.org — الإحصاء والاقتصاد القياسي"}
FR_PROSE=("Bienvenue. Ce site est un **manuel vivant** de statistique et d'économétrie : cours en LaTeX, "
"visualisations interactives et code exécutable. Choisissez votre niveau — [Licence](licence.qmd), "
"[Master](master.qmd) ou [Doctorat](doctorat.qmd) — ou cliquez directement une partie de l'arbre ci-dessus.")
PROSE={
"en":("Welcome. This site is a **living textbook** of statistics and econometrics: courses in LaTeX, "
"interactive visualizations and runnable code. Choose your level — [Bachelor's](licence.qmd), "
"[Master's](master.qmd) or [Doctorate](doctorat.qmd) — or click directly on a part of the tree above."),
"es":("Bienvenido. Este sitio es un **manual vivo** de estadística y econometría: cursos en LaTeX, "
"visualizaciones interactivas y código ejecutable. Elija su nivel — [Grado](licence.qmd), "
"[Máster](master.qmd) o [Doctorado](doctorat.qmd) — o haga clic directamente en una parte del árbol de arriba."),
"ar":("مرحبًا. هذا الموقع **كتاب حيّ** في الإحصاء والاقتصاد القياسي: دروس بصيغة LaTeX، ورسوم تفاعلية، "
"وشيفرة قابلة للتنفيذ. اختر مستواك — [الإجازة](licence.qmd)، [الماستر](master.qmd) أو [الدكتوراه](doctorat.qmd) — "
"أو انقر مباشرة على جزء من الشجرة أعلاه."),
}

def build_index():
    src = (ROOT/"index.qmd").read_text(encoding="utf-8")
    for lang in LANGS:
        s = src
        s = s.replace('pagetitle: "jmadkour.org — Statistique & économétrie"', f'pagetitle: "{PT[lang]}"')
        s = s.replace('page-layout: full', f'page-layout: full\nlang: {lang}', 1)
        s = s.replace(FR_PROSE, PROSE[lang])
        s = s.replace("Survolez ou cliquez une partie de l'arbre pour ouvrir la page…", CAP[lang])
        s = s.replace("↻ Rejouer la croissance", BTN[lang])
        for fr in sorted(LABELS, key=len, reverse=True):
            s = s.replace(fr, LABELS[fr][lang])
        if lang == "ar":
            s = s.replace('```{=html}\n<style>',
                          '```{=html}\n<script>document.documentElement.setAttribute("dir","rtl");</script>\n<style>', 1)
        out = ROOT/lang/"index.qmd"; out.parent.mkdir(exist_ok=True)
        if locked(out):
            print(f"  · {lang}/index.qmd  (gelé)"); continue
        out.write_text(s, encoding="utf-8"); print(f"  ✓ {lang}/index.qmd")


# ----------------------------------------------------------------------------
# Masquage / restauration (pour DeepL : protège tout sauf la prose)
# ----------------------------------------------------------------------------
_PATTERNS = [
    re.compile(r'```.*?```', re.S),      # blocs de code / HTML brut
    re.compile(r'(?m)^:{3,}.*$'),        # lignes de divs Quarto :::
    re.compile(r'\$\$.*?\$\$', re.S),    # maths (display)
    re.compile(r'\$[^\$\n]+\$'),         # maths (inline)
    re.compile(r'`[^`\n]+`'),            # code inline
    re.compile(r'\]\([^)\n]*\)'),        # cibles de liens/images ](...)
    re.compile(r'\{[^}\n]*\}'),          # blocs d'attributs {...}
]
def protect(text):
    store = []
    def repl(m):
        store.append(m.group(0)); return f'<x id="{len(store)-1}"/>'
    for pat in _PATTERNS:
        text = pat.sub(repl, text)
    return text, store
def restore(text, store):
    for i, orig in enumerate(store):
        text = text.replace(f'<x id="{i}"/>', orig)
    return text

def split_fm(text):
    m = re.match(r'^(---\n.*?\n---\n)(.*)$', text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


# ----------------------------------------------------------------------------
# Moteurs
# ----------------------------------------------------------------------------
def deepl_page(srctext, lang, tr):
    """tr : fonction chaîne->chaîne (DeepL)."""
    fm, body = split_fm(srctext)
    def fmrep(m): return f'{m.group(1)}"{tr(m.group(2))}"'
    fm = re.sub(r'(?m)^(title:\s*)"([^"]*)"', fmrep, fm)
    fm = re.sub(r'(?m)^(subtitle:\s*)"([^"]*)"', fmrep, fm)
    masked, store = protect(body)
    masked = masked.replace("&", "&amp;")          # DeepL (mode xml) exige un & échappé
    translated = tr(masked).replace("&amp;", "&")
    return fm + restore(translated, store)

def claude_page(srctext, target, client):
    msg = client.messages.create(model=MODEL, max_tokens=8000,
        system=SYSTEM.format(target=target),
        messages=[{"role": "user", "content": srctext}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


# ----------------------------------------------------------------------------
def locked(path):
    return path.exists() and re.search(r'(?m)^\s*i18n-lock:\s*true\s*$', path.read_text(encoding="utf-8") or "")

def postprocess(qmd, relpath, lang):
    t = qmd.strip() + "\n"
    if re.search(r'(?m)^lang:', t):
        t = re.sub(r'(?m)^lang:.*$', f'lang: {lang}', t, count=1)
    else:
        t = re.sub(r'^(---\s*\n)', rf'\1lang: {lang}\n', t, count=1)
    t = re.sub(r'(?m)^sidebar:\s*(' + '|'.join(SIDEBAR_IDS) + r')\s*$',
               lambda m: f'sidebar: {m.group(1)}-{lang}', t)
    parts = relpath.split("/")
    if len(parts) >= 2 and parts[0] == "cours":
        pfx = f"../../../cours/{parts[1]}/slides/"
        t = t.replace("](slides/", f"]({pfx}").replace('src="slides/', f'src="{pfx}')
    if lang == "ar" and 'setAttribute("dir","rtl")' not in t:
        p = t.split("---", 2)
        if len(p) == 3:
            rtl = '\n```{=html}\n<script>document.documentElement.setAttribute("dir","rtl");</script>\n```\n'
            t = "---" + p[1] + "---" + rtl + p[2]
    return t


def main():
    args = set(sys.argv[1:]); force = "--all" in args
    print("Accueil (arbre) :"); build_index()
    if "--index-only" in args:
        return

    # --- connexions aux moteurs (dégradation propre) ---
    deepl_tr = None; deepl_why = ""; deepl_url = ""
    try:
        import deepl
        key = os.environ.get("DEEPL_API_KEY", "").strip()
        if key:
            # essaie le serveur gratuit puis le serveur Pro (ou celui forcé par DEEPL_SERVER_URL)
            urls = [os.environ["DEEPL_SERVER_URL"]] if os.environ.get("DEEPL_SERVER_URL") \
                   else ["https://api-free.deepl.com", "https://api.deepl.com"]
            last = ""
            for u in urls:
                try:
                    _dt = deepl.Translator(key, server_url=u)
                    _dt.get_usage()                     # valide la clé ET le serveur
                    def deepl_tr(text, code, _t=_dt):
                        return _t.translate_text(text, source_lang="FR", target_lang=code,
                                                 tag_handling="xml", ignore_tags=["x"]).text
                    deepl_url = u
                    break
                except Exception as e:
                    last = str(e); deepl_tr = None
            if deepl_tr is None:
                deepl_why = (f"clé refusée par DeepL ({last}) "
                             f"[clé fournie : {len(key)} caractères, finit par ':fx' = {key.endswith(':fx')}]")
        else:
            deepl_why = "clé DEEPL_API_KEY absente de l'environnement"
    except Exception as e:
        deepl_why = f"paquet 'deepl' non installé pour ce Python ({e})"
    claude_cl = None; claude_why = ""
    try:
        import anthropic
        if os.environ.get("ANTHROPIC_API_KEY"):
            claude_cl = anthropic.Anthropic()
        else:
            claude_why = "clé ANTHROPIC_API_KEY absente de l'environnement"
    except Exception as e:
        claude_why = f"paquet 'anthropic' non installé pour ce Python ({e})"

    def available(lang):
        return deepl_tr is not None if ENGINE[lang] == "deepl" else claude_cl is not None

    def translate(srctext, lang):
        if ENGINE[lang] == "deepl":
            return deepl_page(srctext, lang, lambda s: deepl_tr(s, DEEPL_TARGET[lang]))
        return claude_page(srctext, LANGS[lang], claude_cl)

    print(f"Moteurs : EN/ES → DeepL {('OK (' + deepl_url + ')') if deepl_tr else 'absent — ' + deepl_why} · "
          f"AR → Claude {'OK' if claude_cl else 'absent — ' + claude_why}")
    print(f"(Python utilisé : {sys.executable})")

    sources = content_sources()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    done = ph = 0
    print("Pages de contenu :")
    for rel in sources:
        srctext = (ROOT/rel).read_text(encoding="utf-8")
        h = hashlib.md5(srctext.encode("utf-8")).hexdigest()
        for lang in LANGS:
            out = ROOT/lang/rel; key = f"{lang}/{rel}"
            if locked(out):
                continue
            if available(lang):
                if not force and out.exists() and state.get(key) == h:
                    continue
                try:
                    res = postprocess(translate(srctext, lang), rel, lang)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(res, encoding="utf-8"); state[key] = h; done += 1
                    print(f"  ✓ {key}")
                except Exception as e:
                    print(f"  ✗ {key} : {e}")
            elif not out.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(postprocess(srctext, rel, lang), encoding="utf-8"); ph += 1

    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=0))
    msg = f"Terminé. {done} page(s) traduite(s)."
    if ph:
        msg += f" {ph} page(s) créée(s) en français (provisoire) — ajoutez les clés manquantes puis relancez."
    print(msg)

if __name__ == "__main__":
    main()
