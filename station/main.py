from elasticsearch_dsl import A, Q, Search
from elasticsearch import Elasticsearch

from station.config import Settings

settings = Settings()


def main():
    client = Elasticsearch(hosts=[settings.elasticsearch_url])

    q = Q(
        "nested",
        path="texta_facts",
        query=Q(
            "bool",
            must=[
                Q("match", texta_facts__fact="ORG"),
                Q("match", texta_facts__str_val="Magpies"),
            ],
        ),
    )
    s = Search(using=client, index="en-small").query(q)
    s.aggs.bucket("texta_facts", "nested", path="texta_facts").bucket(
        "related_entities", A("terms", field="texta_facts.str_val", size=5)
    )
    response = s.execute()
    print(response.aggregations.texta_facts.related_entities.buckets)


if __name__ == "__main__":
    main()
