import datetime
import time

from rich.style import Style
from rich.table import Table
from textual.widgets import Static

from models.user_data import UserData

# Requirements
_MIN_KARMA = 2000
_MIN_COMMENT_KARMA = 800
_MIN_AGE_DAYS = 120

# Common Styles
_RED_FLAG = Style(color='red', bold=True)


class UserInfoWidget(Static):

    def __init__(self, user_data: UserData, **kwargs):
        self.user_data = user_data
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        table = Table()
        table.add_column('field')
        table.add_column('value')
        table.add_column('')

        age_days = (datetime.datetime.today().date() - self.user_data.created_at).days

        table.add_row('Name', self.user_data.username)
        table.add_row('Account Age', str(age_days),
                      style=_RED_FLAG if age_days < _MIN_AGE_DAYS else None)
        table.add_row('Total Karma', str(self.user_data.total_karma),
                      style=_RED_FLAG if self.user_data.total_karma < _MIN_KARMA else None)
        table.add_row('Comment Karma', str(self.user_data.comment_karma),
                      style=_RED_FLAG if self.user_data.comment_karma < _MIN_COMMENT_KARMA else None)
        table.add_row('USL Status', 'FOUND' if self.user_data.is_in_usl else 'NOT FOUND',
                      f'https://www.universalscammerlist.com/?username={self.user_data.username}',
                      style=_RED_FLAG if self.user_data.is_in_usl else None)
        self.update(table)
