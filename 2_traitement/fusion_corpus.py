# Fusion des corpus filtrés (médias et politiques) en un corpus unique.

import json
from datetime import datetime

# Chargement
with open('', encoding='utf-8') as f:  # à compléter : corpus politiques filtré en entrée
    pol = json.load(f)
with open('', encoding='utf-8') as f:  # à compléter : corpus médias filtré en entrée
    med = json.load(f)

# Vérifications de cohérence avant merge
assert all('acteur_type' in v for v in pol['videos']), "acteur_type manquant dans politiciens"
assert all('acteur_type' in v for v in med['videos']), "acteur_type manquant dans medias"
assert all(v['acteur_type'] == 'politicien' for v in pol['videos']), "acteur_type incohérent (politiciens)"
assert all(v['acteur_type'] == 'media' for v in med['videos']), "acteur_type incohérent (medias)"

# Vérification absence de doublons d'ID entre les deux corpus
ids_pol = {v['id'] for v in pol['videos']}
ids_med = {v['id'] for v in med['videos']}
overlap = ids_pol & ids_med
if overlap:
    print(f"ATTENTION : {len(overlap)} doublons entre politiciens et médias")
else:
    print(f"OK : aucun doublon d'ID entre les deux fichiers")

# Construction du fichier mergé
merged = {
    "metadata": {
        "politiciens": pol['metadata'],
        "medias": med['metadata'],
        "merge_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_videos": len(pol['videos']) + len(med['videos']),
        "n_politiciens": len(pol['videos']),
        "n_medias": len(med['videos'])
    },
    "videos": pol['videos'] + med['videos']
}

# Sauvegarde
with open('', 'w', encoding='utf-8') as f:  # à compléter : corpus fusionné en sortie
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f"\nFusion terminée : {merged['metadata']['total_videos']} vidéos")
print(f"  - Politiciens : {merged['metadata']['n_politiciens']}")
print(f"  - Médias : {merged['metadata']['n_medias']}")
