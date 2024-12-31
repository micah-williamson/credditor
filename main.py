from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.validation import Function
from textual.widgets import Static, Button, Input, Footer

from models.save_state import SaveState
from models.user_data import UserData
from screens.load_user_screen import LoadUserScreen
from screens.user_screen import UserScreen


class CredditorApp(App):
    CSS_PATH = 'main.tcss'

    BINDINGS = [
        Binding(key="escape", action="quit", description="Quit"),
    ]

    def compose(self) -> ComposeResult:
        load_user_settings = SaveState.load_user_settings
        with Static(id="login_box"):
            yield Input(
                id='username_input',
                placeholder='username',
                value=load_user_settings.username,
                validators=[
                    Function(lambda v: not v.startswith('u/'), 'Must not start with'),
                    Function(lambda v: len(v) > 2, 'Must be at least 3 chars')
                ],
            )
            yield Button(id='load_button', label='Load', action='app.load_user')
        yield Footer(show_command_palette=False)

    def _action_quit(self):
        self.exit()

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
            self.push_screen(LoadUserScreen(load_user_settings), self._handle_load_user_result)

    def _handle_load_user_result(self, user_data: UserData) -> None:
        SaveState.user_data[user_data.username] = user_data
        SaveState.save()
        self.push_screen(UserScreen(user_data))
        pass


def main():
    SaveState.__cls_init__()
    app = CredditorApp()
    app.run()


if __name__ == '__main__':
    main()
