import json


from algoliasearch.search_client import SearchClient


from station.config import Settings
from station.utils import load_data

settings = Settings()


def main():
    articles_df = load_data()

    # load data to Algolia
    client = SearchClient.create(
        settings.algolia_application_id, settings.algolia_admin_api_key
    )
    index = client.init_index("articles")
    records = json.loads(
        articles_df
        .rename(columns={"article_id": "objectID"})
        .to_json(orient="records")
    )
    index.save_objects(records)

    # configure Algolia
    index.set_settings(
        {
            "searchableAttributes": ["content", "description", "title"],
            "ranking": [
                "desc(publishedAt)",
                "typo",
                "geo",
                "words",
                "filters",
                "proximity",
                "attribute",
                "exact",
                "custom",
            ],
            "indexLanguages": ["fr"],
            "attributesForFaceting": ["source_name"],
        }
    )
