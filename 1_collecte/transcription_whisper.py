# Transcription automatique des vidéos TikTok via l'API OpenAI Whisper
#
# Dépend de :
#   - Le fichier JSON video_medias_mots_cles_v2.json (champ voice_to_text à compléter)
#   - Les fichiers vidéo téléchargés dans le dossier videos_medias/
#   - La librairie openai (pip install openai)
#   - La variable d'environnement OPENAI_API_KEY (export OPENAI_API_KEY='sk-...')
#
# Fonctionnement :
#   1. Lit le JSON source et identifie les vidéos dont voice_to_text est vide
#   2. Pour chaque vidéo, recherche le fichier .mp4 correspondant par son ID
#   3. Envoie le fichier à l'API Whisper (modèle whisper-1, langue fr)
#   4. Sauvegarde les transcriptions dans voice_to_text_whisper_output.json
#   5. Reprend là où il s'est arrêté si interrompu (résistant aux interruptions)
#
# Output :
#   Une liste JSON d'objets { id, username, url_video, voice_to_text }
#   à fusionner manuellement dans le JSON principal.

import json
import os
import sys
from pathlib import Path

# CONFIGURATION

# Chemin vers le JSON source contenant les vidéos à transcrire
CHEMIN_JSON_SOURCE = ''  # à compléter : JSON dont le champ voice_to_text est à compléter

# Dossier contenant les fichiers vidéo téléchargés
DOSSIER_VIDEOS = ''  # à compléter : dossier des vidéos (même dossier que la sortie de telechargement_videos.py)

# Fichier de sortie contenant les transcriptions générées
CHEMIN_OUTPUT = ''  # à compléter : JSON de sortie des transcriptions

# Taille maximale acceptée par l'API Whisper (en Mo)
TAILLE_MAX_MB = 25

# FONCTIONS

def charger_output_existant() -> dict:
    """Charge les transcriptions déjà effectuées (pour reprendre après interruption)."""
    chemin = Path(CHEMIN_OUTPUT)
    if chemin.exists():
        with open(chemin, encoding="utf-8") as f:
            data = json.load(f)
        return {str(item["id"]): item for item in data}
    return {}

def sauvegarder_output(resultats: dict) -> None:
    """Sauvegarde les transcriptions dans le fichier output."""
    with open(CHEMIN_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(list(resultats.values()), f, ensure_ascii=False, indent=2)

def trouver_fichier_video(video_id: str, dossier: Path) -> Path | None:
    """Recherche le fichier .mp4 correspondant à l'ID donné."""
    for fichier in dossier.glob("*.mp4"):
        if video_id in fichier.stem:
            return fichier
    return None

def estimer_cout(videos: list) -> tuple[int, float]:
    """Calcule la durée totale et le coût estimé de l'appel API."""
    total_secondes = sum(v.get("video_duration", 60) for v in videos)
    cout = (total_secondes / 60) * 0.006  # $0.006 par minute audio
    return total_secondes, cout

# PROGRAMME PRINCIPAL

def main():
    # Vérification des prérequis
    os.environ.setdefault("OPENAI_API_KEY", "") #insérer clé API OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERREUR : La variable d'environnement OPENAI_API_KEY n'est pas définie.")
        print("  Définissez-la avec : export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("ERREUR : La librairie openai n'est pas installée.")
        print("  Installez-la avec : pip install openai")
        sys.exit(1)

    chemin_json = Path(CHEMIN_JSON_SOURCE)
    if not chemin_json.exists():
        print(f"ERREUR : Fichier JSON introuvable : {CHEMIN_JSON_SOURCE}")
        sys.exit(1)

    dossier = Path(DOSSIER_VIDEOS)
    if not dossier.exists():
        print(f"ERREUR : Dossier vidéos introuvable : {DOSSIER_VIDEOS}")
        sys.exit(1)

    # Chargement du JSON et identification des vidéos à traiter
    with open(chemin_json, encoding="utf-8") as f:
        donnees = json.load(f)

    videos_a_traiter = [v for v in donnees["videos"] if not v.get("voice_to_text")]
    total = len(videos_a_traiter)

    # Chargement des transcriptions déjà effectuées
    resultats = charger_output_existant()
    deja_faits = sum(1 for v in videos_a_traiter if str(v["id"]) in resultats)

    # Estimation du coût
    non_encore_faits = [v for v in videos_a_traiter if str(v["id"]) not in resultats]
    total_secondes, cout_estime = estimer_cout(non_encore_faits)

    print("══════════════════════════════════════════════════════════════")
    print("  TRANSCRIPTION WHISPER — Résumé")
    print(f"  Vidéos sans voice_to_text : {total}")
    print(f"  Déjà transcrits (reprise) : {deja_faits}")
    print(f"  À transcrire              : {len(non_encore_faits)}")
    print(f"  Durée totale estimée      : {total_secondes / 60:.1f} minutes")
    print(f"  Coût API estimé           : ${cout_estime:.2f} USD")
    print("══════════════════════════════════════════════════════════════")

    if not non_encore_faits:
        print("  Toutes les vidéos sont déjà transcrites.")
        return

    confirmation = input("\n  Lancer la transcription ? (o/n) : ").strip().lower()
    if confirmation != "o":
        print("  Annulé.")
        return

    print()

    # Initialisation du client OpenAI
    client = OpenAI()

    # Boucle de transcription
    nb_succes  = 0
    nb_ignores = 0
    nb_erreurs = 0

    for idx, video in enumerate(videos_a_traiter, start=1):
        video_id = str(video["id"])
        username = video.get("username", "inconnu")

        # Déjà traité — reprise après interruption
        if video_id in resultats:
            print(f"[{idx}/{total}] {video_id} — déjà transcrit, ignoré")
            continue

        print(f"[{idx}/{total}] @{username} — ID {video_id}")

        # Recherche du fichier vidéo
        fichier = trouver_fichier_video(video_id, dossier)
        if not fichier:
            print(f"        → Fichier introuvable (slideshow ou vidéo non téléchargée), ignoré")
            nb_ignores += 1
            continue

        # Vérification de la taille
        taille_mb = fichier.stat().st_size / (1024 * 1024)
        if taille_mb > TAILLE_MAX_MB:
            print(f"        → Fichier trop grand ({taille_mb:.1f} Mo > {TAILLE_MAX_MB} Mo), ignoré")
            nb_ignores += 1
            continue

        # Appel à l'API Whisper
        try:
            with open(fichier, "rb") as f:
                reponse = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="fr"
                )

            transcription = reponse.text
            print(f"        → OK ({len(transcription)} caractères)")

            resultats[video_id] = {
                "id": video_id,
                "username": username,
                "url_video": video.get("url_video", ""),
                "voice_to_text": transcription
            }

            # Sauvegarde incrémentale après chaque transcription
            sauvegarder_output(resultats)
            nb_succes += 1

        except Exception as e:
            print(f"        → Erreur API : {e}")
            nb_erreurs += 1

    # Résumé final
    print()
    print("══════════════════════════════════════════════════════════════")
    print("  TRANSCRIPTION TERMINÉE")
    print(f"  Réussies  : {nb_succes}")
    print(f"  Ignorées  : {nb_ignores} (fichier manquant ou trop grand)")
    print(f"  Erreurs   : {nb_erreurs}")
    print(f"  Output    : {CHEMIN_OUTPUT}")
    print("══════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
