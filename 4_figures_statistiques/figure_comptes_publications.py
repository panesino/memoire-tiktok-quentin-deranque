# -*- coding: utf-8 -*-
"""
Figure — Comptes ayant le plus publié sur l'affaire.
Deux panneaux côte à côte : médias | personnalités politiques.
Barres horizontales décroissantes (le plus actif en haut).
"""

import json
from collections import Counter
import matplotlib.pyplot as plt

# PARAMÈTRES À AJUSTER
CHEMIN_CORPUS     = ""  # à compléter : corpus nettoyé (data/corpus_cleaned_v1.json)
TOP_N             = 30          # nombre de comptes affichés par panneau
COULEUR_BARRES    = "0.60"      # gris (0 = noir, 1 = blanc)
AFFICHER_VALEURS  = True        # écrire le nombre au bout de chaque barre
FICHIER_SORTIE    = ""  # à compléter : image PNG de sortie

# CHARGEMENT ET COMPTAGE PAR COMPTE
with open(CHEMIN_CORPUS, encoding="utf-8") as f:
    data = json.load(f)
videos = data.get("videos", data)

def compter(acteur):
    c = Counter(v["username"] for v in videos if v.get("acteur_type") == acteur)
    return c.most_common(TOP_N)

groupes = {"Médias": compter("media"),
           "Personnalités et partis politiques": compter("politicien")}

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
    ax.invert_yaxis()                      # le plus actif en haut
    ax.set_title(titre)
    ax.set_xlabel("Nombre de vidéos publiées", labelpad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if AFFICHER_VALEURS:
        for i, v in enumerate(valeurs):
            ax.text(v + max(valeurs) * 0.01, i, str(v), va="center", fontsize=9)
    ax.margins(x=0.12)                      # un peu d'air à droite pour les valeurs

fig.tight_layout(pad=1.5, w_pad=4)
fig.savefig(FICHIER_SORTIE, dpi=200, bbox_inches="tight")
print("Figure enregistrée :", FICHIER_SORTIE)
