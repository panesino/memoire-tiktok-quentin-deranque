# Collecte des vidéos des comptes de médias via la Research API de TikTok.

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Credentials
from credentials import CLIENT_KEY, CLIENT_SECRET

# Comptes TikTok
COMPTES_CIBLES = [
    "lhumanitefr",
    "lemediatv",
    "mediapartfr",
    "blast_officiel",
    "quotidienofficiel",
    "20minutesfrance",
    "afpfr",
    "c_a_vous",
    "france24",
    "france.inter",
    "lcp_an",
    "lemondefr",
    "nouvelobs",
    "lehuffpostfr",
    "mariannelemag",
    "publicsenat",
    "rfi",
    "rtl.officiel",
    "rtlinfo",
    "tv5monde",
    "franceinfo",
    "m6info_",
    "liberation.fr",
    "bfmtv",
    "cnews",
    "europe1",
    "lexpress",
    "le_progres_",
    "lefigaro",
    "leparisien",
    "lepointfr",
    "lesechos.fr",
    "rmc_off",
    "sudradio",
    "tf1info",
    "va.plus",
    "laradionova",
    "franctireurmag",
    "t18_officiel",
    "loopsider",
    "brutofficiel",
    "laprovence_",
    "ledauphinelibere",
    "lepopulaire.fr",
    "journalsudouest",
    "ladepechedumidi",
    "slatefr",
    "artefr",
    "franceculture",
    "parismatch",
    "vakitamedia",
    "i24news_fr",
    "lejddfr",
    "latribune",
    "hugodecrypte",
    "konbini",
    "clique_tv",
    "streetpress_",
    "le20hfrancetelevisions",
    "tbt9_w9",

]

# Période de collecte
DATE_DEBUT = "20260209"   # 9 février 2026, J-3 avant mort de QD
DATE_FIN   = ""           # Laisser vide -> automatiquement remplacé par la date du jour

# Chemin de sortie du fichier JSON unique de résultats
CHEMIN_SORTIE_JSON = ""  # à compléter : JSON de sortie de la collecte médias

# Données constantes
BASE_URL_VIDEOS  = "https://open.tiktokapis.com/v2/research/video/query/"
BASE_URL_PROFIL  = "https://open.tiktokapis.com/v2/research/user/info/"
BASE_URL_TOKEN   = "https://open.tiktokapis.com/v2/oauth/token/"
MAX_COUNT        = 100
DUREE_TOKEN_SEC  = 7200  #car token TikTok expire après 2h

# Chemin du fichier d'état pour la reprise après quota épuisé
# (même dossier que le script)
CHEMIN_ETAT = Path(__file__).parent / "collecte_tiktok_etat.json"

# Champs vidéo à collecter (liste exhaustive)
CHAMPS_VIDEOS = ",".join([
    "id", "create_time", "username", "region_code",
    "video_description", "music_id",
    "like_count", "comment_count", "share_count", "view_count",
    "hashtag_names", "video_duration",
    "effect_ids", "playlist_id", "voice_to_text",
    "is_stem_verified", "video_mention_list", "video_label",
])

# Champs de profil à collecter (validés Research API)
CHAMPS_PROFIL = ",".join([
    "follower_count", "likes_count", "video_count",
])

# GESTION DU TOKEN — repris et étendu depuis collect_videos.py

# Variable globale pour le token et son horodatage d'obtention
_token_valeur    = None
_token_obtenu_a  = None

def get_access_token() -> str:
    """
    Obtient un nouveau token d'accès via client_credentials.
    Reproduit fidèlement la fonction get_access_token() du script d'exemple.
    """
    r = requests.post(
        BASE_URL_TOKEN,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        },
        data={
            "client_key":    CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "grant_type":    "client_credentials",
        },
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise ValueError(f"Token non reçu : {r.json()}")
    return token

def obtenir_token_valide() -> str:
    """
    Retourne un token valide. Si le token courant est absent ou proche
    de l'expiration (<60s restantes), en obtient un nouveau.
    """
    global _token_valeur, _token_obtenu_a

    maintenant = time.time()
    token_expire = (
        _token_valeur is None
        or _token_obtenu_a is None
        or (maintenant - _token_obtenu_a) >= (DUREE_TOKEN_SEC - 60)
    )

    if token_expire:
        if _token_valeur is not None:
            print("[TOKEN] Token expiré — renouvellement en cours...")
        _token_valeur   = get_access_token()
        _token_obtenu_a = maintenant
        if _token_valeur:
            print("[TOKEN] Nouveau token obtenu avec succès.")

    return _token_valeur

