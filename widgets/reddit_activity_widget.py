import datetime
from collections import Counter

from textual.containers import Vertical
from textual.widgets import Static, Sparkline, Label

from const import ACTIVITY_DAYS_BACK
from models.user_data import UserData


class RedditActivityWidget(Static):
    DEFAULT_CSS = """
    .reddit_activity_row {
        margin: 2 2;
        height: auto;
    
        Sparkline {
            margin-top: 2;
        }
    }
    """

    def __init__(self, user_data: UserData, **kwargs):
        self.user_data = user_data
        self.days_back = ACTIVITY_DAYS_BACK
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        self._plot('Comment Activity', ACTIVITY_DAYS_BACK)
        self._plot('Comment Activity', 60)

    def _plot(self, label: str, days_back: int):
        points = self.user_data.comments

        start_day = (datetime.datetime.now() - datetime.timedelta(days=days_back)).date()

        # Trim and normalize point data
        points = [datetime.datetime.fromtimestamp(p.created_utc).date() for p in points]
        points = [p for p in points if p >= start_day]

        # Fill buckets
        buckets = {start_day + datetime.timedelta(days=i): 0 for i in range(days_back + 1)}
        for point in points:
            buckets[point] += 1

        values = list(buckets.values())
        counter = Counter(values)

        min_ = min(values)
        max_ = max(values)
        mean_ = round(sum(values) / len(values), 2)
        mode_ = counter.most_common(3)

        row = Vertical(classes='reddit_activity_row')
        row.compose_add_child(Label(f'{label} ({days_back}d)'))
        row.compose_add_child(Label(f'[MIN={min_}] [MAX={max_}] [MEAN={mean_}] [MODE={mode_}]'))
        row.compose_add_child(Sparkline(list(buckets.values())))
        self.mount(row)
