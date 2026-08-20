"""
Dictionnaires de corrections pour le nettoyage du corpus.
Toutes les corrections sont insensibles à la casse pour les noms propres.
"""

# 1. NOMS PROPRES MAL TRANSCRITS
# Format : variante_phonétique → forme canonique
# Détectés par scan automatique sur le corpus + à compléter manuellement
# Les regex seront appliquées avec word boundaries (\b) et IGNORECASE

NAMED_ENTITIES_CORRECTIONS = {
    # Sarah Knafo (Reconquête)
    "sarakanafos": "Sarah Knafo",
    "kanaffo": "Knafo",
    "knafou": "Knafo",
    "saraknafos": "Sarah Knafo",
    "saraknafo": "Sarah Knafo",

    #Jordan Bardella (RN)
    "Jordan maldéla": "Jordan Bardella",
    "Jordan bordela": "Jordan Bardella",
    "Jordan mardella": "Jordan Bardella",

    # Bruno Retailleau (LR, ministre Intérieur)
    "rotaillot": "Retailleau",
    "rotailleau": "Retailleau",
    "rotaiyo": "Retailleau",
    "rotaio": "Retailleau",
    "retaillot": "Retailleau",
    "retailleau": "Retailleau",

    # Jean-Luc Mélenchon (LFI)
    "mélanchon": "Mélenchon",
    "melanchon": "Mélenchon",
    "Mélanchon": "Mélenchon",

    #Jean-Luc Moudenc et pas Mélenchon
    "moudinque": "Moudenc",
    "moudin": "Moudenc",

    # Raphaël Arnault (LFI)
    "Raphaël Arnaud": "Raphaël Arnault",
    "Raphaël arnaud": "Raphaël Arnault",
    "Rafael Arnaud": "Raphaël Arnault",

    # Mathilde Panot (LFI)
    "Mathilde Pannot": "Mathilde Panot",
    "Mathilde panneau": "Mathilde Panot",
    "Mathilde pano": "Mathilde Panot",
    "Mathilde Pinot": "Mathilde Panot",

    # Manuel Bompard (LFI)
    "manuel bombard": "Manuel Bompard",
    "Manuel bombard": "Manuel Bompard",
    "Manuel Bombard": "Manuel Bompard",
    "Emmanuel bonpart": "Manuel Bompard",
    "Emmanuel bonpark": "Manuel Bompard",
    "manuel bonpard": "Manuel Bompard",
    "manuel bonpark": "Manuel Bompard",
    "manuel bomba": "Manuel Bompard",
    "manuel bonpart": "Manuel Bompard",

    # Éric Ciotti (UDR)
    "Eric": "Éric",
    "siottie": "Ciotti",
    "siotti": "Ciotti",

    # Marion Maréchal (IDL/ex-Reconquête)
    "Marion maréchal": "Marion Maréchal",
    "marion-maréchal": "Marion Maréchal",

    # Quentin Deranque
    "Quentin d'orange": "Quentin Deranque",
    "Quentin d'érang": "Quentin Deranque",
    "Quentin des rangs": "Quentin Deranque",
    "Quentin de rang": "Quentin Deranque",
    "Quentin durant": "Quentin Deranque",

    # antifascisme/antifasciste
    "antifachisme": "antifascisme",
    "antifacisme": "antifascisme",
    "antifachiste": "antifasciste",
    "antifaciste": "antifasciste",
    "antifachistes": "antifascistes",
    "antifacistes": "antifascistes",

    #rixe
    "1 rix": "une rixe",
    "un rix": "une rixe",
    "une rix": "une rixe",
    "la rix": "la rixe",
    "simple rix": "simple rixe",
    "l'arix": "la rixe",

}

# 2. ARTEFACTS DE TRANSCRIPTION TIKTOK
# Format : pattern_regex → remplacement
# Appliqués via re.sub avec flags=re.IGNORECASE pour les mots

# Chiffres isolés à remplacer
# IMPORTANT : "1" isolé = "un/une" mal transcrit (4348 occurrences vérifiées)
# "2", "3", "4", "5" isolés sont presque toujours de vrais chiffres → NE PAS remplacer
ARTIFACTS_REGEX = [
    # "1" isolé devient "un" (cas le plus massif : 4348 occurrences)
    (r'\b1\b', 'un'),

    # Espaces multiples → espace simple (à appliquer EN DERNIER)
    # géré dans la fonction de nettoyage
]

# 3. HÉSITATIONS ORALES
# Hésitations orales à retirer.
ORAL_HESITATIONS = [
    "euh",
    "bah",
]

# 4. PATTERNS À NETTOYER

# URLs
URL_PATTERN = r'https?://\S+|www\.\S+'

# Emojis (regex Unicode)
EMOJI_PATTERN = (
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002500-\U00002BEF"  # chinese char
    "\U00002702-\U000027B0"  # dingbats
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"  # dingbats
    "\u3030"
    "]"
)

# Caractères de contrôle invisibles
INVISIBLE_PATTERN = r'[\u200b-\u200f\u202a-\u202e\ufeff]'
