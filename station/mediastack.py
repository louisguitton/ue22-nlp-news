from typing import List

import requests

from station.config import Settings

settings = Settings()



def get_live_news(
    settings: Settings,
    sources: str = None,
    categories: str = None,
    countries: str = None,
    languages: str = None,
    keywords: str = None,
    date: str = None,
    sort: str = "published_desc",
    limit: int = 25,
    offset: int = 0
):
    """Call the /v1/news endpoint.

    https://mediastack.com/documentation#live_news"""
    url = "http://api.mediastack.com/v1/news"

    params = {
        "access_key": settings.mediastack_key,
        "sources": sources,
        "categories": categories,
        "countries": countries,
        "languages": languages,
        "keywords": keywords,
        "date": date,
        "sort": sort,
        "limit": limit,
        "offset": offset
    }
    res = requests.get(url, params=params)
    return res.json()


