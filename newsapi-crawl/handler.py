import datetime
import json
import logging
import os
from typing import Dict, Any, List
import urllib

import pytz
import boto3
from newsapi import NewsApiClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


newsapi_key = os.environ["NEWSAPI_KEY"]


def _extract_sources(articles: List[Dict]) -> Dict[str, str]:
    return {
        a["source"]["name"]: urllib.parse.urlparse(a["url"]).netloc.lstrip("www.")
        for a in articles
    }


def get_domains(
    newsapi: NewsApiClient, filepath: str = "./sources.json", **newsapi_params
) -> Dict[str, str]:
    """Get NewsAPI domains.

    Arguments:
        newsapi: NewsAPI python client. See <https://newsapi.org/docs/client-libraries/python> for more documentation.
        filepath: local destination to store the domains as a JSON file.
        q: Keywords or a phrase to search for in the article title and body.  See the official News API
            `documentation <https://newsapi.org/docs/endpoints/everything>`_ for search syntax and examples.
        qintitle: Keywords or a phrase to search for in the article title and body.  See the official News API
            `documentation <https://newsapi.org/docs/endpoints/everything>`_ for search syntax and examples.
        sources: A comma-seperated string of identifiers for the news sources or blogs you want headlines from.
            Use :meth:`NewsApiClient.get_sources` to locate these programmatically, or look at the
            `sources index <https://newsapi.org/sources>`_.  **Note**: you can't mix this param with the
            ``country`` or ``category`` params.
        language: The 2-letter ISO-639-1 code of the language you want to get headlines for.
            See :data:`newsapi.const.languages` for the set of allowed values.
            The default for this method is ``"en"`` (English).  **Note**: this parameter is not mentioned in the
            `/top-headlines documentation <https://newsapi.org/docs/endpoints/top-headlines>`_ as of Sep. 2019,
            but *is* supported by the API.
        country: The 2-letter ISO 3166-1 code of the country you want to get headlines for.
            See :data:`newsapi.const.countries` for the set of allowed values.
            **Note**: you can't mix this parameter with the ``sources`` param.

    Returns:
        a dictionary of sources with their name as key and domain as value.
    """
    sources = {}
    for category in [
        "business",
        "entertainment",
        "general",
        "health",
        "science",
        "sports",
        "technology",
    ]:
        top_headlines = newsapi.get_top_headlines(category=category, **newsapi_params)
        sources.update(_extract_sources(top_headlines["articles"]))

    # TODO: do not overwrite, simply update
    with open(filepath, "w") as fh:
        json.dump(sources, fh)

    return sources


def get_news(
    newsapi: NewsApiClient,
    execution_date: datetime.datetime,
    n_hours_delta: int = 1,
    **newsapi_params,
) -> List[Dict[str, Any]]:
    """Get NewsAPI news for a given timeframe.

    This method paginates the requests to accomodate for the Developer plan of NewsAPI.
    In that plan, only 1 page of up to 100 articles can be queried at once.
    Therefore, we're using a while loop to paginate through the articles, and still be able
    to get all articles published between `execution_date` and `exection_date` + `n_hours_delta` * hours.

    Arguments:
        newsapi: NewsAPI python client. See <https://newsapi.org/docs/client-libraries/python> for more documentation.
        execution_date: datetime marking the left bound of the time interval for which we want to crawl news
        n_hours_delta: number of hours after the execution_date marking the right bound of the time interval for which we want to crawl news
        q: Keywords or a phrase to search for in the article title and body.  See the official News API
            `documentation <https://newsapi.org/docs/endpoints/everything>`_ for search syntax and examples.
        qintitle: Keywords or a phrase to search for in the article title and body.  See the official News API
            `documentation <https://newsapi.org/docs/endpoints/everything>`_ for search syntax and examples.
        sources: A comma-seperated string of identifiers for the news sources or blogs you want headlines from.
            Use :meth:`NewsApiClient.get_sources` to locate these programmatically, or look at the
            `sources index <https://newsapi.org/sources>`_.
        domains:  A comma-seperated string of domains (eg bbc.co.uk, techcrunch.com, engadget.com)
            to restrict the search to.
        exclude_domains:  A comma-seperated string of domains (eg bbc.co.uk, techcrunch.com, engadget.com)
            to remove from the results.
        language: The 2-letter ISO-639-1 code of the language you want to get headlines for.
            See :data:`newsapi.const.languages` for the set of allowed values.
        sort_by: The order to sort articles in.
            See :data:`newsapi.const.sort_method` for the set of allowed values.

    Returns:
        List of all articles published between `execution_date` and `exection_date` + `n_hours_delta` * hours.
    """
    logger.info("Getting articles for " + str(execution_date))
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

    print(api_calls)
    logger.info(f"Done. Spent {api_calls} NewsAPI calls")

    # Our assumption is that articles returned are from 1 given hour only, if that is not the case, raise an exception
    max_published_at: datetime = datetime.datetime.strptime(
        max(r["publishedAt"] for r in records), "%Y-%m-%dT%H:%M:%SZ"
    )
    if max_published_at - min_published_at > datetime.timedelta(hours=n_hours_delta):
        raise ValueError(
            f"The span of publish dates of the crawled articles is more than {n_hours_delta} hours."
        )

    return records


def main(
    execution_date: datetime.datetime,
    n_hours_delta: int = 1,
    refresh_sources: bool = False,
) -> None:
    """Get all french articles for a given timeframe and store them to S3."""
    # before using any API credits, check S3 credentials
    sts = boto3.client("sts")
    sts.get_caller_identity()

    newsapi = NewsApiClient(api_key=newsapi_key)

    # using the `sources` param of /v2/everything endpoint is useful only if the sources are officially supported by NewsAPI.
    # for French, NewsAPI has only 5 sources that you can pass to `sources`, which is only a fraction of the articles you can get.
    # so instead, we use the `domains` param of /v2/everything.
    # we can construct the list of domains by calling /v2/top-headlines, filtering for `country=fr` and storing that to a file.
    if refresh_sources:
        get_domains(newsapi, language="fr", country="fr")

    # save API calls by loading sources from file
    # NewsAPI developer account is rate limited to 100 requests per day
    with open("./sources.json", "r") as fh:
        french_sources = json.load(fh)

    newsapi_params = dict(
        domains=",".join([domain for name, domain in french_sources.items()]),
        language="fr",
        sort_by="publishedAt",
        page_size=100,
    )
    articles = get_news(
        newsapi,
        execution_date=execution_date,
        n_hours_delta=n_hours_delta,
        **newsapi_params,
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
    main(execution_date, n_hours_delta=24)
