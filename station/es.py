"""Ingest NewsAPI articles into ElasticSearch.

Ref:
    - https://github.com/elastic/elasticsearch-py/blob/master/examples/bulk-ingest/bulk-ingest.py
"""
import datetime
import json

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import FacetedSearch, TermsFacet, DateHistogramFacet

from station.utils import load_data


def create_index(client: Elasticsearch) -> None:
    """Creates an index in Elasticsearch if one isn't already there."""
    client.indices.create(
        index="articles",
        body={
            "settings": {"number_of_shards": 1},
            "mappings": {
                # https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html
                "properties": {
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "content": {"type": "text"},
                    "source_name": {"type": "keyword"},
                    "author": {"type": "keyword"},
                    "published_at": {"type": "date"},
                    "url": {"type": "keyword"},
                }
            },
        },
        ignore=400,
    )


def generate_actions():
    """Reads articles and for each row yields a single document.
    This function is passed into the bulk()
    helper to create many documents in sequence.
    """
    articles_df = load_data().rename(
        columns={"publishedAt": "published_at", "article_id": "_id"}
    )
    print(articles_df.shape)
    records = json.loads(articles_df.to_json(orient="records"))
    return records


class Article(Document):
    title = Text()
    description = Text()
    content = Text()
    source_name = Keyword()
    author = Keyword()
    published_at = Date()
    url = Keyword()

    class Index:
        name = "articles"
        settings = {
            "number_of_shards": 1,
        }


class ArticleSearch(FacetedSearch):
    """Ref: https://elasticsearch-dsl.readthedocs.io/en/latest/#pre-built-faceted-search"""
    doc_types = [
        Article,
    ]
    # fields that should be searched
    fields = ["source_name", "title", "description", "body"]

    facets = {
        # use bucket aggregations to define facets
        "source_name": TermsFacet(field="source_name"),
        "publishing_frequency": DateHistogramFacet(
            field="published_at", interval="week"
        ),
    }


if __name__ == "__main__":
    client = connections.create_connection(hosts=["localhost:9200"])
    create_index(client)

    bulk(client=client, actions=generate_actions(), index="articles")

    s = ArticleSearch()
    response = s.execute()

    for (tag, count, selected) in response.facets.source_name:
        print(tag, " (SELECTED):" if selected else ":", count)

    for (week, count, selected) in response.facets.publishing_frequency:
        print(week.strftime("%d %B %Y"), " (SELECTED):" if selected else ":", count)