# FENÊTRAGE DES DATES — repris depuis script d'ex de Caroline (collect_videos.py)

def date_windows(debut: str, fin: str, jours_max: int = 30):
    """
    Découpe une plage de dates en fenêtres de jours_max jours maximum.
    Format attendu : YYYYMMDD
    """
    fmt = "%Y%m%d"
    cur = datetime.strptime(debut, fmt)
    end = datetime.strptime(fin, fmt)
    while cur <= end:
        nxt = min(cur + timedelta(days=jours_max - 1), end)
        yield cur.strftime("%Y%m%d"), nxt.strftime("%Y%m%d")
        cur = nxt + timedelta(days=1)

# COLLECTE DU PROFIL UTILISATEUR

def collecter_profil(username: str) -> dict:
    """
    Récupère les informations de profil d'un compte via /v2/research/user/info/.
    Retourne un dict avec les champs de profil ou un dict vide en cas d'erreur.
    """
    token = obtenir_token_valide()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    try:
        r = requests.post(
            BASE_URL_PROFIL,
            params={"fields": CHAMPS_PROFIL},
            json={"username": username},
            headers=headers,
            timeout=10,
        )
        if not r.ok:
            print(f"  → Erreur profil @{username} : HTTP {r.status_code}")
            return {}
        data = r.json()
        if data.get("error", {}).get("code") != "ok":
            print(f"  → Erreur API profil @{username} : {data.get('error')}")
            return {}
        return data.get("data", {})
    except Exception as e:
        print(f"  → Exception lors de la collecte du profil @{username} : {e}")
        return {}

# PAGINATION ET COLLECTE DES VIDÉOS — repris et étendu depuis collect_videos.py

def collecter_fenetre(username: str, debut: str, fin: str,
                      curseur_initial: int = 0,
                      search_id_initial: str = "") -> tuple[list[dict], str]:
    """
    Collecte toutes les vidéos d'un compte sur une fenêtre de 30 jours.
    Gère la pagination cursor/search_id.
    Repris de fetch_window() du script d'exemple.
    Retourne (liste_videos, "QUOTA_EPUISE") si le quota est atteint,
    sinon (liste_videos, "OK").
    """
    url = f"{BASE_URL_VIDEOS}?fields={CHAMPS_VIDEOS}"

    videos    = []
    cursor    = curseur_initial
    has_more  = True
    search_id = search_id_initial
    page      = 1

    while has_more:
        token = obtenir_token_valide()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        }

        body = {
            "query": {
                "and": [
                    {
                        "operation":    "EQ",
                        "field_name":   "username",
                        "field_values": [username],
                    }
                ]
            },
            "start_date": debut,
            "end_date":   fin,
            "max_count":  MAX_COUNT,
            "cursor":     cursor,
        }

        # search_id omis sur la première requête d'une fenêtre, inclus sur toutes les suivantes
        if search_id:
            body["search_id"] = search_id

        r = requests.post(url, headers=headers, data=json.dumps(body))

        # Gestion du quota journalier (429 ou code erreur spécifique)
        if r.status_code == 429:
            return videos, "QUOTA_EPUISE"

        if not r.ok:
            print(f"  → HTTP {r.status_code} pour @{username} fenêtre {debut}→{fin} : {r.text}")
            break

        data = r.json()
        erreur = data.get("error", {})

        # Certaines réponses quota-épuisé retournent un code spécifique
        if erreur.get("code") not in ("ok", None, ""):
            code_erreur = erreur.get("code", "")
            if "quota" in code_erreur.lower() or "rate" in code_erreur.lower():
                return videos, "QUOTA_EPUISE"
            print(f"  → Erreur API : {erreur}")
            break

        batch     = data.get("data", {}).get("videos", [])
        has_more  = data.get("data", {}).get("has_more", False)
        cursor    = data.get("data", {}).get("cursor", 0)
        search_id = data.get("data", {}).get("search_id", "")

        videos.extend(batch)

        print(f"    [PAGINATION] @{username} | fenêtre {debut}→{fin} | "
              f"page {page} | {len(videos)} vidéos récupérées jusqu'ici")

        page += 1
        time.sleep(1)  # Délai entre les pages

    return videos, "OK"

