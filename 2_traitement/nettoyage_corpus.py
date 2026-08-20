"""
Script de nettoyage du corpus TikTok mergé.

INPUT  : corpus_merged_v1.json
OUTPUT : corpus_cleaned_v1.json (avec clés _clean ajoutées)

Pour chaque vidéo, ajoute 4 nouvelles clés :
  - video_description_clean
  - voice_to_text_clean
  - hashtag_names_clean   (string concaténée)
  - texte_final_clean           (concaténation finale prête pour embedding)

Les clés originales sont CONSERVÉES pour traçabilité.

Usage :
    python clean_corpus.py
    python clean_corpus.py --inspect    # mode inspection : montre 10 exemples avant/après sans sauvegarder
"""

import json
import re
import sys
import argparse
from pathlib import Path

# Import du dictionnaire de corrections
from corrections_dict import (
    NAMED_ENTITIES_CORRECTIONS,
    ARTIFACTS_REGEX,
    ORAL_HESITATIONS,
    URL_PATTERN,
    EMOJI_PATTERN,
    INVISIBLE_PATTERN,
)

# FONCTIONS DE NETTOYAGE MODULAIRES

def remove_urls(text: str) -> str:
    """Retire les URLs du texte."""
    return re.sub(URL_PATTERN, ' ', text)

def remove_emojis(text: str) -> str:
    """Retire les emojis du texte."""
    return re.sub(EMOJI_PATTERN, ' ', text)

def remove_invisible(text: str) -> str:
    """Retire les caractères Unicode invisibles."""
    return re.sub(INVISIBLE_PATTERN, '', text)

def correct_named_entities(text: str) -> str:
    """Corrige les noms propres mal transcrits selon le dictionnaire."""
    for variante, canonique in NAMED_ENTITIES_CORRECTIONS.items():
        # word boundaries + insensible à la casse
        pattern = r'\b' + re.escape(variante) + r'\b'
        text = re.sub(pattern, canonique, text, flags=re.IGNORECASE)
    return text

def correct_artifacts(text: str) -> str:
    """Applique les corrections d'artefacts (chiffres isolés, etc.)."""
    for pattern, replacement in ARTIFACTS_REGEX:
        text = re.sub(pattern, replacement, text)
    return text

def remove_oral_hesitations(text: str) -> str:
    """
    Retire les hésitations orales si configurées.
    Gère proprement les virgules orphelines laissées par le retrait
    (ex : "j'ai, euh, dit" → "j'ai dit" et non "j'ai, , dit").
    """
    for h in ORAL_HESITATIONS:
        # Cas 1 : hésitation entourée de virgules (le plus fréquent)
        # "j'ai, euh, dit" → "j'ai dit"
        pattern_commas = r',\s*\b' + re.escape(h) + r'\b\s*,'
        text = re.sub(pattern_commas, ',', text, flags=re.IGNORECASE)

        # Cas 2 : hésitation simple, retrait standard
        pattern_simple = r'\b' + re.escape(h) + r'\b'
        text = re.sub(pattern_simple, '', text, flags=re.IGNORECASE)

    # Nettoyage des virgules doublées éventuelles : ", ," → ","
    text = re.sub(r',\s*,', ',', text)
    return text

