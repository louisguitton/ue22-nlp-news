ES_INDEX = "articles"

ES_ALL_FIELD = "all_text"
ES_MAPPING = {
    "dynamic": "strict",
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html
    "properties": {
        "title": {
            "type": "text",
            "analyzer": "french",
            "copy_to": ES_ALL_FIELD,
        },
        "description": {
            "type": "text",
            "analyzer": "french",
            "copy_to": ES_ALL_FIELD,
        },
        "content": {
            "type": "text",
            "analyzer": "french",
            "copy_to": ES_ALL_FIELD,
        },
        "source_name": {"type": "keyword"},
        "author": {"type": "keyword"},
        "published_at": {"type": "date"},
        "url": {"type": "keyword"},
        "url_to_image": {"type": "keyword"},
        ES_ALL_FIELD: {
            "type": "text",
            "store": True,
        },
    },
}
