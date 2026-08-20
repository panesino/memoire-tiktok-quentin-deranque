# Téléchargement des vidéos TikTok identifiées par collecte_tiktok_api.py

# Dépend de :
#   - Le fichier JSON contenant les références des vidéos d'intérêt
#   - La librairie Pyktok (pip install pyktok)

# Fonctionnement :
#   1. Lit le fichier .json contenant les infos sur les vidéos à télécharger
#   2. Parcourt la liste "videos"
#   3. Filtre selon MODE_FILTRE / LISTE_IDS_A_TELECHARGER
#   4. Télécharge chaque vidéo via Pyktok (cookies Chrome)
#   5. Nomme les fichiers DATE_USERNAME_VIDEOID.mp4
#   6. Tient un log CSV des téléchargements

import json
import csv
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# CONFIGURATION

# Chemin vers le fichier JSON contenant les références des vidéos d'intérêt
CHEMIN_JSON_SOURCE = ''  # à compléter : JSON des vidéos à télécharger (issu du filtrage)

# Dossier de destination pour les vidéos téléchargées
DOSSIER_VIDEOS = ''  # à compléter : dossier de destination des vidéos

# Navigateur pour l'export des cookies (Pyktok) — Chrome configuré par défaut
NAVIGATEUR = "chrome"     # Ne pas modifier sauf changement de navigateur

# 2 modes de filtrage possibles:
# False → télécharger TOUTES les vidéos présentes dans la liste "videos" du JSON
# True  → télécharger uniquement les vidéos dont les IDs sont dans LISTE_IDS_A_TELECHARGER
MODE_FILTRE = False

# IDs des vidéos à télécharger (utilisé uniquement si MODE_FILTRE = True)
# Ce sont les valeurs du champ "id" présentes dans le JSON produit par le Script 1
LISTE_IDS_A_TELECHARGER = [
    # À COMPLÉTER
]

# Délai en secondes entre chaque téléchargement (évite les blocages TikTok)
DELAI_ENTRE_TELECHARGEMENTS = 3

# CONSTANTES

# Fichier de log CSV (même dossier que le script)
CHEMIN_LOG_CSV = Path(__file__).parent / "telechargement_log.csv"

# En-têtes du fichier CSV de log
ENTETES_CSV = ["video_id", "username", "url", "statut", "chemin_fichier", "horodatage", "erreur"]

# Nombre de tentatives en cas d'échec réseau
NB_TENTATIVES = 1
DELAI_RESEAU  = 2   #secondes entre les tentatives réseau

# INITIALISATION DU LOG CSV

def initialiser_log_csv() -> None:
    """Crée le fichier CSV de log s'il n'existe pas encore."""
    if not CHEMIN_LOG_CSV.exists():
        with open(CHEMIN_LOG_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ENTETES_CSV)
            writer.writeheader()

def ajouter_ligne_log(video_id: str, username: str, url: str,
                      statut: str, chemin_fichier: str, erreur: str) -> None:
    """Ajoute une ligne au fichier CSV de log."""
    with open(CHEMIN_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ENTETES_CSV)
        writer.writerow({
            "video_id":      video_id,
            "username":      username,
            "url":           url,
            "statut":        statut,
            "chemin_fichier": chemin_fichier,
            "horodatage":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "erreur":        erreur,
        })

# TÉLÉCHARGEMENT D'UNE VIDÉO AVEC PYKTOK

