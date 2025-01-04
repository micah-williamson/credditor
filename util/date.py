import datetime
import time

import arrow


def humanize(date: datetime.date) -> str:
    return arrow.get(date, tzinfo=time.tzname[time.daylight]).humanize(arrow.now())
