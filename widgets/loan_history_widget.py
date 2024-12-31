from rich.table import Table
from textual.widgets import Static

from models.user_data import UserData


class LoanHistoryWidget(Static):

    def __init__(self, user_data: UserData, **kwargs):
        self.user_data = user_data
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        user = self.user_data.user
        loan_history = self.user_data.loan_history

        def _highlight_inspected_user(username: str) -> str:
            return f'[bold blue]{username}[/]' if username.lower() == user.name.lower() else username

        def _warn_if(value, predicate):
            return f'[yellow]{value}[/]' if predicate() else str(value)

        table = Table()
        table.add_column('status')
        table.add_column('lender')
        table.add_column('borrower')
        table.add_column('cur')
        table.add_column('amt', justify='right')
        table.add_column('repaid', justify='right')
        table.add_column('borrow dt', justify='right')
        table.add_column('repay dt', justify='right')
        table.add_column('req dt', justify='right')
        table.add_column('req amt', justify='right')
        table.add_column('rq repay amt', justify='right')
        table.add_column('rq repay dt', justify='right')
        table.add_column('link')

        for row in loan_history:
            table.add_row(
                '[red bold]Unpaid[/]' if row.repaid_date is None else '[green bold]Paid[/]',
                _highlight_inspected_user(row.lender),
                _highlight_inspected_user(row.borrower),
                row.currency_code,
                str(row.borrow_amount),
                str(row.repaid_amount),
                str(row.borrow_date),
                str(row.repaid_date),
                _warn_if(row.loan_request.created_at,
                         lambda: row.loan_request.created_at != row.borrow_date),
                _warn_if(row.loan_request.borrow_amount,
                         lambda: row.loan_request.borrow_amount != row.borrow_amount),
                str(row.loan_request.repay_amount),
                _warn_if(row.loan_request.repay_date,
                         lambda: row.loan_request.repay_date is not None and row.repaid_date is not None and row.loan_request.repay_date < row.repaid_date),
                f'[link={row.loan_request.permalink}]post[/]',
            )

        self.update(table)
