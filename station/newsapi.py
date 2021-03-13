from pprint import pprint
import urllib
import json
from typing import Dict
from datetime import datetime, timedelta

from newsapi import NewsApiClient
import pandas as pd

from station.config import Settings


def get_domains(
    newsapi: NewsApiClient, filepath: str = "data/sources.json"
) -> Dict[str, str]:
    french_sources = {}
    for category in [
        "business",
        "entertainment",
        "general",
        "health",
        "science",
        "sports",
        "technology",
    ]:
        top_headlines = newsapi.get_top_headlines(
            category=category, language="fr", country="fr"
        )
        french_sources.update(
            {
                a["source"]["name"]: urllib.parse.urlparse(a["url"]).netloc.lstrip(
                    "www."
                )
                for a in top_headlines["articles"]
            }
        )

    # TODO: do not overwrite, simply update
    with open(filepath, "w") as fh:
        json.dump(french_sources, fh)

    return french_sources


def get_news(newsapi: NewsApiClient, sources: Dict[str, str], datetime: datetime):
    all_articles = newsapi.get_everything(
        domains=",".join([domain for name, domain in sources.items()]),
        from_param=datetime.strftime("%Y-%m-%dT%H:%M:%S"),
        to=(datetime + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        language="fr",
        sort_by="publishedAt",
        page_size=100,
    )
    df = pd.json_normalize(all_articles["articles"])
    return df


if __name__ == "__main__":
    settings = Settings()
    newsapi = NewsApiClient(api_key=settings.newsapi_key)

    french_sources = get_domains(newsapi)

    articles = get_news(newsapi, french_sources, datetime(2021, 3, 12, 19))
