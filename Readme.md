# station

> Industry grade text analytics combining spaCy and ElasticSearch

## Thanks

- https://github.com/EMBEDDIA/texta-rest
- https://github.com/d-one/NLPeasy
- https://github.com/nestauk/clio-lite
- https://github.com/deepset-ai/haystack

## Flow

- get some JSONL text data
  - specify which language it is (in our case ES_analyser = french)
  - specify which fields are text and copied to 'all_text'
  - specify which field to use as '\_id'
- ingest into ElasticSearch
- add 'Dataset' class that takes an ES query and returns documents
- add 'Serialiser' class that takes Dataset and returns docs for sklearn and spaCy
- parse documents with Language models (spaCy or stanza?) to get NER

## News Dataset

https://commoncrawl.org/2016/10/news-dataset-available/
https://github.com/commoncrawl/news-crawl/
