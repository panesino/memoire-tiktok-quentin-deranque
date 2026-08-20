# Récupération des métadonnées des comptes de médias candidats via la Research API de TikTok (aide à la sélection du corpus).

import json
import requests
from datetime import datetime

from credentials import CLIENT_KEY, CLIENT_SECRET

ACCOUNTS = [
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

TOKEN_URL   = "https://open.tiktokapis.com/v2/oauth/token/"
API_URL     = "https://open.tiktokapis.com/v2/research/user/info/"
OUTPUT_JSON = ""  # à compléter : fichier de sortie des statistiques de comptes

FIELDS = ["follower_count", "video_count", "likes_count"]

def get_access_token() -> str:
    """Obtient un access token client_credentials via l'API TikTok."""
    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key":    CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "grant_type":    "client_credentials",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_user_stats(username: str, access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params  = {"fields": ",".join(FIELDS)}
    payload = {"username": username}
    response = requests.post(API_URL, params=params, json=payload, headers=headers, timeout=10)
    if not response.ok:
        print(f"  [debug] status={response.status_code} body={response.text[:200]}")
    response.raise_for_status()
    data = response.json().get("data", {})
    return {
        "compte":      username,
        "followers":   data.get("follower_count", "N/A"),
        "nb_videos":   data.get("video_count",    "N/A"),
        "total_likes": data.get("likes_count",    "N/A"),
    }

def main():
    print("Obtention du token...")
    access_token = get_access_token()
    print(f"Token OK. Récupération des stats pour {len(ACCOUNTS)} comptes...\n")
    resultats = []

    for i, username in enumerate(ACCOUNTS, 1):
        print(f"[{i}/{len(ACCOUNTS)}] {username}...", end=" ", flush=True)
        try:
            stats = get_user_stats(username, access_token)
            print("OK")
        except Exception as e:
            print(f"ERREUR: {e}")
            stats = {
                "compte":      username,
                "followers":   f"Erreur: {e}",
                "nb_videos":   "N/A",
                "total_likes": "N/A",
            }
        resultats.append(stats)

    output = {
        "date_export": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "comptes": resultats,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Export terminé ({len(resultats)} comptes) -> {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
