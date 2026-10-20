import pytest
from models.converters import convert_post_format, convert_user_format, is_post_favorited_by


def test_is_post_favorited_by():
    post = {
        "favoritedBy": [
            {"name": "Alice"},
            {"name": "Bob"},
        ]
    }
    assert is_post_favorited_by(post, "Alice") is True
    assert is_post_favorited_by(post, "alice") is True
    assert is_post_favorited_by(post, "Charlie") is False
    assert is_post_favorited_by(post, None) is False


def test_convert_post_format():
    szuru_post = {
        "id": 42,
        "creationTime": "2023-01-01T12:00:00Z",
        "lastEditTime": "2023-01-02T12:00:00Z",
        "canvasWidth": 1920,
        "canvasHeight": 1080,
        "fileSize": 123456,
        "checksumMD5": "d41d8cd98f00b204e9800998ecf8427e",
        "safety": "safe",
        "score": 10,
        "source": "https://example.com\nsecond line",
        "contentUrl": "data/posts/42.png",
        "thumbnailUrl": "thumbnails/42.jpg",
        "tags": [
            {"names": ["cat"], "category": "general"},
            {"names": ["monet"], "category": "artist"},
            {"names": ["miku"], "category": "character"},
            {"names": ["vocaloid"], "category": "series"},
            {"names": ["highres"], "category": "meta"},
        ],
        "favoritedBy": [{"name": "Alice"}],
    }

    # Test favorited by Alice
    dan_post_alice = convert_post_format(szuru_post, login="Alice")
    assert dan_post_alice["id"] == 42
    assert dan_post_alice["is_favorited"] is True
    assert dan_post_alice["fav_string"] == "fav:1"
    assert dan_post_alice["md5"] == "d41d8cd98f00b204e9800998ecf8427e"
    assert dan_post_alice["rating"] == "s"
    assert dan_post_alice["tag_string"] == "cat monet miku vocaloid highres"
    assert dan_post_alice["tag_string_artist"] == "monet"
    assert dan_post_alice["tag_string_character"] == "miku"
    assert dan_post_alice["tag_string_copyright"] == "vocaloid"
    assert dan_post_alice["tag_string_meta"] == "highres"
    assert dan_post_alice["source"] == "https://example.com"
    assert dan_post_alice["media_asset"]["md5"] == "d41d8cd98f00b204e9800998ecf8427e"

    # Test not favorited by Bob
    dan_post_bob = convert_post_format(szuru_post, login="Bob")
    assert dan_post_bob["is_favorited"] is False
    assert dan_post_bob["fav_string"] == ""


def test_convert_user_format():
    user_data = {
        "results": [
            {
                "id": 5,
                "name": "Alice",
                "rank": "regular",
                "creationTime": "2022-05-01T00:00:00Z",
                "lastLoginTime": "2023-01-01T00:00:00Z",
                "uploadedPostCount": 15,
            }
        ]
    }
    dan_user = convert_user_format(user_data)
    assert dan_user["name"] == "Alice"
    assert dan_user["id"] == 5
    assert dan_user["post_upload_count"] == 15

    # Test empty results fallback without crashing and ensure returned dict is a fresh copy
    empty_user = convert_user_format({"results": []})
    assert empty_user["name"] == "Anonymous"
    assert empty_user["id"] == 1
    empty_user["id"] = 999
    assert convert_user_format({})["id"] == 1


def test_is_post_favorited_by_own_favorite_and_strings():
    assert is_post_favorited_by({"ownFavorite": True}, "anyone") is True
    assert is_post_favorited_by({"favoritedBy": ["Alice", "Bob"]}, "bob") is True

