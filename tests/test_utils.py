from utils import (
    convert_rating,
    convert_back_rating,
    parse_query,
    parse_tags,
    parse_tags_str,
    strip_json_suffix,
    tags_str,
    encode_auth_headers,
)


def test_strip_json_suffix():
    assert strip_json_suffix("123.json") == "123"
    assert strip_json_suffix("123") == "123"
    assert strip_json_suffix("alice.json") == "alice"


def test_convert_rating():
    assert convert_rating("s") == "safe"
    assert convert_rating("safe") == "safe"
    assert convert_rating("g") == "safe"
    assert convert_rating("general") == "safe"
    assert convert_rating("q") == "sketchy"
    assert convert_rating("questionable") == "sketchy"
    assert convert_rating("sensitive") == "sketchy"
    assert convert_rating("e") == "unsafe"
    assert convert_rating("explicit") == "unsafe"
    assert convert_rating("unsafe") == "unsafe"
    assert convert_rating("unknown_val") is None
    assert convert_rating(None) is None


def test_convert_back_rating():
    assert convert_back_rating("safe") == "s"
    assert convert_back_rating("sketchy") == "q"
    assert convert_back_rating("unsafe") == "e"
    assert convert_back_rating(None) == "g"


def test_parse_query_ratings():
    assert parse_query("rating:s") == "safety:safe"
    assert parse_query("rating:safe") == "safety:safe"
    assert parse_query("-rating:e") == "-safety:unsafe"
    assert parse_query("rating:questionable cat") == "safety:sketchy cat"


def test_parse_query_orders():
    assert parse_query("order:score") == "sort:score"
    assert parse_query("order:favcount") == "sort:favs"
    assert parse_query("order:id_desc") == "sort:id"
    assert parse_query("order:random") == "sort:random"
    assert parse_query("cat order:score dog") == "cat sort:score dog"


def test_parse_query_favorites_and_uploader():
    assert parse_query("ordfav:alice") == "fav:alice"
    assert parse_query("uploader:bob") == "user:bob"
    assert parse_query("-uploader:bob") == "-user:bob"


def test_parse_tags():
    assert parse_tags("tag1, tag2, [tag3]") == ["tag1", "tag2", "tag3"]
    assert parse_tags(["tag1", "", "tag2"]) == ["tag1", "tag2"]
    assert parse_tags("") == []
    assert parse_tags_str("tag1, 'tag2', \"tag3\"") == "tag1 tag2 tag3"


def test_tags_str():
    tags = [
        {"names": ["cat", "feline"], "category": "general"},
        {"names": ["hat"], "category": "general"},
        "raw_tag",
    ]
    assert tags_str(tags) == "cat hat raw_tag"


def test_encode_auth_headers():
    encoded = encode_auth_headers("user", "pass:word")
    assert encoded == "dXNlcjpwYXNzOndvcmQ="

