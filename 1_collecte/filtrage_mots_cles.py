# Filtrage thématique du corpus par mots-clés et statistiques associées.

import json
from datetime import datetime
from pathlib import Path

CHEMIN_JSON = ""  # à compléter : JSON de collecte en entrée (sortie de collecte_api_politiciens.py)
CHEMIN_STATS = ""  # à compléter : JSON filtré et statistiques en sortie

MOTS_CLES = ["Quentin", "Deranque", "antifa", "neonazi", "identitaire"]

# Chargement
with open(CHEMIN_JSON, "r", encoding="utf-8") as f:
    donnees = json.load(f)

metadata = donnees.get("metadata", {})
videos = donnees.get("videos", [])

# Aperçu général
date_debut_cfg = metadata.get("date_debut_periode", "")
date_fin_cfg   = metadata.get("date_fin_periode", "")

# Date de collecte
date_collecte = metadata.get("date_collecte", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Dates réelles des vidéos
timestamps = [v.get("create_time", 0) for v in videos if v.get("create_time")]
if timestamps:
    ts_min = min(timestamps)
    ts_max = max(timestamps)
    video_la_plus_ancienne = datetime.fromtimestamp(ts_min).strftime("%Y-%m-%d")
    video_la_plus_recente  = datetime.fromtimestamp(ts_max).strftime("%Y-%m-%d")
else:
    video_la_plus_ancienne = ""
    video_la_plus_recente  = ""

# Durée de la période
from datetime import date
try:
    d1 = date.fromisoformat(date_debut_cfg)
    d2 = date.fromisoformat(date_fin_cfg)
    duree_jours = (d2 - d1).days
except Exception:
    duree_jours = 0

# Comptes
comptes_cibles = metadata.get("comptes_cibles", [])

# Comptes sans vidéos collectées
comptes_avec_videos = set(v.get("username", "") for v in videos)
comptes_sans_videos = [c for c in comptes_cibles if c not in comptes_avec_videos]

# Top 5 par nombre de vidéos
from collections import Counter
compte_video_counts = Counter(v.get("username", "") for v in videos)
top5 = [{"compte": c, "nb_videos": n} for c, n in compte_video_counts.most_common(5)]

# Vidéos
nb_total = len(videos)
durees = [v.get("video_duration", 0) for v in videos if v.get("video_duration")]
duree_moyenne = round(sum(durees) / len(durees), 1) if durees else 0

videos_avec_hashtags = sum(1 for v in videos if v.get("hashtag_names"))
videos_sans_hashtags = nb_total - videos_avec_hashtags

videos_sans_transcript = [v for v in videos if not (v.get("voice_to_text") or "").strip()]
pct_sans_transcript = round(len(videos_sans_transcript) / nb_total * 100, 1) if nb_total else 0

# Mots-clés
def contient_un_mot_cle(video):
    texte = " ".join(str(val) for val in video.values() if val).lower()
    return any(mc.lower() in texte for mc in MOTS_CLES)

videos_mc = [v for v in videos if contient_un_mot_cle(v)]
nb_mc = len(videos_mc)
pct_mc = round(nb_mc / nb_total * 100, 1) if nb_total else 0

videos_mc_sans_transcript = [v for v in videos_mc if not (v.get("voice_to_text") or "").strip()]
nb_mc_sans = len(videos_mc_sans_transcript)
nb_mc_avec = nb_mc - nb_mc_sans
pct_mc_sans = round(nb_mc_sans / nb_mc * 100, 1) if nb_mc else 0
pct_mc_avec = round(nb_mc_avec / nb_mc * 100, 1) if nb_mc else 0

# Engagement vidéos avec mots-clés
total_vues       = sum(v.get("view_count",    0) for v in videos_mc)
total_likes      = sum(v.get("like_count",    0) for v in videos_mc)
total_comments   = sum(v.get("comment_count", 0) for v in videos_mc)
total_partages   = sum(v.get("share_count",   0) for v in videos_mc)
vues_moyennes    = round(total_vues / nb_mc) if nb_mc else 0
ratio_engagement = round((total_likes + total_comments + total_partages) / total_vues * 100, 2) if total_vues else 0

# Détail par mot-clé
detail_par_mot_cle = {}
for mc in MOTS_CLES:
    videos_ce_mc = [
        v for v in videos
        if mc.lower() in " ".join(str(val) for val in v.values() if val).lower()
    ]
    nb = len(videos_ce_mc)
    sans_t = sum(1 for v in videos_ce_mc if not (v.get("voice_to_text") or "").strip())
    detail_par_mot_cle[mc] = {
        "nombre_videos": nb,
        "pourcentage_du_total": f"{round(nb / nb_total * 100, 1)}%" if nb_total else "0%",
        "sans_transcript": sans_t,
        "avec_transcript": nb - sans_t,
    }

# Construction du JSON de stats
stats = {
    "statistiques_collecte_tiktok": {
        "apercu_general": {
            "date_collecte": date_collecte,
            "periode_collecte": {
                "debut": date_debut_cfg,
                "fin":   date_fin_cfg,
                "duree_jours": duree_jours,
            },
            "periode_videos_reelles": {
                "video_la_plus_ancienne": video_la_plus_ancienne,
                "video_la_plus_recente":  video_la_plus_recente,
            },
            "version_api": metadata.get("version_api", "v2"),
        },
        "comptes": {
            "nombre_comptes_cibles": len(comptes_cibles),
            "comptes_sans_videos_collectees": comptes_sans_videos,
            "top5_comptes_par_nombre_videos": top5,
        },
        "videos": {
            "nombre_total_videos":  nb_total,
            "duree_moyenne_secondes": duree_moyenne,
            "videos_avec_hashtags": videos_avec_hashtags,
            "videos_sans_hashtags": videos_sans_hashtags,
            "videos_sans_transcript": {
                "total": len(videos_sans_transcript),
                "pourcentage": f"{pct_sans_transcript}%",
            },
        },
        "mots_cles": {
            "liste": MOTS_CLES,
            "logique": "OU — vidéo retenue si elle contient au moins un des mots-clés (tous champs confondus)",
            "nombre_videos_avec_au_moins_un_mot_cle": nb_mc,
            "pourcentage_du_total": f"{pct_mc}%",
            "sans_transcript": {
                "nombre": nb_mc_sans,
                "pourcentage_parmi_videos_mots_cles": f"{pct_mc_sans}%",
            },
            "avec_transcript": {
                "nombre": nb_mc_avec,
                "pourcentage_parmi_videos_mots_cles": f"{pct_mc_avec}%",
            },
            "detail_par_mot_cle": detail_par_mot_cle,
        },
        "engagement_videos_mots_cles": {
            "note": f"Calculé uniquement sur les {nb_mc} vidéos contenant au moins un mot-clé",
            "total_vues":          total_vues,
            "total_likes":         total_likes,
            "total_commentaires":  total_comments,
            "total_partages":      total_partages,
            "vues_moyennes_par_video": vues_moyennes,
            "ratio_engagement_par_vue": f"{ratio_engagement}%",
        },
    }
}

with open(CHEMIN_STATS, "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"Statistiques générées → {CHEMIN_STATS}")
print(f"Total vidéos          : {nb_total}")
print(f"Vidéos avec mots-clés : {nb_mc} ({pct_mc}%)")
for mc, d in detail_par_mot_cle.items():
    print(f"  '{mc}' : {d['nombre_videos']} vidéos")
