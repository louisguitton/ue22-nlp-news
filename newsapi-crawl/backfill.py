import logging
import datetime
import pandas as pd
from tqdm import tqdm
from handler import main

logger = logging.getLogger('handler')
logger.setLevel(logging.INFO)

backfill_range = pd.date_range(
    start=datetime.datetime(2021, 3, 23, 0),
    end=datetime.datetime(2021, 3, 26, 0),
    freq="D",
)

for date in tqdm(backfill_range):
    main(date, n_hours_delta=24)
