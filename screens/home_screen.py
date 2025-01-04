import datetime
import time

import arrow
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import ScreenResume
from textual.screen import Screen
from textual.validation import Function
from textual.widgets import Footer, Button, Static, Input, Rule, Label, ListView, ListItem

from models.save_state import SaveState
from models.user_data import UserData
from screens.load_user_screen import LoadUserScreen
from screens.user_screen import UserScreen
from util.date import humanize


class HomeScreen(Screen):
    BINDINGS = [
        Binding(key="escape", action="quit", description="Quit"),
        Binding("enter", "handle_enter", "Enter", show=False),
        Binding("backspace", "handle_delete", "Delete", show=False),
    ]

    def compose(self) -> ComposeResult:
        load_user_settings = SaveState.load_user_settings

        # User Load Header
        with Static(classes="header"):
            with Horizontal(classes="ghostpanel autoheight"):
                yield Input(
                    id='username_input',
                    placeholder='username',
                    value=load_user_settings.username,
                    validators=[
                        Function(lambda v: not v.startswith('u/'), 'Must not start with'),
                        Function(lambda v: len(v) > 2, 'Must be at least 3 chars')
                    ],
                )
                yield Button(id='load_button', label='Load', action='screen.load_user')

        yield Rule()

        # Recently Loaded/Cached User Table

        with Static(classes='ghostpanel'):
            yield Label('Cached Users (by last viewed).')
            yield Label(
                'Use [↑][↓] to select a user. Use [Enter] to view or [Backspace ←] to delete.')

        with Static(classes='panel'):
            with Static(classes='cached_user_row'):
                yield Label('Username')
                yield Label('Last Data Fetch')
                yield Label('Last Viewed')
                yield Label('')

            yield ListView(id='cached_user_list', classes='autoheight')

        yield Footer(show_command_palette=False)

    def on_screen_resume(self, event_: ScreenResume):
        # Called anytime the screen is shown. Including when the screen stack is popped revealing
        # this screen
        self._refresh_user_list()

    @property
    def recent_users(self):
        users = list(SaveState.user_data.values())
        users.sort(key=lambda u: u.last_viewed, reverse=True)
        return users

    def _action_handle_delete(self):
        cached_user_list = self.query_one(ListView)
        selected_user = self.recent_users[cached_user_list.index]
        SaveState.user_data.pop(selected_user.username)
        SaveState.save()
        self._refresh_user_list()

    def on_list_view_selected(self, _event):
        cached_user_list = self.query_one(ListView)
        selected_user = self.recent_users[cached_user_list.index]
        self._handle_load_user_result(selected_user)

    def _action_quit(self):
        self.app.exit()

    def _action_load_user(self):
        username_input = self.query_one('#username_input', Input)

        if not username_input.is_valid:
            self.notify('Invalid reddit username')
            return

        username = username_input.value

        load_user_settings = SaveState.load_user_settings
        load_user_settings.username = username
        SaveState.save()

        if username in SaveState.user_data:
            # We already have data loaded for this user. We can skip loading it
            self._handle_load_user_result(SaveState.user_data[username])
        else:
            self.app.push_screen(LoadUserScreen(load_user_settings), self._handle_load_user_result)

    def _handle_load_user_result(self, user_data: UserData) -> None:
        SaveState.user_data[user_data.username] = user_data
        user_data.last_viewed = datetime.datetime.now()
        SaveState.save()
        self._refresh_user_list()
        self.app.push_screen(UserScreen(user_data))

    def _refresh_user_list(self):
        user_list = self.query_one('#cached_user_list', ListView)
        user_list.clear()
        for user in self.recent_users:
            list_item = ListItem(classes='cached_user_row')
            list_item.compose_add_child(Label(user.username))
            list_item.compose_add_child(Label(humanize(user.last_load)))
            list_item.compose_add_child(Label(humanize(user.last_viewed)))
            list_item.compose_add_child(Label(''))
            user_list.append(list_item)
