ES_INDEX = "articles"

ES_MAPPING = {
    "dynamic": "strict",
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html
    "properties": {
        "title": {
            "type": "text",
            "analyzer": "french",
            "copy_to": "all_text",
        },
        "description": {
            "type": "text",
            "analyzer": "french",
            "copy_to": "all_text",
        },
        "content": {
            "type": "text",
            "analyzer": "french",
            "copy_to": "all_text",
        },
        "source_name": {"type": "keyword"},
        "author": {"type": "keyword"},
        "published_at": {"type": "date"},
        "url": {"type": "keyword"},
        "url_to_image": {"type": "keyword"},
        "all_text": {
            "type": "text",
        },
    },
}
