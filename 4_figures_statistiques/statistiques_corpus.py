"""
Génération des statistiques complètes du corpus nettoyé (corpus_cleaned_v1.json).
Produit deux fichiers texte :
  - stats_corpus.txt        : statistiques thématiques complètes
  - stats_temporelles.txt   : distribution temporelle détaillée
"""

import json
import datetime
import statistics
import os
from collections import Counter, defaultdict

# Chemins
CORPUS  = ""  # à compléter : corpus nettoyé (data/corpus_cleaned_v1.json)
OUT_DIR = ""  # à compléter : dossier de sortie des statistiques

ALL_CIBLES_POL = [
    'reconqueteofficiel','zemmour_eric','sarah_knafo','rnational_off','jordanbardella',
    'mlp.officiel','sebchenu','julienodoul','louis_aliot','jphtanguy','david.rachline',
    'edwige_diaz','laurelavalette','jsanchez_rn','franckallisio','laurentjacobelli',
    'matthieu_valet','fabriceleggeri','philippe_ballard','kevinmauvieux','eciotti',
    'lesrepublicains','laurentwauquiez_','brunoretailleauoff','fxbellamy','rachida_dati',
    'vpecresse','horizonsleparti','parti_renaissance','emmanuelmacron','gabriel_attal',
    'gdarmanin.officiel','olivierveran','karl.olive','marleneschiappa','prisca_thevenot',
    'aurore_berge','yaelbraunpivet','benjamin_haddad','partisocialiste','fhollandeofficiel',
    'faure_olivier','jerome_guedj','borisvallaud','lesecologistes','marinetondelier',
    'sandrousseau','yjadot','marie.touss1','franceinsoumisean','jlmelenchon','manonaubryfr',
    'rima.has','mathildepanot','manuelbompard','guetteclemence','francois_ruffin',
    'clementine_autain','louisboyard','sebastiendelogu','alma_dufour','alexis_corbiere',
    'deputee_obono','eric.coquerel','bastien.lachaud','garrido.raquel','thomas_portes',
    'david_guiraud','rachel.keke.officiel','raphael_arnault','aleaument','paulvannier',
    'cmbilongo','damien.maudet','particommuniste','fabien_roussel','ianbrossatsenateur',
    'leondeffontaines','npa.anticapitaliste','lutteouvriereofficiel','olivier.besancenot',
    'philippe.poutou','nathaliearthaud','dominiquedevillepin','dupontaignannicolas',
    'florianphilippot','fasselineau','uprtvfa','marion_marechal','aymeric.caron',
]
ALL_CIBLES_MED = [
    'lhumanitefr','lemediatv','mediapartfr','blast_officiel','quotidienofficiel',
    '20minutesfrance','afpfr','c_a_vous','france24','france.inter','lcp_an','lemondefr',
    'nouvelobs','lehuffpostfr','mariannelemag','publicsenat','rfi','rtl.officiel','rtlinfo',
    'tv5monde','franceinfo','m6info_','liberation.fr','bfmtv','cnews','europe1','lexpress',
    'le_progres_','lefigaro','leparisien','lepointfr','lesechos.fr','rmc_off','sudradio',
    'tf1info','va.plus','laradionova','franctireurmag','t18_officiel','loopsider','brutofficiel',
    'laprovence_','ledauphinelibere','lepopulaire.fr','journalsudouest','ladepechedumidi',
    'slatefr','artefr','franceculture','parismatch','vakitamedia','i24news_fr','lejddfr',
    'latribune','hugodecrypte','konbini','clique_tv','streetpress_','le20hfrancetelevisions',
    'tbt9_w9',
]

# Chargement
with open(CORPUS, encoding="utf-8") as f:
    data = json.load(f)

videos   = data["videos"]
metadata = data.get("metadata", {})
N        = len(videos)
pol      = [v for v in videos if v["acteur_type"] == "politicien"]
med      = [v for v in videos if v["acteur_type"] == "media"]
comptes_pol = sorted(set(v["username"] for v in pol))
comptes_med = sorted(set(v["username"] for v in med))

def ts(t):
    return datetime.datetime.fromtimestamp(t) if t else None

def fmt(n):
    return f"{int(n):,}".replace(",", " ")  # espace fine

def pct(n, total):
    return f"{n/total*100:.1f}%" if total else "n/a"

def hms(s):
    s = int(s)
    m, sec = divmod(s, 60)
    h, m   = divmod(m, 60)
    return f"{h}h{m:02d}m{sec:02d}s" if h else f"{m}m{sec:02d}s"

