from rich.table import Table
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Label

from models.user_data import UserData


class LoanHistoryWidget(Static):

    def __init__(self, user_data: UserData, **kwargs):
        self.user_data = user_data
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        loan_history_table = self.get_loan_history_table()
        with Vertical():
            yield Label(
                'Field marked in orange are [yellow]warnings[/]. The number after the | marks the corresponding field.')
            yield Label('')
            yield Label(
                '[u]Borrow Amount [1][/]: The rq borrow amount does not match the actual borrow amount. Possible difficulty in negotiating loan')
            yield Label(
                '[u]Borrow Date [2][/]: The post date does not match the borrowed date. Possible difficulty in negotiating loan')
            yield Label(
                '[u]Repay Date [3][/]: Loan was repaid after the rq repay date. Possible late payment')
            yield Label('')
            loan_history_container = Static()
            loan_history_container.update(loan_history_table)
            yield loan_history_container

    def get_loan_history_table(self) -> Table:
        loan_history = self.user_data.loan_history

        def _highlight_inspected_user(username: str) -> str:
            return f'[bold blue]{username}[/]' if username.lower() == self.user_data.username.lower() else username

        def _warn_if(value, flag: bool, match: int):
            return f'[yellow]{value}|{match}[/]' if flag else str(value)

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
        table.add_column('installments', justify='right')
        table.add_column('link')

        for row in loan_history:
            # User did not get the loan on the same day of request
            flag_borrow_date = row.loan_request.created_at != row.borrow_date
            # The borrow amount change from the request
            flag_borrow_amount = row.loan_request.borrow_amount != row.borrow_amount
            # The actual repay date is past the proposed repay date. Repayment may have been late
            flag_repay_date = row.loan_request.repay_date is not None and row.repaid_date is not None and row.loan_request.repay_date < row.repaid_date

            table.add_row(
                '[red bold]Unpaid[/]' if row.repaid_date is None else '[green bold]Paid[/]',
                _highlight_inspected_user(row.lender),
                _highlight_inspected_user(row.borrower),
                row.currency_code,
                _warn_if(row.borrow_amount, flag_borrow_amount, 1),
                str(row.repaid_amount),
                _warn_if(row.borrow_date, flag_borrow_date, 2),
                _warn_if(row.repaid_date, flag_repay_date, 3),
                _warn_if(row.loan_request.created_at, flag_borrow_date, 2),
                _warn_if(row.loan_request.borrow_amount, flag_borrow_amount, 1),
                str(row.loan_request.repay_amount),
                _warn_if(row.loan_request.repay_date, flag_repay_date, 3),
                str(len(
                    row.loan_request.repay_installments)) if row.loan_request.repay_installments else '?',
                f'[link={row.loan_request.permalink}]post[/]',
            )

        return table