# SAUVEGARDE ET REPRISE DE L'ÉTAT

def sauvegarder_etat(compte_en_cours: str, fenetre_debut: str, fenetre_fin: str,
                     cursor: int, search_id: str, videos_collectees: list[dict]) -> None:
    """Sauvegarde l'état courant de la collecte pour reprise ultérieure."""
    etat = {
        "compte_en_cours":  compte_en_cours,
        "fenetre_debut":    fenetre_debut,
        "fenetre_fin":      fenetre_fin,
        "cursor":           cursor,
        "search_id":        search_id,
        "horodatage":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "videos_collectees": videos_collectees,
    }
    with open(CHEMIN_ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=2)

def charger_etat() -> dict | None:
    """Charge le fichier d'état si présent, retourne None sinon."""
    if not CHEMIN_ETAT.exists():
        return None
    try:
        with open(CHEMIN_ETAT, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def supprimer_etat() -> None:
    """Supprime le fichier d'état une fois la collecte terminée avec succès."""
    if CHEMIN_ETAT.exists():
        CHEMIN_ETAT.unlink()

# CHARGEMENT DU JSON EXISTANT

def charger_json_existant() -> tuple[list[dict], str | None]:
    """
    Charge le fichier JSON existant.
    Retourne (liste_videos, date_fin_precedente) ou ([], None) si absent.
    """
    chemin = Path(CHEMIN_SORTIE_JSON)
    if not chemin.exists():
        return [], None
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
        videos   = data.get("videos", [])
        date_fin = data.get("metadata", {}).get("date_fin_periode")
        print(f"[JSON EXISTANT] {len(videos)} vidéos chargées — dernière collecte jusqu'au {date_fin}")
        return videos, date_fin
    except Exception as e:
        print(f"[JSON EXISTANT] Erreur de lecture : {e} — collecte depuis zéro")
        return [], None

# SAUVEGARDE DU RÉSULTAT FINAL

def sauvegarder_json(videos: list[dict], date_debut: str, date_fin: str) -> None:
    """Sauvegarde le fichier JSON final de résultats."""
    if not CHEMIN_SORTIE_JSON:
        print("CHEMIN_SORTIE_JSON non défini — le fichier JSON ne sera pas sauvegardé.")
        return

    sortie = {
        "metadata": {
            "date_collecte":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_debut_periode":  date_debut,
            "date_fin_periode":    date_fin,
            "comptes_cibles":      COMPTES_CIBLES,
            "nombre_total_videos": len(videos),
            "version_api":         "v2",
        },
        "videos": videos,
    }

    chemin = Path(CHEMIN_SORTIE_JSON)
    chemin.parent.mkdir(parents=True, exist_ok=True)

    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)

    print(f"\n  Fichier JSON sauvegardé : {CHEMIN_SORTIE_JSON}")

# AFFICHAGE DU MESSAGE DE QUOTA ÉPUISÉ