def avg(lst):
    return statistics.mean(lst) if lst else 0

def med_stat(lst):
    return statistics.median(lst) if lst else 0

SEP  = "=" * 72
SEP2 = "-" * 70
JOURS = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]

def engagement_block(lst):
    views    = [v.get("view_count",   0) for v in lst]
    likes    = [v.get("like_count",   0) for v in lst]
    comments = [v.get("comment_count",0) for v in lst]
    shares   = [v.get("share_count",  0) for v in lst]
    n = len(lst)
    lines = []
    lines.append(f"    Vues     : total={fmt(sum(views))}  moy={fmt(int(avg(views)))}  médiane={fmt(int(med_stat(views)))}")
    lines.append(f"    Likes    : total={fmt(sum(likes))}  moy={fmt(int(avg(likes)))}  médiane={fmt(int(med_stat(likes)))}")
    lines.append(f"    Coms     : total={fmt(sum(comments))}  moy={fmt(int(avg(comments)))}  médiane={fmt(int(med_stat(comments)))}")
    lines.append(f"    Partages : total={fmt(sum(shares))}  moy={fmt(int(avg(shares)))}  médiane={fmt(int(med_stat(shares)))}")
    total_eng = sum(likes) + sum(comments) + sum(shares)
    ratio = total_eng / sum(views) * 100 if sum(views) else 0
    lines.append(f"    Ratio engagement/vues : {ratio:.2f}%")
    return lines

def compte_row(username, vids):
    vv = [v for v in vids if v["username"] == username]
    views    = sum(v.get("view_count",   0) for v in vv)
    likes    = sum(v.get("like_count",   0) for v in vv)
    comments = sum(v.get("comment_count",0) for v in vv)
    shares   = sum(v.get("share_count",  0) for v in vv)
    durs     = [v.get("video_duration",0) for v in vv if v.get("video_duration")]
    dur      = hms(avg(durs)) if durs else "—"
    foll     = vv[0].get("follower_count", 0) if vv else 0
    return len(vv), views, likes, comments, shares, dur, foll

#  FICHIER 1 — stats_corpus.txt
L = []

def h1(t): L.extend(["", SEP, f"  {t}", SEP])
def h2(t): L.extend(["", f"── {t} " + "─" * max(0, 68-len(t))])

