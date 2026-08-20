# -*- coding: utf-8 -*-
"""
Figure — Comptes ayant cumulé le plus de vues sur l'affaire.
Deux panneaux côte à côte : médias | personnalités politiques.
Barres horizontales décroissantes (le plus vu en haut).
"""

import json
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# PARAMÈTRES À AJUSTER
CHEMIN_CORPUS    = ""  # à compléter : corpus nettoyé (data/corpus_cleaned_v1.json)
TOP_N            = 30          # nombre de comptes affichés par panneau
COULEUR_BARRES   = "0.60"      # gris (0 = noir, 1 = blanc)
AFFICHER_VALEURS = True        # écrire la valeur au bout de chaque barre
FICHIER_SORTIE   = ""  # à compléter : image PNG de sortie

# CHARGEMENT ET SOMME DES VUES PAR COMPTE
with open(CHEMIN_CORPUS, encoding="utf-8") as f:
    data = json.load(f)
videos = data.get("videos", data)

def vues_par_compte(acteur):
    s = defaultdict(int)
    for v in videos:
        if v.get("acteur_type") == acteur:
            s[v["username"]] += v.get("view_count", 0) or 0
    return sorted(s.items(), key=lambda x: -x[1])[:TOP_N]

groupes = {"Médias": vues_par_compte("media"),
           "Personnalités et partis politiques": vues_par_compte("politicien")}

def abrege(x):
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f}".replace(".", ",") + " M"
    if x >= 1_000:
        return f"{round(x/1_000)} k"
    return str(int(x))

# TRACÉ
plt.rcParams.update({"font.family": "serif", "font.size": 11})
fig, axes = plt.subplots(1, 2, figsize=(12, 10))

for ax, (titre, top) in zip(axes, groupes.items()):
    comptes = ["@" + c for c, _ in top]
    valeurs = [n for _, n in top]
    y = range(len(top))
    ax.barh(y, valeurs, color=COULEUR_BARRES)
    ax.set_yticks(y)
    ax.set_yticklabels(comptes)
    ax.invert_yaxis()                          # le plus vu en haut
    ax.set_title(titre)
    ax.set_xlabel("Vues cumulées", labelpad=10)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: abrege(v)))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if AFFICHER_VALEURS:
        for i, v in enumerate(valeurs):
            ax.text(v + max(valeurs) * 0.01, i, abrege(v), va="center", fontsize=9)
    ax.margins(x=0.16)

fig.tight_layout(pad=1.5, w_pad=4)
fig.savefig(FICHIER_SORTIE, dpi=200, bbox_inches="tight")
print("Figure enregistrée :", FICHIER_SORTIE)
