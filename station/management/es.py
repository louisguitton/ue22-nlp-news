"""Updates the ElasticSearch index."""
import json
from pprint import pprint

from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk, BulkIndexError
import typer


from station.constants import ES_INDEX, ES_MAPPING
from station.utils import load_data


def _document_generator():
    articles_df = (
        load_data()
        .rename(
            columns={
                "publishedAt": "published_at",
                "article_id": "_id",
                "urlToImage": "url_to_image",
            }
        )
        .drop("source_id", axis=1)
    )
    records = json.loads(articles_df.to_json(orient="records"))
    return records


def main():
    """Updates the ElasticSearch index."""
    connection = connections.create_connection(hosts=["localhost:9200"])

    typer.echo(f'Checking if index "{ES_INDEX}" exists...')
    if connection.indices.exists(index=ES_INDEX):
        typer.echo(f'Index "{ES_INDEX}" already exists')
        typer.echo(f'Updating mapping on "{ES_INDEX}" index...')
        connection.indices.put_mapping(index=ES_INDEX, body=ES_MAPPING)
        typer.echo(f'Updated mapping on "{ES_INDEX}" successfully')
    else:
        typer.echo(f'Index "{ES_INDEX}" does not exist')
        typer.echo(f'Creating index "{ES_INDEX}"...')
        connection.indices.create(
            index=ES_INDEX,
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                },
                "mappings": ES_MAPPING,
            },
        )
        typer.echo(f'Index "{ES_INDEX}" created successfully')

    typer.echo(f'Bulk updating documents on "{ES_INDEX}" index...')
    try:
        succeeded, _ = bulk(
            client=connection, index=ES_INDEX, actions=_document_generator()
        )
    except BulkIndexError as exception:
        raise BulkIndexError(
            "error encountered while indexing",
            [e["index"]["error"] for e in exception.errors],
        )

    typer.echo(f'Updated {succeeded} documents on "{ES_INDEX}" successfully')


if __name__ == "__main__":
    typer.run(main)
