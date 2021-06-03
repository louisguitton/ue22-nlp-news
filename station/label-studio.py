import dask.dataframe as dd

df = dd.read_json("data/newsapi/2021-04-25/**/*.json", lines=True)


import json

data = []
with open("data/newsapi/2021-04-25/00/articles.json", "r") as fh:
    for line in fh:
        raw_data = json.loads(line)
        data.append(
            dict(
                data={
                    "text": "\n".join(
                        [
                            str(raw_data["title"]),
                            str(raw_data["description"]),
                            str(raw_data["content"]),
                        ]
                    ),
                    "source": raw_data["source"]["name"],
                    "publishedAt": raw_data["publishedAt"],
                    "urlToImage": raw_data["urlToImage"],
                }
            )
        )

with open("data/newsapi/2021-04-25/01/articles.json", "w") as fh:
    json.dump(data, fh)
