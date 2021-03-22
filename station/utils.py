from hashlib import md5
from typing import List

import dask.dataframe as dd
import pandas as pd


def _get_surrogate_key(row: pd.Series, cols: List[str]) -> str:
    surrogate_string = "|".join([str(row[col]) for col in cols])
    surrogate_key = md5(surrogate_string.encode("utf-8")).hexdigest()
    return surrogate_key


def load_data(filepath: str = "data/newsapi/*/*/articles.json") -> pd.DataFrame:
    # load data
    df = dd.read_json(
        # 's3://articles-louisguitton/newsapi/2021-03-15/09/articles.json' fails, the issue is with s3
        filepath
    )

    # generate unique id and deduplicate
    articles_df = (
        df.compute()
        .assign(publishedAt=lambda d: pd.to_datetime(d.publishedAt))
        .reset_index(drop=True)
        .pipe(
            lambda d: d.join(
                pd.json_normalize(d.source, meta_prefix="source_").rename(
                    columns={"id": "source_id", "name": "source_name"}
                )
            )
        )
        .drop(columns="source")
        # Here we use ('title', 'source_name'), we could use 'url' but we would get more duplicates that just changed url.
        .assign(
            article_id=lambda d: d.apply(
                _get_surrogate_key, args=(["title", "source_name"],), axis=1
            )
        )
        .drop_duplicates(subset="article_id", keep="last")
    )
    return articles_df
