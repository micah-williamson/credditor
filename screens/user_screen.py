from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Button, ContentSwitcher, Label, Rule, Static

from models.save_state import SaveState
from models.user_data import UserData
from screens.load_user_screen import LoadUserScreen
from util.date import humanize
from widgets.loan_history_widget import LoanHistoryWidget
from widgets.reddit_activity_widget import RedditActivityWidget
from widgets.user_info_widget import UserInfoWidget

# Requirements
_MIN_KARMA = 2000
_MIN_COMMENT_KARMA = 800
_MIN_AGE_DAYS = 120


class UserScreen(Screen):
    BINDINGS = [
        Binding(key='escape', action='go_back', description='Go back'),
    ]

    def __init__(self, user_data: UserData) -> None:
        self.user_data = user_data
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(classes='header'):
            with Horizontal(classes='ghostpanel autoheight'):
                with Vertical(classes='autoheight'):
                    yield Label('Username')
                    yield Label(self.user_data.username)
                with Vertical(classes='autoheight'):
                    yield Label('Last Data Fetch')
                    yield Label(humanize(self.user_data.last_load))
                with Vertical(classes='autoheight'):
                    yield Button('Refresh', classes='compact', action='screen.refresh_user')

            yield Rule()

            with Horizontal(classes='ghostpanel autoheight'):
                yield Button('User Info', id='user_info')
                yield Button('Reddit Activity', id='reddit_activity')
                yield Button('Loan History', id='loan_history')

            with ContentSwitcher(id='user_screen_content', initial='user_info', classes='panel'):
                yield UserInfoWidget(id='user_info', user_data=self.user_data)
                yield RedditActivityWidget(id='reddit_activity', user_data=self.user_data)
                yield LoanHistoryWidget(id='loan_history', user_data=self.user_data)

        yield Footer(show_command_palette=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one(ContentSwitcher).current = event.button.id

    def _action_refresh_user(self):
        username = self.user_data.username

        load_user_settings = SaveState.load_user_settings
        load_user_settings.username = username

        self.app.push_screen(LoadUserScreen(load_user_settings), self._handle_refresh_user_result)

    def _handle_refresh_user_result(self, user_data: UserData) -> None:
        SaveState.user_data[user_data.username] = user_data
        SaveState.save()
        self.user_data = user_data
        self.refresh(recompose=True)

    def _action_go_back(self):
        self.dismiss()
