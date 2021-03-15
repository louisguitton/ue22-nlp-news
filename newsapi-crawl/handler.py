import datetime
import json
import logging
import os
from typing import Dict, Any, List
import pytz

import boto3
from newsapi import NewsApiClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


newsapi_key = os.environ["NEWSAPI_KEY"]


def get_news_of_hour(
    newsapi: NewsApiClient, sources: Dict[str, str], date_at: datetime.datetime
) -> List[Dict[str, Any]]:
    """Get NewsAPI news for a given hour."""
    newsapi_params = dict(
        domains=",".join([domain for name, domain in sources.items()]),
        language="fr",
        sort_by="publishedAt",
        page_size=100,
    )

    left_bound: str = date_at.strftime("%Y-%m-%dT%H:%M:%S")

    # initialise the loop
    records: List[Dict[str, Any]] = []
    has_more_articles = True
    min_published_at: datetime = date_at + datetime.timedelta(hours=1)

    def _get_right_bound(min_published_at: datetime) -> str:
        # we have to remove 1 second for the midnight query because newsapi right bound is inclusive
        right_bound = (min_published_at - datetime.timedelta(seconds=1)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        return right_bound

    while has_more_articles:
        resp: Dict[str, Any] = newsapi.get_everything(
            from_param=left_bound, to=_get_right_bound(min_published_at), **newsapi_params
        )
        new_records: List[Dict[str, Any]] = resp["articles"]
        records += new_records
        # NewsAPI free license limits to 100 results per API call
        # If there were more articles during that time, split the API calls to return all articles from that hour
        has_more_articles = len(records) == 100
        min_published_at: datetime = datetime.datetime.strptime(
            min(r["publishedAt"] for r in new_records), "%Y-%m-%dT%H:%M:%SZ"
        )

    # Our assumption is that articles returned are from 1 given hour only, if that is not the case, raise an exception
    min_published_at: datetime = datetime.datetime.strptime(
        min(r["publishedAt"] for r in records), "%Y-%m-%dT%H:%M:%SZ"
    )
    max_published_at: datetime = datetime.datetime.strptime(
        max(r["publishedAt"] for r in records), "%Y-%m-%dT%H:%M:%SZ"
    )
    if max_published_at - min_published_at > datetime.timedelta(hours=1):
        raise ValueError(
            "The span of publish dates of the crawled articles is more than 1 hour."
        )

    return records


def main(date_at: datetime) -> None:
    newsapi = NewsApiClient(api_key=newsapi_key)

    # save 1 API call by loading from file
    # NewsAPI developer account is rate limited to 100 requests per day
    with open("./sources.json", "r") as fh:
        french_sources = json.load(fh)

    articles = get_news_of_hour(newsapi, french_sources, date_at=date_at)

    if len(articles):
        s3_bucket = "articles-louisguitton"
        s3_key = f"newsapi/{date_at.strftime('%Y-%m-%d/%H')}/articles.json"
        logger.info(f"Writing to s3://{s3_bucket}/{s3_key}")
        s3 = boto3.resource("s3")
        s3object = s3.Object(s3_bucket, s3_key)
        jsonline_body = "\n".join([json.dumps(a) for a in articles])
        s3object.put(Body=(bytes(jsonline_body.encode("UTF-8"))))
    else:
        logger.info("No articles to write to S3")


def run(event, context) -> None:
    """Lambda function handler that will run on schedule.

    Ref:
        - https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents.html
    """
    # When the function is triggered at time 2021-03-12T10:05:00, we want the news from the last hour
    utc_datetime = datetime.datetime.strptime(event["time"], "%Y-%m-%dT%H:%M:%SZ")
    berlin_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(
        pytz.timezone("Europe/Berlin")
    )
    time = berlin_datetime - datetime.timedelta(hours=1)
    name = context.function_name
    logger.info("Your cron function " + name + " ran at " + str(time))

    main(time)
