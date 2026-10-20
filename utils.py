import base64
from typing import List, Optional, Union

RATING_MAP = {
    "safe": "safe",
    "s": "safe",
    "g": "safe",
    "general": "safe",
    "questionable": "sketchy",
    "sketchy": "sketchy",
    "q": "sketchy",
    "sensitive": "sketchy",
    "explicit": "unsafe",
    "e": "unsafe",
    "unsafe": "unsafe",
}

BACK_RATING_MAP = {
    "safe": "s",
    "sketchy": "q",
    "unsafe": "e",
}

SORT_MAP = {
    "score": "sort:score",
    "score_desc": "sort:score",
    "score_asc": "sort:score-asc",
    "favcount": "sort:favs",
    "fav": "sort:favs",
    "id": "sort:id",
    "id_desc": "sort:id",
    "id_asc": "sort:id-asc",
    "rank": "sort:random",
    "random": "sort:random",
    "tagcount": "sort:tag-count",
    "tag_count": "sort:tag-count",
    "date": "sort:creation-date",
}

_TAG_CLEAN_TABLE = str.maketrans({
    ",": " ",
    "[": "",
    "]": "",
    '"': "",
    "'": "",
})


def strip_json_suffix(value: str) -> str:
    """Remove trailing .json extension from path parameters if present"""
    return value.removesuffix(".json")


def encode_auth_headers(u: str, p: str) -> str:
    """Encode username and password/token as base64 for Szurubooru Basic Auth header"""
    return base64.b64encode(f"{u}:{p}".encode("utf-8")).decode("ascii")


def tags_str(tags: list) -> str:
    """Extract first name from list of Szurubooru tag dicts and return space-delimited string"""
    names = []
    for tag in tags:
        if isinstance(tag, dict):
            tag_names = tag.get("names")
            if tag_names:
                names.append(tag_names[0])
        elif isinstance(tag, str):
            names.append(tag)
    return " ".join(names)


def convert_rating(rating: Optional[str]) -> Optional[str]:
    """Convert Danbooru rating to Szurubooru safety level"""
    if not rating:
        return None
    return RATING_MAP.get(rating.strip().lower())


def convert_back_rating(rating: Optional[str]) -> str:
    """Convert Szurubooru safety level to Danbooru rating character"""
    if not rating:
        return "g"
    return BACK_RATING_MAP.get(rating.strip().lower(), "g")


def parse_query(query: Optional[str]) -> str:
    """
    Translate Danbooru search query tokens into Szurubooru search syntax.
    Handles ratings, ordering/sorting, favorites, and user filters.
    """
    if not query:
        return ""

    tokens = query.split()
    if not tokens:
        return ""

    translated_tokens = []

    for token in tokens:
        is_negated = token.startswith("-")
        clean_token = token[1:] if is_negated else token

        if ":" in clean_token:
            key, _, val = clean_token.partition(":")
            key_lower = key.lower()
            prefix = "-" if is_negated else ""

            # 1. Rating mapping (e.g. rating:s, -rating:e, rating:safe)
            if key_lower == "rating":
                mapped_rating = convert_rating(val)
                if mapped_rating:
                    translated_tokens.append(f"{prefix}safety:{mapped_rating}")
                    continue

            # 2. Ordering / Sorting mapping (order:score -> sort:score)
            elif key_lower == "order":
                order_val = val.lower()
                translated = SORT_MAP.get(order_val, f"sort:{order_val}")
                translated_tokens.append(f"{prefix}{translated}")
                continue

            # 3. Favorite mapping (ordfav:user -> fav:user)
            elif key_lower == "ordfav":
                translated_tokens.append(f"{prefix}fav:{val}")
                continue

            # 4. Uploader / User mapping
            elif key_lower == "uploader":
                translated_tokens.append(f"{prefix}user:{val}")
                continue

        # Keep original token (handles tag names, wildcards, etc.)
        translated_tokens.append(token)

    return " ".join(translated_tokens)


def parse_tags(tags: Union[str, list]) -> List[str]:
    """Parse comma/space/bracket separated tags into a clean list of tag strings"""
    if isinstance(tags, list):
        return [s for t in tags if (s := str(t).strip())]

    if not tags:
        return []

    return tags.translate(_TAG_CLEAN_TABLE).split()


def parse_tags_str(tags: Union[str, list]) -> str:
    """Parse tags and return a single space-separated string"""
    return " ".join(parse_tags(tags))

