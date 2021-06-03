from typing import List, Dict, Union

from elasticsearch_dsl import connections, Search, Q
from elasticsearch_dsl.query import MoreLikeThis

from station.constants import ES_ALL_FIELD


class DatasetBase:
    def __init__(
        self,
        query: Q,
        date_field: str = None,
        stored_fields: str = None,
    ):
        self.search = Search()
        if date_field:
            self.search = self.search.sort(f"-{date_field}")
        if stored_fields:
            self.search = self.search.params(stored_fields=stored_fields)
        self.search = self.search.query(query)

    def __iter__(self):
        """ref: https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html?highlight=scroll#pagination"""
        return self.search.scan()

    def __len__(self):
        return self.search.count()


class Dataset(DatasetBase):
    def __init__(
        self,
        query: str,
        match_fields: List[str] = [ES_ALL_FIELD],
        date_field: str = None,
        stored_fields: str = None,
    ):
        # multi_match is ElasticSearch's Swiss Army knife for constructing queries across multiple fields.
        query = Q("multi_match", query=query, fields=match_fields)
        super().__init__(
            query=query, date_field=date_field, stored_fields=stored_fields
        )


class MLTDataset(DatasetBase):
    """ref: https://www.elastic.co/guide/en/elasticsearch/reference/master/query-dsl-mlt-query.html"""

    def __init__(
        self,
        like: Union[str, List[Union[str, Dict[str, str]]]],
        unlike: Union[str, List[Union[str, Dict[str, str]]]] = None,
        exclude: List[str] = [],
        min_term_freq: int = 1,
        max_query_terms: int = 12,
        min_doc_freq: int = 5,
        min_word_length: int = 0,
        max_word_length: int = 0,
        stop_words: List[str] = [],
        match_fields: List[str] = [ES_ALL_FIELD],
        date_field: str = None,
        stored_fields: str = None,
    ):
        query = MoreLikeThis(
            like=like,
            unlike=unlike,
            fields=match_fields,
            min_term_freq=min_term_freq,
            max_query_terms=max_query_terms,
            min_doc_freq=min_doc_freq,
            min_word_length=min_word_length,
            max_word_length=max_word_length,
            stop_words=stop_words,
        )
        super().__init__(query, date_field=date_field, stored_fields=stored_fields)
        self.search: Search = self.search.exclude("ids", values=exclude)

    def __iter__(self):
        """Use execute instead of scan for MLT query.

        I don't have the explanation yet but when running .scan(),
        I was getting the following error:
        `ScanError: Scroll request has only succeeded on 1 (+0 skipped) shards out of 7.`
        """
        return (hit for hit in self.search.execute())


if __name__ == "__main__":
    connection = connections.create_connection(hosts=["localhost:9200"])

    d = Dataset(
        query="sarkozy",
        date_field="published_at",
    )
    list(d)

    sarko_vaccin = [
        {"_id": "87f5c158211a6b45d009db6b3a341280", "_index": "articles"},
        {"_id": "6de485bcbdb78e8bd7282b376b246a51", "_index": "articles"},
        # {"_id": "c07e017b518ee88a66d20cee985851a8", "_index": "articles"},
        # {"_id": "cd80b3e15726b94f8f6a2285a806cc36", "_index": "articles"}
    ]
    mlt_d = MLTDataset(like=sarko_vaccin, date_field="published_at")
    list(mlt_d)