def normalize_whitespace(text: str) -> str:
    """Normalise les espaces multiples et trim."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# FONCTIONS DE NETTOYAGE PAR CHAMP

def clean_description(text: str) -> str:
    """
    Nettoie une description de vidéo TikTok.
    Pipeline : URLs → emojis → invisibles → noms propres → artefacts → espaces.
    """
    if not text or not isinstance(text, str):
        return ""

    text = remove_urls(text)
    text = remove_emojis(text)
    text = remove_invisible(text)
    text = correct_named_entities(text)
    text = correct_artifacts(text)
    text = normalize_whitespace(text)
    return text

def clean_voice_to_text(text: str) -> str:
    """
    Nettoie une transcription orale (voice_to_text).
    Pipeline : URLs (rare) → invisibles → noms propres → artefacts → hésitations → espaces.
    Pas de suppression d'emojis car peu présents dans les transcriptions audio.
    """
    if not text or not isinstance(text, str):
        return ""

    text = remove_urls(text)
    text = remove_invisible(text)
    text = correct_named_entities(text)
    text = correct_artifacts(text)
    text = remove_oral_hesitations(text)
    text = normalize_whitespace(text)
    return text

def clean_hashtags(hashtag_list) -> str:
    """
    Transforme une liste de hashtags en chaîne concaténée.
    Retire le # initial s'il existe, joint avec espaces.
    Retourne une chaîne vide si la liste est vide ou invalide.
    """
    if not hashtag_list or not isinstance(hashtag_list, list):
        return ""

    cleaned = []
    for tag in hashtag_list:
        if not isinstance(tag, str):
            continue
        # Retire le # initial s'il existe (l'API TikTok renvoie souvent sans, mais on sécurise)
        tag = tag.lstrip('#').strip()
        if tag:
            cleaned.append(tag)

    return ' '.join(cleaned)

def construire_texte_clean(desc_clean: str, v2t_clean: str, hashtags_clean: str) -> str:
    """
    Concatène les trois champs nettoyés dans l'ordre :
        description . voice_to_text . hashtags
    Avec un point + saut de ligne comme séparateur sémantique entre desc et v2t.
    Les hashtags sont ajoutés à la fin séparés par un point.

    Logique : on inclut uniquement les champs non vides.
    """
    parts = []

    if desc_clean:
        parts.append(desc_clean)

    if v2t_clean:
        parts.append(v2t_clean)

    if hashtags_clean:
        parts.append(hashtags_clean)

    if not parts:
        return ""

    # Séparateur : ". \n" entre les blocs principaux
    return ".\n".join(parts)

# PIPELINE PRINCIPAL

def process_video(video: dict) -> dict:
    """
    Enrichit une vidéo avec les 4 clés _clean en conservant les originales.
    Retourne le dict modifié (modification in-place + return pour chaînage).
    """
    desc_raw = video.get('video_description', '') or ''
    v2t_raw = video.get('voice_to_text', '') or ''
    hashtags_raw = video.get('hashtag_names', []) or []

    desc_clean = clean_description(desc_raw)
    v2t_clean = clean_voice_to_text(v2t_raw)
    hashtags_clean = clean_hashtags(hashtags_raw)

    video['video_description_clean'] = desc_clean
    video['voice_to_text_clean'] = v2t_clean
    video['hashtag_names_clean'] = hashtags_clean
    video['texte_clean'] = construire_texte_clean(desc_clean, v2t_clean, hashtags_clean)

    return video

def process_corpus(input_path: Path, output_path: Path, inspect: bool = False, n_inspect: int = 10):
    """
    Charge le corpus mergé, applique le nettoyage, sauvegarde le résultat.

    Si inspect=True : ne sauvegarde rien, affiche n_inspect exemples avant/après.
    """
    print(f"Chargement de {input_path}...")
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    videos = data['videos']
    n_total = len(videos)
    print(f"  {n_total} vidéos à traiter\n")

    if inspect:
        # Mode inspection : on traite mais on n'écrase pas les originales pour comparaison
        import random
        random.seed(42)
        sample_indices = random.sample(range(n_total), min(n_inspect, n_total))

        for idx in sample_indices:
            v = videos[idx]
            desc_raw = v.get('video_description', '') or ''
            v2t_raw = v.get('voice_to_text', '') or ''
            hashtags_raw = v.get('hashtag_names', []) or []

            desc_c = clean_description(desc_raw)
            v2t_c = clean_voice_to_text(v2t_raw)
            hashtags_c = clean_hashtags(hashtags_raw)
            texte_c = construire_texte_clean(desc_c, v2t_c, hashtags_c)

            print(f"{'='*70}")
            print(f"Vidéo #{idx} — @{v['username']} ({v['acteur_type']})")
            print(f"{'='*70}")

            print(f"\n>>> DESCRIPTION ORIGINALE :")
            print(f"    {desc_raw[:300]}")
            print(f"\n>>> DESCRIPTION CLEAN :")
            print(f"    {desc_c[:300]}")

            print(f"\n>>> VOICE_TO_TEXT ORIGINAL :")
            print(f"    {v2t_raw[:300]}")
            print(f"\n>>> VOICE_TO_TEXT CLEAN :")
            print(f"    {v2t_c[:300]}")

            print(f"\n>>> HASHTAGS ORIGINAUX : {hashtags_raw}")
            print(f">>> HASHTAGS CLEAN     : {hashtags_c}")

            print(f"\n>>> TEXTE_CLEAN FINAL ({len(texte_c.split())} mots) :")
            print(f"    {texte_c[:500]}")
            print()

        return

    # Mode production : on traite tout et on sauvegarde
    for i, video in enumerate(videos):
        process_video(video)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n_total} vidéos traitées...")

    print(f"  {n_total}/{n_total} vidéos traitées.\n")

    # Statistiques de qualité
    n_texte_vide = sum(1 for v in videos if not v['texte_clean'].strip())
    nb_mots = [len(v['texte_clean'].split()) for v in videos]
    nb_mots_sorted = sorted(nb_mots)
    median = nb_mots_sorted[len(nb_mots_sorted) // 2]

    print("=== STATISTIQUES POST-NETTOYAGE ===")
    print(f"Vidéos avec texte_clean vide : {n_texte_vide}")
    print(f"Médiane mots (texte_clean)   : {median}")
    print(f"Min / Max mots               : {min(nb_mots)} / {max(nb_mots)}")
    print(f"Vidéos < 30 mots             : {sum(1 for n in nb_mots if n < 30)}")
    print(f"Vidéos >= 30 mots            : {sum(1 for n in nb_mots if n >= 30)}\n")

    # Mise à jour des métadonnées
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['cleaning_applied'] = True
    data['metadata']['cleaning_version'] = 'v1'
    data['metadata']['n_corrections_named_entities'] = len(NAMED_ENTITIES_CORRECTIONS)
    data['metadata']['n_artifacts_patterns'] = len(ARTIFACTS_REGEX)

    print(f"Sauvegarde dans {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Fichier sauvegardé ({output_path.stat().st_size / 1024:.0f} Ko)")

# CLI

def main():
    parser = argparse.ArgumentParser(description="Nettoyage du corpus TikTok mergé.")
    parser.add_argument(
        '--input', type=Path,
        default=Path('corpus_merged_v1.json'),
        help='Fichier JSON d\'entrée (défaut : corpus_merged_v1.json)'
    )
    parser.add_argument(
        '--output', type=Path,
        default=Path('corpus_cleaned_v1.json'),
        help='Fichier JSON de sortie (défaut : corpus_cleaned_v1.json)'
    )
    parser.add_argument(
        '--inspect', action='store_true',
        help='Mode inspection : affiche des exemples avant/après sans sauvegarder'
    )
    parser.add_argument(
        '--n-inspect', type=int, default=10,
        help='Nombre d\'exemples à afficher en mode inspect (défaut : 10)'
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERREUR : fichier {args.input} introuvable.")
        sys.exit(1)

    process_corpus(args.input, args.output, inspect=args.inspect, n_inspect=args.n_inspect)

if __name__ == '__main__':
    main()
