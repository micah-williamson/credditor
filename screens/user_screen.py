from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Button, ContentSwitcher

from models.user_data import UserData
from widgets.loan_history_widget import LoanHistoryWidget
from widgets.reddit_activity_widget import RedditActivityWidget
from widgets.user_info_widget import UserInfoWidget

# Requirements
_MIN_KARMA = 2000
_MIN_COMMENT_KARMA = 800
_MIN_AGE_DAYS = 120


class UserScreen(Screen):
    DEFAULT_CSS = """
    #user_screen_buttons {
        dock: top;
        height: auto;
    }
    
    #user_screen_content {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding(key='escape', action='go_back', description='Go back'),
    ]

    def __init__(self, user_data: UserData) -> None:
        self.user_data = user_data
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id='user_screen_buttons'):
            yield Button('User Info', id='user_info')
            yield Button('Reddit Activity', id='reddit_activity')
            yield Button('Loan History', id='loan_history')

        with ContentSwitcher(id='user_screen_content', initial='user_info'):
            yield UserInfoWidget(id='user_info', user_data=self.user_data)
            yield RedditActivityWidget(id='reddit_activity', user_data=self.user_data)
            yield LoanHistoryWidget(id='loan_history', user_data=self.user_data)

        yield Footer(show_command_palette=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one(ContentSwitcher).current = event.button.id

    def _action_go_back(self):
        self.dismiss()
