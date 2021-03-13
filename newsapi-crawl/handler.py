import datetime
import json
import logging
import os
from typing import Dict
import urllib

import boto3
from newsapi import NewsApiClient   

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

newsapi_key = os.environ['NEWSAPI_KEY']


def get_domains(newsapi: NewsApiClient) -> Dict[str, str]:
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

    return french_sources


def get_news(
    newsapi: NewsApiClient, sources: Dict[str, str], date_at: datetime.datetime
):
    all_articles = newsapi.get_everything(
        domains=",".join([domain for name, domain in sources.items()]),
        from_param=date_at.strftime("%Y-%m-%dT%H:%M:%S"),
        to=(date_at + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        language="fr",
        sort_by="publishedAt",
        page_size=100,
    )
    return all_articles["articles"]


def run(event, context):
    # https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents-expressions.html
    # https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents.html
    time = datetime.datetime.strptime(event["time"], "%Y-%m-%dT%H:%M:%SZ")
    name = context.function_name
    logger.info("Your cron function " + name + " ran at " + str(time))

    newsapi = NewsApiClient(api_key=newsapi_key)
    french_sources = get_domains(newsapi)
    articles = get_news(newsapi, french_sources, date_at=time)

    s3_bucket = "articles-louisguitton"
    s3_key = f"newsapi/{time.strftime('%Y-%m-%d/%H')}/articles.json"
    logger.info(f"Writing to s3:/{s3_bucket}/{s3_key}")
    s3 = boto3.resource('s3')
    s3object = s3.Object(s3_bucket, s3_key)

    s3object.put(
        Body=(bytes(json.dumps(articles).encode('UTF-8')))
    )
