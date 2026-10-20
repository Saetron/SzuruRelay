from typing import Any, Dict, Optional
from utils import convert_back_rating
from services.url_helper import build_resource_url

category_map = {
    "default": 0,
    "general": 0,
    "artist": 1,
    "series": 3,
    "copyright": 3,
    "character": 4,
    "meta": 5,
    0: "General",
    1: "Artist",
    3: "Series",
    4: "Character",
    5: "Meta",
}

RANK_MAP = {
    "anonymous": (0, "Anonymous"),
    "restricted": (10, "Restricted"),
    "regular": (20, "Member"),
    "power": (30, "Gold"),
    "moderator": (40, "Moderator"),
    "administrator": (50, "Admin"),
}

_ANONYMOUS_USER = {
    "id": 1,
    "name": "Anonymous",
    "level": 0,
    "level_string": "Anonymous",
    "created_at": "2020-01-01T00:00:00Z",
    "is_deleted": False,
    "is_banned": False,
}


def is_post_favorited_by(szuru_post: Dict[str, Any], login: Optional[str]) -> bool:
    """Check if the current post is favorited by the logged-in user"""
    if not login:
        return False
    if szuru_post.get("ownFavorite") is True:
        return True
    favorited_by = szuru_post.get("favoritedBy")
    if not favorited_by:
        return False
    login_lower = login.lower()
    for fav in favorited_by:
        if isinstance(fav, dict):
            name = fav.get("name")
            if name and name.lower() == login_lower:
                return True
        elif isinstance(fav, str) and fav.lower() == login_lower:
            return True
    return False


def convert_user_format(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Szurubooru user profile response to Danbooru user format"""
    user_obj = None
    if isinstance(user_data, dict):
        if "results" in user_data:
            results = user_data.get("results")
            if results:
                user_obj = results[0]
        else:
            user_obj = user_data

    if not user_obj:
        return dict(_ANONYMOUS_USER)

    rank = str(user_obj.get("rank", "regular")).lower()
    level, level_string = RANK_MAP.get(rank, (20, "Member"))
    creation_time = user_obj.get("creationTime", "")
    last_login_time = user_obj.get("lastLoginTime", "")

    return {
        "id": user_obj.get("id", 1),
        "name": user_obj.get("name", "User"),
        "level": level,
        "level_string": level_string,
        "created_at": creation_time,
        "last_logged_in_at": last_login_time,
        "updated_at": last_login_time or creation_time,
        "blacklisted_tags": "",
        "favorite_tags": "",
        "is_deleted": False,
        "is_banned": False,
        "time_zone": "Eastern Time (US & Canada)",
        "post_upload_count": user_obj.get("uploadedPostCount", 0),
        "favorite_count": user_obj.get("favoritePostCount", 0),
        "comment_count": user_obj.get("commentCount", 0),
        "per_page": 20,
        "default_image_size": "large",
    }


def convert_post_format(
    szuru_post: Dict[str, Any],
    login: Optional[str] = None,
    request: Optional[Any] = None,
    base_domain: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a Szurubooru post object to a Danbooru-compatible post object"""
    raw_content_url = szuru_post.get("contentUrl", "")
    raw_thumb_url = szuru_post.get("thumbnailUrl", "")
    content_url = build_resource_url(
        raw_content_url, request=request, base_domain=base_domain
    )
    thumbnail_url = build_resource_url(
        raw_thumb_url, request=request, base_domain=base_domain
    )
    url_path = content_url.partition("?")[0]
    ext = url_path.rsplit(".", 1)[-1].lower() if "." in url_path else "jpg"

    artist_tags = []
    general_tags = []
    character_tags = []
    copyright_tags = []
    meta_tags = []
    all_tags = []

    raw_tags = szuru_post.get("tags") or []
    for tag in raw_tags:
        if isinstance(tag, dict):
            names = tag.get("names")
            if not names:
                continue
            tag_name = names[0]
            if not tag_name:
                continue
            all_tags.append(tag_name)
            cat = str(tag.get("category", "default")).lower()
            if cat in ("default", "general"):
                general_tags.append(tag_name)
            elif cat == "artist":
                artist_tags.append(tag_name)
            elif cat == "character":
                character_tags.append(tag_name)
            elif cat in ("series", "copyright"):
                copyright_tags.append(tag_name)
            elif cat == "meta":
                meta_tags.append(tag_name)
            else:
                general_tags.append(tag_name)
        elif isinstance(tag, str) and tag:
            all_tags.append(tag)
            general_tags.append(tag)

    favorited = is_post_favorited_by(szuru_post, login)
    source = (szuru_post.get("source") or "").partition("\n")[0]

    post_id = szuru_post.get("id", 0)
    creation_time = szuru_post.get("creationTime", "")
    last_edit_time = szuru_post.get("lastEditTime") or creation_time
    width = szuru_post.get("canvasWidth", 0)
    height = szuru_post.get("canvasHeight", 0)
    file_size = szuru_post.get("fileSize", 0)
    md5 = szuru_post.get("checksumMD5", "")
    safety = szuru_post.get("safety", "safe")
    score = szuru_post.get("score", 0)
    user_info = szuru_post.get("user")
    uploader_id = user_info.get("id", 1) if isinstance(user_info, dict) else 1

    return {
        "id": post_id,
        "created_at": creation_time,
        "uploader_id": uploader_id,
        "score": score,
        "file_url": content_url,
        "large_file_url": content_url,
        "preview_file_url": thumbnail_url,
        "file_ext": ext,
        "rating": convert_back_rating(safety),
        "source": source,
        "tag_string": " ".join(all_tags),
        # Preserved for AnimeBoxes
        "fav_string": "fav:1" if favorited else "",
        # Standard Danbooru boolean
        "is_favorited": favorited,
        "tag_string_general": " ".join(general_tags),
        "tag_string_artist": " ".join(artist_tags),
        "tag_string_character": " ".join(character_tags),
        "tag_string_copyright": " ".join(copyright_tags),
        "tag_string_meta": " ".join(meta_tags),
        "tag_count": len(raw_tags),
        "tag_count_artist": len(artist_tags),
        "tag_count_general": len(general_tags),
        "tag_count_character": len(character_tags),
        "tag_count_copyright": len(copyright_tags),
        "tag_count_meta": len(meta_tags),
        "image_width": width,
        "image_height": height,
        "file_size": file_size,
        "md5": md5,
        "has_large": True,
        "has_visible_children": False,
        "has_active_children": False,
        "has_children": False,
        "media_asset": {
            "id": post_id,
            "created_at": creation_time,
            "updated_at": last_edit_time,
            "md5": md5,
            "file_ext": ext,
            "image_width": width,
            "image_height": height,
            "variants": [
                {
                    "type": "sample",
                    "url": content_url,
                    "width": width,
                    "height": height,
                    "file_ext": ext,
                },
                {
                    "type": "original",
                    "url": content_url,
                    "width": width,
                    "height": height,
                    "file_ext": ext,
                },
            ],
        },
    }

