# pip install datasets[s3]
import glob

import datasets
from datasets import load_dataset
from elasticsearch import Elasticsearch
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import CountVectorizer

# Copy S3 files locally
s3 = datasets.filesystems.S3FileSystem()
s3.get("articles-louisguitton/newsapi/", "data/", recursive=True)

# Process dataset
dataset = (
    load_dataset("json", data_files=glob.glob("data/newsapi/*/00/articles.json"))
    .rename_column("publishedAt", "published_at")
    .flatten()
    # TODO: process better to clean cases when description and content are the same
    .map(
        lambda row: {
            "text": "\n".join(
                [row["title"] or "", row["description"] or "", row["content"] or ""]
            )
        }
    )
    .sort("published_at")
    .remove_columns(
        ["author", "source.id", "urlToImage", "url", "title", "description", "content"]
    )
)


# Compute Aggregations
df = dataset.with_format("pandas")["train"][:]
df.groupby(df.published_at.dt.date).text.count()
df.groupby(df["source.name"]).text.count()
df.text.apply(len).hist()

# Adding an ElasticSearch index
# docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.11.2
es_client = Elasticsearch([{"host": "localhost", "port": "9200"}])
es_client.ping()
es_config = {
    "settings": {
        "number_of_shards": 1,
        "analysis": {
            "analyzer": {
                "stop_standard": {"type": "standard", " stopwords": "_french_"}
            }
        },
    },
    "mappings": {
        "properties": {
            "text": {"type": "text", "analyzer": "standard", "similarity": "BM25"}
        }
    },
}
# TODO: fix TransportError: TransportError(429, 'cluster_block_exception', 'index [newsapi] blocked by: [TOO_MANY_REQUESTS/12/disk usage exceeded flood-stage watermark, index has read-only-allow-delete block];')
dataset["train"].add_elasticsearch_index(
    "text", es_client=es_client, es_index_name="newsapi", es_index_config=es_config
)

query = "machine"
scores, retrieved_examples = dataset["train"].get_nearest_examples("text", query, k=10)
retrieved_examples["title"][0]

# KG generation with co-occuring words
count_model = CountVectorizer(ngram_range=(1, 1))
X = count_model.fit_transform(df.text)
Xc = X.T * X
g = sp.diags(1.0 / Xc.diagonal())
Xc_norm = g * Xc
Xc_norm.setdiag(0)

def get_top_associated_words(of: str = "sarkozy"):
    v = Xc_norm[count_model.vocabulary_[of]].todense()
    A = np.squeeze(np.asarray(v))
    top = np.argpartition(A, -20)[-20:]
    # TODO: remove stopwords
    return [k for k, vv in count_model.vocabulary_.items() if vv in top]
