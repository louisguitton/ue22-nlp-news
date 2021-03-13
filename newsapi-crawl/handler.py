import datetime
import json
import logging
import os
from typing import Dict

import boto3
from newsapi import NewsApiClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


newsapi_key = os.environ["NEWSAPI_KEY"]


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


def main(date_at: datetime):
    newsapi = NewsApiClient(api_key=newsapi_key)

    # save 1 API call by loading from file
    # NewsAPI developer account is rate limited to 100 requests per day
    with open("./sources.json", "r") as fh:
        french_sources = json.load(fh)

    articles = get_news(newsapi, french_sources, date_at=date_at)

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


def run(event, context):
    """Lambda function handler that will run on schedule.
    
    Ref:
        - https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents.html
    """
    # When the function is triggered at time 2021-03-12T10:05:00, we want the news from the last hour
    time = datetime.datetime.strptime(
        event["time"], "%Y-%m-%dT%H:%M:%SZ"
    ) - datetime.timedelta(hours=1)
    name = context.function_name
    logger.info("Your cron function " + name + " ran at " + str(time))

    main(time)