def afficher_message_quota(videos_collectees: list[dict], compte: str,
                            fenetre_debut: str, fenetre_fin: str) -> None:
    """Affiche le message formaté de quota épuisé."""
    nb = len(videos_collectees)
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║             QUOTA JOURNALIER API TIKTOK ÉPUISÉ                   ║
╠══════════════════════════════════════════════════════════════════╣
║  Le quota de 1 000 requêtes/jour a été atteint.                  ║
║                                                                  ║
║  État de la collecte sauvegardé dans :                           ║
║  → collecte_tiktok_etat.json                                     ║
║                                                                  ║
║  Vidéos collectées jusqu'ici : {str(nb).ljust(34)}║
║  Dernier compte traité       : @{str(compte).ljust(33)}║
║  Dernière fenêtre            : {(fenetre_debut + ' → ' + fenetre_fin).ljust(34)}║
║                                                                  ║
║  Le quota se renouvelle à 01:00 AM (Genève)                      ║
║                                                                  ║
║   POUR REPRENDRE LA COLLECTE :                                   ║
║     Relancez simplement le script avec la même commande.         ║
║     Il reprendra automatiquement où il s'est arrêté.             ║
╚══════════════════════════════════════════════════════════════════╝""")

# PROGRAMME PRINCIPAL

def main():
    # Calcul automatique de DATE_FIN si vide
    date_fin_effective = DATE_FIN
    if not date_fin_effective:
        date_fin_effective = datetime.now().strftime("%Y%m%d")
        print(f"[CONFIG] DATE_FIN non définie — utilisation de la date du jour : {date_fin_effective}")

    # Chargement du JSON existant
    videos_existantes, date_fin_precedente = charger_json_existant()
    ids_existants = {v["id"] for v in videos_existantes if v.get("id")}

    # Comptes ayant déjà au moins une vidéo dans le JSON
    comptes_avec_videos = {v["username"] for v in videos_existantes if v.get("username")}

    # Date de début effective : reprendre depuis la dernière collecte
    date_debut_effective = DATE_DEBUT
    if date_fin_precedente and date_fin_precedente >= DATE_DEBUT:
        date_debut_effective = date_fin_precedente  # chevauche d'1 jour pour sécurité
        print(f"[INCRÉMENTAL] Collecte depuis le {date_debut_effective} pour les comptes déjà collectés")
        comptes_absents = [c for c in COMPTES_CIBLES if c not in comptes_avec_videos]
        if comptes_absents:
            print(f"[INCRÉMENTAL] {len(comptes_absents)} compte(s) jamais collecté(s) → collecte depuis {DATE_DEBUT} : "
                  f"{', '.join('@' + c for c in comptes_absents)}")
    else:
        print(f"[INCRÉMENTAL] Aucun JSON existant — collecte depuis {DATE_DEBUT}")

    # Vérifications préalables
    if not COMPTES_CIBLES:
        print("ERREUR : COMPTES_CIBLES est vide. Ajoutez au moins un compte dans la configuration.")
        sys.exit(1)

    # Chargement de l'état de reprise éventuel
    etat = charger_etat()
    videos_globales: list[dict] = []
    reprise_compte        = None
    reprise_fenetre_debut = None

    if etat:
        # Le JSON intermédiaire a déjà été sauvegardé lors du quota épuisé.
        # On repart d'une collecte incrémentale fraîche pour TOUS les comptes.
        # On conserve uniquement le compte interrompu et sa fenêtre de début pour
        # re-couvrir les vidéos manquées en milieu de pagination (le search_id
        # TikTok expire rapidement, on ne réutilise pas le curseur).
        reprise_compte        = etat.get("compte_en_cours")
        reprise_fenetre_debut = etat.get("fenetre_debut")
        print(f"[REPRISE] Fichier d'état détecté.")
        print(f"[REPRISE] Les résultats partiels de la session précédente sont dans le JSON existant.")
        if reprise_compte and reprise_fenetre_debut:
            print(f"[REPRISE] @{reprise_compte} était interrompu sur la fenêtre débutant le "
                  f"{reprise_fenetre_debut} — re-collecte depuis cette date.")
        supprimer_etat()
        print()

    # En-tête de démarrage
    print("  COLLECTE TIKTOK — Démarrage")
    print(f"  Période      : {DATE_DEBUT} → {date_fin_effective}")
    print(f"  Comptes      : {len(COMPTES_CIBLES)} comptes cibles")
    print("  Commentaires : désactivés (préservation du quota)")
    print()

    # Obtention du premier token
    obtenir_token_valide()

    # Boucle principale sur les comptes
    for idx, username in enumerate(COMPTES_CIBLES, start=1):

        print(f"\n[{idx}/{len(COMPTES_CIBLES)}] Traitement de @{username}")

        # Collecte du profil
        print("  → Récupération du profil...", end=" ", flush=True)
        profil = collecter_profil(username)
        if profil:
            abonnes = profil.get("follower_count", "?")
            abonnes_fmt = f"{abonnes:,}".replace(",", " ") if isinstance(abonnes, int) else str(abonnes)
            print(f" ({abonnes_fmt} abonnés)")
        else:
            print("Profil non disponible — les champs de profil seront vides")

        # Collecte des vidéos fenêtre par fenêtre
        if username not in comptes_avec_videos:
            # Jamais collecté → collecte complète depuis DATE_DEBUT
            debut_compte = DATE_DEBUT
        elif username == reprise_compte and reprise_fenetre_debut:
            # Compte interrompu en milieu de pagination → reprendre depuis le début
            # de la fenêtre interrompue (les doublons seront filtrés par ids_existants)
            debut_compte = reprise_fenetre_debut
        else:
            # Déjà collecté → incrémental depuis la dernière collecte
            debut_compte = date_debut_effective

        videos_compte: list[dict] = []
        quota_epuise = False

        for fen_debut, fen_fin in date_windows(debut_compte, date_fin_effective):

            curseur_init   = 0
            search_id_init = ""

            print(f"  → Fenêtre {fen_debut} → {fen_fin}...", end=" ", flush=True)

            videos_fenetre, statut = collecter_fenetre(
                username, fen_debut, fen_fin, curseur_init, search_id_init
            )

            if statut == "QUOTA_EPUISE":
                videos_session = videos_globales + videos_compte
                nouvelles_session = [v for v in videos_session if v.get("id") not in ids_existants]
                videos_intermediaires = videos_existantes + nouvelles_session

                # Sauvegarder l'état (informationnel uniquement — cursor/search_id ne sont
                # pas réutilisés au redémarrage car le search_id TikTok expire rapidement)
                sauvegarder_etat(
                    compte_en_cours=username,
                    fenetre_debut=fen_debut,
                    fenetre_fin=fen_fin,
                    cursor=0,
                    search_id="",
                    videos_collectees=[],
                )
                afficher_message_quota(videos_intermediaires, username, fen_debut, fen_fin)
                sauvegarder_json(videos_intermediaires, DATE_DEBUT, date_fin_effective)
                quota_epuise = True
                break

            print(f" {len(videos_fenetre)} vidéos")
            videos_compte.extend(videos_fenetre)

        if quota_epuise:
            sys.exit(0)

        # Enrichissement : profil dupliqué sur chaque ligne vidéo
        videos_enrichies: list[dict] = []
        for video in videos_compte:
            entree = {
                # Champs de profil (dupliqués intentionnellement sur chaque ligne)
                "username":       username,
                "follower_count": profil.get("follower_count", 0),
                "likes_count":    profil.get("likes_count", 0),
                "video_count":    profil.get("video_count", 0),

                # Champs vidéo
                "id":                video.get("id", ""),
                "create_time":       video.get("create_time", 0),
                "region_code":       video.get("region_code", ""),
                "video_description": video.get("video_description", ""),
                "video_duration":    video.get("video_duration", 0),
                "hashtag_names":     video.get("hashtag_names", []),
                "music_id":          video.get("music_id", ""),
                "effect_ids":        video.get("effect_ids", []),
                "playlist_id":       video.get("playlist_id", ""),
                "voice_to_text":     video.get("voice_to_text", ""),
                "is_stem_verified":  video.get("is_stem_verified", False),
                "video_mention_list": video.get("video_mention_list", []),
                "video_label":       video.get("video_label", ""),

                # Métriques
                "like_count":    video.get("like_count", 0),
                "comment_count": video.get("comment_count", 0),
                "share_count":   video.get("share_count", 0),
                "view_count":    video.get("view_count", 0),

                # URL construite pour le Script 2
                "url_video": f"https://www.tiktok.com/@{username}/video/{video.get('id', '')}",
            }
            videos_enrichies.append(entree)

        videos_globales.extend(videos_enrichies)

        print(f"  → @{username} terminé : {len(videos_enrichies)} vidéos ajoutées à la liste ")

    # Fusion avec les vidéos existantes (déduplication par ID)
    nouvelles = [v for v in videos_globales if v.get("id") not in ids_existants]
    print(f"\n[INCRÉMENTAL] {len(nouvelles)} nouvelles vidéos ajoutées (sur {len(videos_globales)} collectées)")
    videos_finales = videos_existantes + nouvelles

    # Résumé final
    sauvegarder_json(videos_finales, DATE_DEBUT, date_fin_effective)
    supprimer_etat()  # Collecte terminée avec succès : on efface le fichier d'état

    print()
    print("  COLLECTE TERMINÉE")
    print(f"  Total vidéos collectées : {len(videos_finales)}")
    print("  Structure               : liste plate — 1 entrée = 1 vidéo")
    print("                            profil complet inclus sur chaque ligne")
    print(f"  Fichier de sortie       : {CHEMIN_SORTIE_JSON if CHEMIN_SORTIE_JSON else '(non défini)'}")

if __name__ == "__main__":
    main()