L.append("STATISTIQUES COMPLÈTES DU CORPUS TIKTOK — corpus_cleaned_v1.json")
L.append(f"Généré le : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
if metadata:
    L.append(f"Version nettoyage : {metadata.get('cleaning_version','n/a')}  |  Date merge : {metadata.get('merge_date','n/a')}")

# ─ 1. Vue globale ─────────────────────────────────────────────────────────────
h1("1. VUE GLOBALE")

times = sorted(ts(v["create_time"]) for v in videos if v.get("create_time"))
L.append(f"  Vidéos totales              : {fmt(N)}")
L.append(f"    dont politiciens          : {fmt(len(pol))}  ({pct(len(pol),N)})")
L.append(f"    dont médias               : {fmt(len(med))}  ({pct(len(med),N)})")
L.append(f"  Comptes actifs dans corpus  : {len(comptes_pol)+len(comptes_med)}")
L.append(f"    dont politiciens          : {len(comptes_pol)} / {len(ALL_CIBLES_POL)} cibles")
L.append(f"    dont médias               : {len(comptes_med)} / {len(ALL_CIBLES_MED)} cibles")
L.append(f"  Période couverte            : {times[0].strftime('%d/%m/%Y')} → {times[-1].strftime('%d/%m/%Y')}")
L.append(f"  Durée fenêtre temporelle    : {(times[-1]-times[0]).days} jours")

n_vtt  = sum(1 for v in videos if (v.get("voice_to_text") or "").strip())
n_desc = sum(1 for v in videos if (v.get("video_description") or "").strip())
n_hash = sum(1 for v in videos if v.get("hashtag_names"))
regions = Counter((v.get("region_code") or "?").upper() for v in videos)
L.append(f"  Vidéos avec transcription   : {fmt(n_vtt)}  ({pct(n_vtt,N)})")
L.append(f"  Vidéos sans transcription   : {fmt(N-n_vtt)}  ({pct(N-n_vtt,N)})")
L.append(f"  Vidéos avec description     : {fmt(n_desc)}  ({pct(n_desc,N)})")
L.append(f"  Vidéos avec hashtags        : {fmt(n_hash)}  ({pct(n_hash,N)})")
L.append(f"  Codes région                : {dict(regions.most_common())}")

# ─ 2. Engagement global ───────────────────────────────────────────────────────
h1("2. ENGAGEMENT GLOBAL")
h2("Toutes vidéos")
L.extend(engagement_block(videos))
h2("Politiciens uniquement")
L.extend(engagement_block(pol))
h2("Médias uniquement")
L.extend(engagement_block(med))

# ─ 3. Durée des vidéos ────────────────────────────────────────────────────────
h1("3. DURÉE DES VIDÉOS")

for label, lst in [("Toutes", videos), ("Politiciens", pol), ("Médias", med)]:
    durs = [v["video_duration"] for v in lst if v.get("video_duration")]
    L.append(f"  {label}  (n={len(durs)})")
    L.append(f"    min={hms(min(durs))}  max={hms(max(durs))}  moy={hms(avg(durs))}  médiane={hms(med_stat(durs))}")

durs_all = [v["video_duration"] for v in videos if v.get("video_duration")]
tranches = [(0,30,"≤30s"),(30,60,"30–60s"),(60,120,"1–2min"),(120,300,"2–5min"),(300,9999,">5min")]
L.append(""); L.append("  Distribution par tranche (toutes vidéos) :")
for a, b, label in tranches:
    n_t = sum(1 for d in durs_all if a < d <= b)
    L.append(f"    {label:10s}: {n_t:4d}  ({pct(n_t,len(durs_all))})")

# ─ 4. Top 10 vidéos par vues ──────────────────────────────────────────────────
h1("4. TOP 10 VIDÉOS PAR VUES")

for label, lst in [("Toutes catégories", videos), ("Politiciens", pol), ("Médias", med)]:
    h2(label)
    ranked = sorted(lst, key=lambda v: v.get("view_count",0), reverse=True)[:10]
    for v in ranked:
        desc = (v.get("video_description") or "")[:70]
        L.append(f"  {fmt(v.get('view_count',0)):>12} vues | {fmt(v.get('like_count',0)):>7} likes | @{v['username']}")
        L.append(f"    \"{desc}\"")

# ─ 5. Détail par compte — politiciens ────────────────────────────────────────
h1("5. DÉTAIL PAR COMPTE — POLITICIENS (trié par vues décroissantes)")
header = f"  {'Compte':<32} {'Nb':>4} {'Vues':>12} {'Likes':>8} {'Coms':>7} {'Parts':>7} {'Dur.moy':>8} {'Abonnés':>10}"
L.append(header); L.append("  " + SEP2)

pol_rows = [compte_row(u, pol) + (u,) for u in comptes_pol]
for row in sorted(pol_rows, key=lambda x: -x[1]):  # x[1] = views
    nb, views, likes, coms, shares, dur, foll, u = row
    L.append(f"  @{u:<31} {nb:>4} {fmt(views):>12} {fmt(likes):>8} {fmt(coms):>7} {fmt(shares):>7} {dur:>8} {fmt(foll):>10}")

# ─ 6. Détail par compte — médias ─────────────────────────────────────────────
h1("6. DÉTAIL PAR COMPTE — MÉDIAS (trié par vues décroissantes)")
L.append(header); L.append("  " + SEP2)

med_rows = [compte_row(u, med) + (u,) for u in comptes_med]
for row in sorted(med_rows, key=lambda x: -x[1]):
    nb, views, likes, coms, shares, dur, foll, u = row
    L.append(f"  @{u:<31} {nb:>4} {fmt(views):>12} {fmt(likes):>8} {fmt(coms):>7} {fmt(shares):>7} {dur:>8} {fmt(foll):>10}")

# ─ 7. Hashtags ────────────────────────────────────────────────────────────────
h1("7. HASHTAGS LES PLUS FRÉQUENTS")

def extract_tags(lst):
    tags = []
    for v in lst:
        t = v.get("hashtag_names") or []
        tags.extend(x.lower() for x in (t if isinstance(t, list) else []) if x)
    return tags

all_tags = extract_tags(videos)
pol_tags = extract_tags(pol)
med_tags = extract_tags(med)
tc = Counter(all_tags)
L.append(f"  Hashtags distincts   : {fmt(len(tc))}")
L.append(f"  Occurrences totales  : {fmt(sum(tc.values()))}")

for label, tags, n_top in [("Toutes catégories", all_tags, 30),
                             ("Politiciens", pol_tags, 15),
                             ("Médias", med_tags, 15)]:
    h2(f"Top {n_top} — {label}")
    for tag, cnt in Counter(tags).most_common(n_top):
        bar = "▪" * min(cnt, 30)
        L.append(f"    #{tag:<35} {cnt:4d}  {bar}")

# ─ 8. Transcriptions ─────────────────────────────────────────────────────────
h1("8. TRANSCRIPTIONS (voice_to_text)")

for label, lst in [("Toutes", videos), ("Politiciens", pol), ("Médias", med)]:
    n_ok = sum(1 for v in lst if (v.get("voice_to_text") or "").strip())
    lens = [len(v.get("voice_to_text_clean") or "") for v in lst
            if (v.get("voice_to_text_clean") or "").strip()]
    L.append(f"  {label}: {n_ok}/{len(lst)} avec transcription ({pct(n_ok,len(lst))})")
    if lens:
        L.append(f"    Longueur (car.) : moy={fmt(int(avg(lens)))}  médiane={fmt(int(med_stat(lens)))}  max={fmt(max(lens))}")

# ─ 9. Longueur des descriptions ──────────────────────────────────────────────
h1("9. LONGUEUR DES DESCRIPTIONS (video_description, caractères)")

for label, lst in [("Toutes", videos), ("Politiciens", pol), ("Médias", med)]:
    lens = [len(v.get("video_description") or "") for v in lst]
    L.append(f"  {label}: moy={fmt(int(avg(lens)))}  médiane={fmt(int(med_stat(lens)))}  max={fmt(max(lens))}")

# ─ 10. Comptes sans vidéos collectées ────────────────────────────────────────
h1("10. COMPTES CIBLES SANS AUCUNE VIDÉO COLLECTÉE")

in_pol = set(comptes_pol)
in_med = set(comptes_med)
abs_pol = [c for c in ALL_CIBLES_POL if c not in in_pol]
abs_med = [c for c in ALL_CIBLES_MED if c not in in_med]

L.append(f"  Politiciens : {len(abs_pol)} comptes sans vidéo (sur {len(ALL_CIBLES_POL)} cibles)")
for c in abs_pol:
    L.append(f"    @{c}")
L.append("")
L.append(f"  Médias : {len(abs_med)} comptes sans vidéo (sur {len(ALL_CIBLES_MED)} cibles)")
for c in abs_med:
    L.append(f"    @{c}")

# ─ Pied de page ──────────────────────────────────────────────────────────────
L.extend(["", SEP, "  Fin du rapport — stats_corpus.txt", SEP])

with open(os.path.join(OUT_DIR, "stats_corpus.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("[OK] stats_corpus.txt")

#  FICHIER 2 — stats_temporelles.txt
T = []

def th1(t): T.extend(["", SEP, f"  {t}", SEP])

T.append("DISTRIBUTION TEMPORELLE DES PUBLICATIONS — corpus_cleaned_v1.json")
T.append(f"Généré le : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ─ Par mois ───────────────────────────────────────────────────────────────────
th1("PAR MOIS")
by_month = defaultdict(lambda: {"total":0,"pol":0,"med":0,"views":0,"likes":0})
for v in videos:
    if not v.get("create_time"): continue
    m = ts(v["create_time"]).strftime("%Y-%m")
    by_month[m]["total"] += 1
    by_month[m]["pol" if v["acteur_type"]=="politicien" else "med"] += 1
    by_month[m]["views"] += v.get("view_count", 0)
    by_month[m]["likes"] += v.get("like_count", 0)

T.append(f"  {'Mois':<10} {'Total':>6} {'Pol':>5} {'Méd':>5} {'Vues':>14} {'Likes':>10}  Histogramme")
T.append("  " + "-" * 70)
for m in sorted(by_month):
    d = by_month[m]
    bar = "█" * d["total"]
    T.append(f"  {m}   {d['total']:>6}  {d['pol']:>4}  {d['med']:>4}  {fmt(d['views']):>14}  {fmt(d['likes']):>10}  {bar}")

# ─ Par semaine ────────────────────────────────────────────────────────────────
th1("PAR SEMAINE (lundi au dimanche)")
by_week = defaultdict(lambda: {"total":0,"pol":0,"med":0,"views":0,"likes":0})
for v in videos:
    if not v.get("create_time"): continue
    d = ts(v["create_time"])
    lundi = (d - datetime.timedelta(days=d.weekday())).strftime("%Y-%m-%d")
    by_week[lundi]["total"] += 1
    by_week[lundi]["pol" if v["acteur_type"]=="politicien" else "med"] += 1
    by_week[lundi]["views"] += v.get("view_count", 0)
    by_week[lundi]["likes"] += v.get("like_count", 0)

T.append(f"  {'Sem. (lundi)':<14} {'Total':>6} {'Pol':>5} {'Méd':>5} {'Vues':>14} {'Likes':>10}  Histogramme")
T.append("  " + "-" * 75)
for w in sorted(by_week):
    d = by_week[w]
    bar = "█" * d["total"]
    T.append(f"  {w}   {d['total']:>6}  {d['pol']:>4}  {d['med']:>4}  {fmt(d['views']):>14}  {fmt(d['likes']):>10}  {bar}")

# ─ Par jour ───────────────────────────────────────────────────────────────────
th1("PAR JOUR")
by_day = defaultdict(lambda: {"total":0,"pol":0,"med":0,"views":0})
for v in videos:
    if not v.get("create_time"): continue
    d = ts(v["create_time"]).strftime("%Y-%m-%d")
    by_day[d]["total"] += 1
    by_day[d]["pol" if v["acteur_type"]=="politicien" else "med"] += 1
    by_day[d]["views"] += v.get("view_count", 0)

T.append(f"  {'Date':<12} {'Total':>5} {'Pol':>4} {'Méd':>4} {'Vues':>14}  Histogramme")
T.append("  " + "-" * 65)
for day in sorted(by_day):
    d = by_day[day]
    bar = "▪" * d["total"]
    T.append(f"  {day}  {d['total']:>5}  {d['pol']:>3}  {d['med']:>3}  {fmt(d['views']):>14}  {bar}")

# ─ Par jour de la semaine ─────────────────────────────────────────────────────
th1("PAR JOUR DE LA SEMAINE (agrégé sur toute la période)")
by_dow = defaultdict(lambda: {"total":0,"pol":0,"med":0,"views":0})
for v in videos:
    if not v.get("create_time"): continue
    dow = ts(v["create_time"]).weekday()
    by_dow[dow]["total"] += 1
    by_dow[dow]["pol" if v["acteur_type"]=="politicien" else "med"] += 1
    by_dow[dow]["views"] += v.get("view_count", 0)

T.append(f"  {'Jour':<12} {'Total':>6} {'Pol':>5} {'Méd':>5} {'Vues':>14}  Histogramme")
T.append("  " + "-" * 65)
for dow in range(7):
    d = by_dow[dow]
    bar = "█" * d["total"]
    T.append(f"  {JOURS[dow]:<12} {d['total']:>6}  {d['pol']:>4}  {d['med']:>4}  {fmt(d['views']):>14}  {bar}")

# ─ Par heure de publication ───────────────────────────────────────────────────
th1("PAR HEURE DE PUBLICATION")
by_hour = defaultdict(lambda: {"total":0,"pol":0,"med":0})
for v in videos:
    if not v.get("create_time"): continue
    h = ts(v["create_time"]).hour
    by_hour[h]["total"] += 1
    by_hour[h]["pol" if v["acteur_type"]=="politicien" else "med"] += 1

T.append(f"  {'Heure':>5} {'Total':>6} {'Pol':>5} {'Méd':>5}  Histogramme")
T.append("  " + "-" * 55)
for h in range(24):
    d = by_hour[h]
    bar = "█" * d["total"]
    T.append(f"  {h:02d}h    {d['total']:>6}  {d['pol']:>4}  {d['med']:>4}  {bar}")

# ─ Activité par compte dans le temps (top comptes) ────────────────────────────
th1("ACTIVITÉ PAR COMPTE AU FIL DU TEMPS — top 10 comptes (toutes catégories)")
top10 = [u for u, _ in Counter(v["username"] for v in videos).most_common(10)]
months = sorted(by_month.keys())
T.append(f"  {'Compte':<30} " + "  ".join(m[5:] for m in months))
T.append("  " + "-" * (30 + 8 * len(months)))

for u in top10:
    vv_u = [v for v in videos if v["username"] == u]
    row = []
    for m in months:
        cnt = sum(1 for v in vv_u if v.get("create_time") and ts(v["create_time"]).strftime("%Y-%m") == m)
        row.append(f"{cnt:>5}" if cnt else "    —")
    T.append(f"  @{u:<29} " + "  ".join(row))

# ─ Pied de page ──────────────────────────────────────────────────────────────
T.extend(["", SEP, "  Fin du rapport — stats_temporelles.txt", SEP])

with open(os.path.join(OUT_DIR, "stats_temporelles.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(T))
print("[OK] stats_temporelles.txt")
