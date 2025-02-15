from textual.app import App

from models.save_state import SaveState
from screens.home_screen import HomeScreen


class CredditorApp(App):
    CSS_PATH = [
        'main.tcss',
        'screens/home_screen.tcss',
        'screens/user_screen.tcss',
        'widgets/progress_tracker_widget.tcss',
        'widgets/reddit_activity_widget.tcss',
    ]

    def on_mount(self):
        self.push_screen(HomeScreen())


def main():
    SaveState.__cls_init__()
    app = CredditorApp()
    app.run()


if __name__ == '__main__':
    main()
