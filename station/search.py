from elasticsearch_dsl import (
    connections,
    Document,
    Date,
    Integer,
    Keyword,
    Text,
    FacetedSearch,
    TermsFacet,
    DateHistogramFacet,
)


class Article(Document):
    title = Text()
    description = Text()
    content = Text()
    source_name = Keyword()
    author = Keyword()
    published_at = Date()
    url = Keyword()
    url_to_image = Keyword()
    all_text = Text()

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
    connection = connections.create_connection(hosts=["localhost:9200"])

    s = ArticleSearch()
    response = s.execute()

    for (tag, count, selected) in response.facets.source_name:
        print(tag, " (SELECTED):" if selected else ":", count)

    for (week, count, selected) in response.facets.publishing_frequency:
        print(week.strftime("%d %B %Y"), " (SELECTED):" if selected else ":", count)
