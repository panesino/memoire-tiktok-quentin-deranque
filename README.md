# Une mort, plusieurs récit: cadrages de l'affaire Quentin Deranque sur TikTok

Ce dépôt rassemble le code et les données dérivées de mon mémoire de Master (Luca Panese, UNIL), consacré à l'analyse computationnelle de la circulation des cadres en lien avec l'affaire Quentin Deranque entre acteurs politiques et médias sur TikTok.

## Contenu

Le dépôt suit l'ordre du pipeline d'analyse.

- `1_collecte/`: sélection des comptes, collecte via la Research API de TikTok, filtrage thématique, téléchargement et transcription des vidéos.
- `2_traitement/`: fusion, nettoyage et normalisation du corpus, catégorisation des comptes par orientation.
- `3_clustering/`: notebook de clustering sémantique (embeddings, UMAP, HDBSCAN, c-TF-IDF) et consolidation en cadrages.
- `4_figures_statistiques/`: génération des figures et des statistiques descriptives.
- `data/`: corpus dérivé et fichiers nécessaires à la reproductibilité.
- `figures/`: figures finales du mémoire.

## Ordre d'exécution

1. `1_collecte/selection_comptes_medias.py`
2. `1_collecte/collecte_api_medias.py` et `1_collecte/collecte_api_politiciens.py`
3. `1_collecte/filtrage_mots_cles.py`
4. `1_collecte/telechargement_videos.py`
5. `1_collecte/transcription_whisper.py`
6. `2_traitement/fusion_corpus.py`
7. `2_traitement/nettoyage_corpus.py` (utilise `dictionnaire_corrections.py`)
8. `2_traitement/categorisation_comptes.py`
9. `3_clustering/clustering_bertopic.ipynb`
10. `4_figures_statistiques/` pour les figures et statistiques

## Données

Pour des raisons de taille, de respect des conditions d'utilisation de TikTok et de protection des données personnelles, les fichiers vidéos et le résultat brut de la collecte ne sont pas fournis.

- `corpus_cleaned_v1.json`: corpus nettoyé (701 vidéos, texte et métadonnées).
- `corpus_pret_clustering.csv`: corpus aligné pour le clustering (697 vidéos).
- `embeddings_Qwen3-8b.npy`: embeddings pré-calculés (697 × 4096).
- `etape1_affectations_canonique.csv`: affectation figée du document vers son cadrage.
- `consolidation_decisions.csv`: décisions de la revue qualitative (25 regroupements).
- `tableau_16_cadrages.csv`: table de présentation des 16 cadrages retenus.

## Reproductibilité

Le calcul des embeddings est coûteux et n'a été exécuté qu'une seule fois. Il est fourni comme artefact. Le notebook `3_clustering/clustering_bertopic.ipynb` se relance à partir de ce fichier, sans GPU, et reproduit la structure à 25 regroupements. Les chiffres présentés reposent sur l'affectation figée `etape1_affectations_canonique.csv`.

## Installation

```
pip install -r requirements.txt
```

## Identifiants

Les scripts de collecte requièrent des identifiants de la Research API de TikTok. Il faut donc renseigner vos identifiants dans `credentials.py`. La transcription requiert par ailleurs une clé OpenAI.
