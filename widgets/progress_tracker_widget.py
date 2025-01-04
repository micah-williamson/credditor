from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, ProgressBar, Label


class ProgressTrackerWidget(Static):
    def compose(self) -> ComposeResult:
        with Vertical(id="progress_container"):
            with Static(classes="progress_row"):
                yield Static(classes="gutter")
                yield Label('User Info')
                yield ProgressBar(id='user_info', total=100)
                yield Static(classes="gutter")
            with Static(classes="progress_row"):
                yield Static(classes="gutter")
                yield Label('Reddit Activity')
                yield ProgressBar(id='reddit_activity', total=100)
                yield Static(classes="gutter")
            with Static(classes="progress_row"):
                yield Static(classes="gutter")
                yield Label('Loan History')
                yield ProgressBar(id='loan_history', total=100)
                yield Static(classes="gutter")

    def update(self, user_info: Optional[float] = None, reddit_activity: Optional[float] = None,
               loan_history: Optional[float] = None) -> None:
        if user_info is not None:
            self.query_one('#user_info', ProgressBar).update(progress=user_info)
        if reddit_activity is not None:
            self.query_one('#reddit_activity', ProgressBar).update(progress=reddit_activity)
        if loan_history is not None:
            self.query_one('#loan_history', ProgressBar).update(progress=loan_history)
        self.refresh()
