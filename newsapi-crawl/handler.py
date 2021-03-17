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


def get_news(
    newsapi: NewsApiClient,
    sources: Dict[str, str],
    execution_date: datetime.datetime,
    n_hours_delta: int = 1,
) -> List[Dict[str, Any]]:
    """Get NewsAPI news for a given hour."""
    logger.info("Getting articles for " + str(execution_date))
    newsapi_params = dict(
        domains=",".join([domain for name, domain in sources.items()]),
        language="fr",
        sort_by="publishedAt",
        page_size=100,
    )

    left_bound: str = execution_date.strftime("%Y-%m-%dT%H:%M:%S")

    # initialise the loop
    records: List[Dict[str, Any]] = []
    has_more_articles = True
    min_published_at: datetime = execution_date + datetime.timedelta(
        hours=n_hours_delta
    )
    api_calls: int = 0

    def _get_right_bound(min_published_at: datetime) -> str:
        # we have to remove 1 second for the midnight query because newsapi right bound is inclusive
        right_bound = (min_published_at - datetime.timedelta(seconds=1)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        return right_bound

    while has_more_articles:
        logger.info("Querying for news published until " + str(min_published_at))
        resp: Dict[str, Any] = newsapi.get_everything(
            from_param=left_bound,
            to=_get_right_bound(min_published_at),
            **newsapi_params,
        )
        api_calls += 1
        new_records: List[Dict[str, Any]] = resp["articles"]
        records += new_records
        # NewsAPI free license limits to 100 results per API call
        # If there were more articles during that time, split the API calls to return all articles from that hour
        has_more_articles = len(new_records) == 100

        if not len(records):
            raise ValueError(f"No news found for {execution_date}")
        min_published_at: datetime = datetime.datetime.strptime(
            min(r["publishedAt"] for r in records), "%Y-%m-%dT%H:%M:%SZ"
        )

    # Our assumption is that articles returned are from 1 given hour only, if that is not the case, raise an exception
    max_published_at: datetime = datetime.datetime.strptime(
        max(r["publishedAt"] for r in records), "%Y-%m-%dT%H:%M:%SZ"
    )
    if max_published_at - min_published_at > datetime.timedelta(hours=n_hours_delta):
        raise ValueError(
            f"The span of publish dates of the crawled articles is more than {n_hours_delta} hours."
        )

    logger.info(f"Done. Spent {api_calls} NewsAPI calls")
    return records


def main(execution_date: datetime.datetime, n_hours_delta: int = 1) -> None:
    newsapi = NewsApiClient(api_key=newsapi_key)

    # save 1 API call by loading from file
    # NewsAPI developer account is rate limited to 100 requests per day
    with open("./sources.json", "r") as fh:
        french_sources = json.load(fh)

    articles = get_news(
        newsapi, french_sources, execution_date=execution_date, n_hours_delta=n_hours_delta
    )

    if len(articles):
        s3_bucket = "articles-louisguitton"
        s3_key = f"newsapi/{execution_date.strftime('%Y-%m-%d/%H')}/articles.json"
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
    name = context.function_name
    logger.info("Your cron function " + name + " ran at " + str(berlin_datetime))


    execution_date = (
        berlin_datetime
        # the NewsAPI developer plan has 1 hour delay https://newsapi.org/pricing
        # given that we get the data from time to time+1h, we would need to remove at least hours=2
        # so to be sure, in case NewsAPI has more delay, we remove 3 hours
        - datetime.timedelta(hours=3)
        # because the serverless function can be scheduled at any minute within an hour, we remove the minutes
        - datetime.timedelta(minutes=berlin_datetime.minute)
    )
    main(execution_date)
