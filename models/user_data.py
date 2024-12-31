import datetime
from dataclasses import dataclass
from typing import List, Optional

import asyncpraw.models


@dataclass
class LoanRequest:
    created_at: datetime.date
    permalink: str
    post_id: str

    # It's not always possible to extract the borrow details from the post so these fields are
    # optional
    borrow_amount: Optional[float]
    repay_amount: Optional[float]
    repay_date: Optional[datetime.date]


@dataclass
class UserLoan:
    lender: str
    borrower: str
    currency_code: str
    borrow_amount: float
    borrow_date: datetime.date

    # True if the searched user is the borrower on this loan
    is_borrower: bool

    # Date will be None and amount will be 0.0 if the loan has not yet been repaid
    repaid_date: Optional[datetime.date]
    repaid_amount: float

    # The details of the loan are the source of truth but may differ from the original request
    loan_request: LoanRequest


@dataclass
class UserData:
    user: asyncpraw.models.Redditor
    comments: List[asyncpraw.models.Comment]
    loan_history: List[UserLoan]

    # If the user is in the universal scammer list
    is_in_usl: bool