def telecharger_video(url: str, username: str, video_id: str,
                      date_publication: str, dossier: Path) -> tuple[str, str, str]:
    """
    Télécharge une vidéo TikTok avec Pyktok.
    Retourne un tuple (statut, chemin_fichier, message_erreur) où :
      - statut peut être : "succes", "video_indisponible", "echec_reseau", "erreur_inconnue"
      - chemin_fichier : chemin absolu du fichier téléchargé, ou ""
      - message_erreur : description de l'erreur, ou ""
    """
    import pyktok as pyk

    # Pyktok sauvegarde toujours sous USERNAME_VIDEOID.mp4 dans le répertoire courant.
    # On se place dans le dossier cible, puis on renomme après téléchargement.
    chemin_pyktok = dossier / f"@{username}_video_{video_id}.mp4"
    chemin_final  = dossier / f"{date_publication}_{username}_{video_id}.mp4"

    # Tentatives réseau
    for tentative in range(1, NB_TENTATIVES + 2):  # +1 pour la tentative initiale
        try:
            cwd_original = os.getcwd()
            os.chdir(dossier)
            try:
                pyk.save_tiktok(url, True)
            finally:
                os.chdir(cwd_original)

            # Renommage vers DATE_USERNAME_VIDEOID.mp4
            if chemin_pyktok.exists() and chemin_pyktok.stat().st_size > 0:
                chemin_pyktok.rename(chemin_final)
                return "succes", str(chemin_final), ""
            elif chemin_final.exists() and chemin_final.stat().st_size > 0:
                return "succes", str(chemin_final), ""
            else:
                return "video_indisponible", "", "Fichier vide ou absent après téléchargement"

        except Exception as e:
            message = str(e).lower()

            # Détection vidéo supprimée / privée
            if any(mot in message for mot in ["private", "deleted", "removed", "not found",
                                               "unavailable", "404", "403"]):
                return "video_indisponible", "", str(e)

            # Détection possible CAPTCHA / détection bot
            if any(mot in message for mot in ["captcha", "robot", "blocked", "forbidden"]):
                print(f"          Signe de détection/CAPTCHA — augmentation du délai à 10s")
                time.sleep(10)
                return "echec_reseau", "", f"Détection probable : {e}"

            # Erreur réseau — réessayer si tentatives restantes
            if tentative <= NB_TENTATIVES:
                print(f"          Erreur réseau (tentative {tentative}/{NB_TENTATIVES}) — "
                      f"nouvelle tentative dans {DELAI_RESEAU}s...")
                time.sleep(DELAI_RESEAU)
                continue
            else:
                return "echec_reseau", "", str(e)

    return "erreur_inconnue", "", "Nombre maximum de tentatives atteint"

# PROGRAMME PRINCIPAL

