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

        user = self.user_data.user

        now = time.time()
        age = now - user.created
        age_days = round(age / 86400)

        table.add_row('Name', user.name)
        table.add_row('Account Age', str(age_days),
                      style=_RED_FLAG if age_days < _MIN_AGE_DAYS else None)
        table.add_row('Total Karma', str(user.total_karma),
                      style=_RED_FLAG if user.total_karma < _MIN_KARMA else None)
        table.add_row('Comment Karma', str(user.comment_karma),
                      style=_RED_FLAG if user.comment_karma < _MIN_COMMENT_KARMA else None)
        table.add_row('USL Status', 'FOUND' if self.user_data.is_in_usl else 'NOT FOUND',
                      f'https://www.universalscammerlist.com/?username={user.name}',
                      style=_RED_FLAG if self.user_data.is_in_usl else None)
        self.update(table)
