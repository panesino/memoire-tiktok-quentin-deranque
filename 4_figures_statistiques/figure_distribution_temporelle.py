"""
Figure A — Distribution temporelle des publications sur l'affaire.
Deux panneaux côte à côte : médias | personnalités politiques.
Barres = nombre de vidéos publiées par jour ; courbe = moyenne mobile (lissage).
"""

import json
from collections import Counter
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt

# PARAMÈTRES À AJUSTER
CHEMIN_CORPUS   = ""  # à compléter : corpus nettoyé (data/corpus_cleaned_v1.json)
FENETRE_LISSAGE = 3          # moyenne mobile en jours (0 ou 1 = pas de courbe)
AXE_Y_PARTAGE   = False      # True = même échelle verticale pour les deux panneaux
COULEUR_BARRES  = "0.60"     # gris (0 = noir, 1 = blanc)
COULEUR_COURBE  = "black"
FICHIER_SORTIE  = ""  # à compléter : image PNG de sortie

# CHARGEMENT ET COMPTAGE PAR JOUR
with open(CHEMIN_CORPUS, encoding="utf-8") as f:
    data = json.load(f)
videos = data.get("videos", data)

def jour(v):
    return datetime.fromtimestamp(v["create_time"], tz=timezone.utc).date()

dates = [jour(v) for v in videos]
JOURS_APRES = 7   # jours vides ajoutés à droite pour que l'axe ne paraisse pas coupé
d_min, d_max = min(dates), max(dates)
jours = [d_min + timedelta(days=i) for i in range((d_max - d_min).days + 1 + JOURS_APRES)]

def serie(acteur):
    c = Counter(jour(v) for v in videos if v.get("acteur_type") == acteur)
    return [c.get(j, 0) for j in jours]

series = {"Médias": serie("media"),
          "Personnalités et partis politiques": serie("politicien")}

def moyenne_mobile(y, k):
    if k <= 1:
        return None
    out = []
    for i in range(len(y)):
        a, b = max(0, i - k // 2), min(len(y), i + k // 2 + 1)
        out.append(sum(y[a:b]) / (b - a))
    return out

# TRACÉ
MOIS = {2: "févr.", 3: "mars", 4: "avr."}
ticks = [j for j in jours if j.weekday() == 0]          # lundis
labels = [f"{j.day:02d} {MOIS[j.month]}" for j in ticks]

plt.rcParams.update({"font.family": "serif", "font.size": 11})
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=AXE_Y_PARTAGE)

for ax, (titre, y) in zip(axes, series.items()):
    ax.bar(jours, y, width=0.9, color=COULEUR_BARRES, label="Nb publications / jour")
    mm = moyenne_mobile(y, FENETRE_LISSAGE)
    if mm:
        ax.plot(jours, mm, color=COULEUR_COURBE, linewidth=1.6,
                label=f"Moyenne mobile ({FENETRE_LISSAGE} j)")
    ax.set_title(titre)
    ax.set_xlabel("Date de publication", labelpad=12)
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.margins(x=0.01)
    ax.legend(frameon=False, fontsize=9)

axes[0].set_ylabel("Nombre de vidéos publiées", labelpad=12)
fig.tight_layout(pad=1.5, w_pad=3)
fig.savefig(FICHIER_SORTIE, dpi=200, bbox_inches="tight")
print("Figure enregistrée :", FICHIER_SORTIE)