def main():
    # Vérifications préalables
    if not CHEMIN_JSON_SOURCE:
        print("ERREUR : CHEMIN_JSON_SOURCE non défini dans la configuration.")
        sys.exit(1)

    if not DOSSIER_VIDEOS:
        print("ERREUR : DOSSIER_VIDEOS non défini dans la configuration.")
        sys.exit(1)

    chemin_json = Path(CHEMIN_JSON_SOURCE)
    if not chemin_json.exists():
        print(f"ERREUR : Fichier JSON introuvable : {CHEMIN_JSON_SOURCE}")
        sys.exit(1)

    # Vérification de Pyktok
    try:
        import pyktok as pyk
    except ImportError:
        print("ERREUR : Pyktok n'est pas installé.")
        print("Installez-le avec : pip install pyktok")
        sys.exit(1)

    # Configuration du navigateur pour les cookies
    pyk.specify_browser(NAVIGATEUR)

    # Chargement du JSON source
    with open(chemin_json, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    liste_videos = donnees.get("videos", [])

    if not liste_videos:
        print("Aucune vidéo trouvée dans le fichier JSON.")
        sys.exit(0)

    # Filtrage selon MODE_FILTRE
    if MODE_FILTRE:
        if not LISTE_IDS_A_TELECHARGER:
            print("ERREUR : MODE_FILTRE est True mais LISTE_IDS_A_TELECHARGER est vide.")
            sys.exit(1)
        ids_filtres = set(str(i) for i in LISTE_IDS_A_TELECHARGER)
        videos_a_traiter = [v for v in liste_videos if str(v.get("id", "")) in ids_filtres]
        print(f"[FILTRE] Mode filtré : {len(videos_a_traiter)} vidéos sélectionnées "
              f"sur {len(liste_videos)} dans le JSON.")
    else:
        videos_a_traiter = liste_videos

    total = len(videos_a_traiter)

    # Création du dossier de destination
    dossier = Path(DOSSIER_VIDEOS)
    dossier.mkdir(parents=True, exist_ok=True)

    # Détection des vidéos déjà téléchargées
    # Les fichiers sont nommés DATE_USERNAME_VIDEOID.mp4 : l'ID est le dernier segment
    ids_deja_telecharges = {
        f.stem.rsplit("_", 1)[-1]
        for f in dossier.glob("*.mp4")
    }
    if ids_deja_telecharges:
        print(f"[INFO] {len(ids_deja_telecharges)} vidéo(s) déjà présente(s) dans le dossier — ignorées.")

    # Initialisation du log CSV
    initialiser_log_csv()

    # En-tête d'affichage
    print("══════════════════════════════════════════════════════════════")
    print("  TÉLÉCHARGEMENT TIKTOK — Démarrage")
    print(f"  Source      : {CHEMIN_JSON_SOURCE}")
    print(f"  Destination : {DOSSIER_VIDEOS}")
    print(f"  Vidéos à télécharger : {total}")
    print("══════════════════════════════════════════════════════════════")
    print()

    # Boucle de téléchargement
    nb_succes  = 0
    nb_echecs  = 0
    nb_ignores = 0
    videos_echouees = []
    delai_actif = DELAI_ENTRE_TELECHARGEMENTS

    for idx, video in enumerate(videos_a_traiter, start=1):
        video_id  = str(video.get("id", ""))
        username  = video.get("username", "inconnu")
        url_video = video.get("url_video", "")

        create_time = video.get("create_time", 0)
        if create_time:
            date_publication = datetime.fromtimestamp(int(create_time)).strftime("%Y%m%d")
        else:
            date_publication = "00000000"

        if not url_video:
            # Reconstruction de l'URL si le champ est absent
            url_video = f"https://www.tiktok.com/@{username}/video/{video_id}"

        # Vérification doublon
        if video_id in ids_deja_telecharges:
            print(f"[{idx}/{total}] @{username} — ID {video_id} → déjà téléchargé, ignoré")
            nb_ignores += 1
            continue

        print(f"[{idx}/{total}] @{username} — ID {video_id}")
        print(f"        URL : {url_video}")

        statut, chemin_fichier, message_erreur = telecharger_video(
            url_video, username, video_id, date_publication, dossier
        )

        if statut == "succes":
            print(f"        →  Sauvegardé : {date_publication}_{username}_{video_id}.mp4")
            nb_succes += 1
        elif statut == "video_indisponible":
            print(f"        → Vidéo indisponible (supprimée ou privée) — passage à la suivante")
            nb_echecs += 1
            videos_echouees.append({"id": video_id, "username": username, "url": url_video, "raison": "indisponible"})
        elif statut == "echec_reseau":
            print(f"        → Échec réseau après {NB_TENTATIVES} tentatives — passage à la suivante")
            nb_echecs += 1
            videos_echouees.append({"id": video_id, "username": username, "url": url_video, "raison": "echec_reseau"})
        else:
            print(f"        → Erreur : {message_erreur} — passage à la suivante")
            nb_echecs += 1
            videos_echouees.append({"id": video_id, "username": username, "url": url_video, "raison": message_erreur})

        # Enregistrement dans le log
        ajouter_ligne_log(
            video_id=video_id,
            username=username,
            url=url_video,
            statut=statut,
            chemin_fichier=chemin_fichier,
            erreur=message_erreur,
        )

        # Délai entre les téléchargements (sauf après le dernier)
        if idx < total:
            time.sleep(delai_actif)

    # Résumé final
    print()
    print("══════════════════════════════════════════════════════════════")
    print("  TÉLÉCHARGEMENT TERMINÉ")
    print(f"  Réussies  : {nb_succes} / {total}")
    print(f"  Ignorées  : {nb_ignores} (déjà présentes)")
    print(f"  Échecs    : {nb_echecs} (détails dans telechargement_log.csv)")
    print(f"  Dossier   : {DOSSIER_VIDEOS}")
    print("══════════════════════════════════════════════════════════════")

    if videos_echouees:
        print()
        print("  VIDÉOS NON TÉLÉCHARGÉES — à récupérer par un autre moyen :")
        print("──────────────────────────────────────────────────────────────")
        for v in videos_echouees:
            print(f"  @{v['username']} | ID : {v['id']} | {v['raison']}")
            print(f"    {v['url']}")
        print("──────────────────────────────────────────────────────────────")

if __name__ == "__main__":
    main()
