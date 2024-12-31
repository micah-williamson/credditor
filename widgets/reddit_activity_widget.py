import datetime
from collections import Counter, defaultdict

from rich.table import Table
from textual.containers import Vertical
from textual.widgets import Static, Sparkline, Label, Rule

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
        self.mount(self._get_activity_chart('Comment Activity', ACTIVITY_DAYS_BACK))
        self.mount(self._get_activity_chart('Comment Activity', 60))
        self.mount(Rule(line_style='heavy'))
        self.mount(self._get_subreddit_table())

    def _get_subreddit_table(self):
        table = Table()
        table.add_column('subreddit')
        table.add_column('comments')
        table.add_column('comment karma')

        subreddit_counter = defaultdict(lambda: (0, 0))
        for comment in self.user_data.comments:
            count, karma = subreddit_counter[comment.subreddit.display_name]
            subreddit_counter[comment.subreddit.display_name] = (count + 1, comment.score)

        subreddit_counts = list(subreddit_counter.items())
        subreddit_counts.sort(key=lambda sc: sc[1][0], reverse=True)

        for subreddit_count in subreddit_counts:
            subreddit_uri = f'r/{subreddit_count[0]}'
            table.add_row(
                f'[link=https://reddit.com/{subreddit_uri}]{subreddit_uri}[/]',
                str(subreddit_count[1][0]),
                str(subreddit_count[1][1])
            )

        container = Static()
        container.update(table)
        return container

    def _get_activity_chart(self, label: str, days_back: int):
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
        return row
