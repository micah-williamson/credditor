from rich.style import Style
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.validation import Function
from textual.widgets import Static, Button, Input, Footer

from models.user_data import UserData
from screens.load_user_screen import LoadUserScreen
from screens.user_screen import UserScreen


class CredditorApp(App):
    CSS_PATH = 'main.tcss'

    BINDINGS = [
        Binding(key="escape", action="quit", description="Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Static(id="login_box"):
            yield Input(
                id='username_input',
                placeholder='u/username',
                validators=[
                    Function(lambda v: v.startswith('u/'), 'Must start with u/'),
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

        self.push_screen(LoadUserScreen(username_input.value), self._handle_load_user_result)

    def _handle_load_user_result(self, user_data: UserData) -> None:
        self.push_screen(UserScreen(user_data))
        pass


def main():
    app = CredditorApp()
    app.run()


if __name__ == '__main__':
    main()
