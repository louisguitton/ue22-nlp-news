import os
import datetime
import pandas as pd
from tqdm import tqdm
import time

backfill_range = pd.date_range(
    start=datetime.datetime(2021, 3, 11, 9),
    end=datetime.datetime(2021, 3, 12, 9),
    freq="H",
)

for date in tqdm(backfill_range):
    cmd = f"sls invoke local --function newsapi-run --stage dev --region eu-west-1 --data \"{{\\\"time\\\": \\\"{date.strftime('%Y-%m-%dT%H:%M:%SZ')}\\\"}}\""
    os.system(cmd)
    time.sleep(1)
