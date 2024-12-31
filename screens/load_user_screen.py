import datetime
import os
import re
from typing import List

import asyncpraw
import asyncpraw.models
from dotenv import load_dotenv
from textual.app import ComposeResult
from textual.screen import Screen
import aiohttp

from const import ACTIVITY_DAYS_BACK, COMMENT_LIMIT
from models.load_user_settings import LoadUserSettings
from models.user_data import UserData, UserLoan, LoanRequest, Comment
from widgets.progress_tracker_widget import ProgressTrackerWidget


class LoadUserScreen(Screen):

    def __init__(self, load_user_settings: LoadUserSettings) -> None:
        self.username = load_user_settings.username
        super().__init__()

    def on_mount(self):
        self._user_data = None
        self.run_worker(self._load_user())

        def _check_for_load():
            if self._user_data is not None:
                self.dismiss(self._user_data)

        self.set_interval(0.3, _check_for_load)

    def compose(self) -> ComposeResult:
        yield ProgressTrackerWidget()

    async def _load_user(self) -> None:
        progress_tracker = self.query_one(ProgressTrackerWidget)

        load_dotenv()
        CLIENT_ID = os.getenv('CLIENT_ID')
        CLIENT_SECRET = os.getenv('CLIENT_SECRET')

        reddit = asyncpraw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent='cledditor'
        )

        # Fetching User Info
        user: asyncpraw.models.Redditor = await reddit.redditor(self.username)
        await user.load()
        progress_tracker.update(user_info=50.0)
        user_in_usl = await self._fetch_in_usl(user.name)
        progress_tracker.update(user_info=100.0)

        # Fetching Comment History
        date_floor = (
                datetime.datetime.today() - datetime.timedelta(days=ACTIVITY_DAYS_BACK)).date()
        comments: List[Comment] = []
        comment: asyncpraw.models.Comment
        async for comment in user.comments.new(limit=COMMENT_LIMIT):
            comments.append(Comment(
                id=comment.id,
                subreddit=comment.subreddit.display_name,
                created_at=datetime.datetime.fromtimestamp(comment.created_utc).date(),
                karma=comment.score
            ))
            progress_tracker.update(reddit_activity=(len(comments) / COMMENT_LIMIT) * 100)
        comments = [c for c in comments if c.created_at >= date_floor]
        progress_tracker.update(reddit_activity=100.0)

        # Fetching Loan History
        loan_ids = await self._fetch_loan_ids(user)
        loan_history = []
        for loan_id in loan_ids:
            loan_history.append(await self._fetch_loan_details(reddit, user, loan_id))
            progress_tracker.update(loan_history=(len(loan_history) / len(loan_ids)) * 100)
        loan_history.sort(key=lambda r: r.borrow_date)
        progress_tracker.update(loan_history=100.0)

        self._user_data = UserData(
            last_load=datetime.datetime.now(),
            last_viewed=datetime.datetime.now(),
            username=user.name,
            created_at=datetime.datetime.fromtimestamp(user.created).date(),
            total_karma=user.total_karma,
            comment_karma=user.comment_karma,
            comments=comments,
            loan_history=loan_history,
            is_in_usl=user_in_usl
        )

    async def _fetch_loan_ids(self, user: asyncpraw.models.Redditor):
        async with aiohttp.ClientSession() as session:
            lend_history = f"https://redditloans.com/api/loans?lender_name={user.name}"
            res = await session.get(lend_history)
            lend_ids = await res.json()

            borrow_history = f"https://redditloans.com/api/loans?borrower_name={user.name}"
            res = await session.get(borrow_history)
            borrow_ids = await res.json()

        return lend_ids + borrow_ids

    async def _fetch_loan_details(self, reddit: asyncpraw.Reddit, user: asyncpraw.models.Redditor,
                                  loan_id: int) -> UserLoan:
        async with aiohttp.ClientSession() as session:
            # Fetch loan details from loans API
            loan_url = f"https://redditloans.com/api/loans/{loan_id}/detailed"
            res = await session.get(loan_url)
            record = await res.json()
            basic = record['basic']

            currency_exponent = basic['currency_exponent']
            currency_divisor = 10 ** currency_exponent

            lender = basic['lender']
            borrower = basic['borrower']
            currency_code = basic['currency_code']
            borrow_amount = basic['principal_minor'] / currency_divisor
            repaid_amount = basic['principal_repayment_minor'] / currency_divisor
            borrow_date = datetime.datetime.fromtimestamp(basic['created_at']).date()
            repaid_date = datetime.datetime.fromtimestamp(basic['repaid_at']).date() \
                if basic['repaid_at'] is not None else None
            is_borrower = user.name.lower() == borrower.lower()

            # Fetch loan request details
            loan_request_borrow_amount = None
            loan_request_repay_amount = None
            loan_request_repay_date = None

            for event in record['events']:
                if event['event_type'] == 'creation':
                    creation_event = event
                    break
            assert (creation_event is not None)

            loan_request_permalink = creation_event['creation_permalink']

            res = re.match('https://www.reddit.com/comments/([^/]+)',
                           loan_request_permalink)
            post_id = res.group(1)
            post = await reddit.submission(post_id)
            loan_request_created_at = datetime.datetime.fromtimestamp(post.created_utc).date()

            try:
                borrow_res = re.match(r'.*?]\s*\(([^)]+?)\)', post.title,
                                      re.RegexFlag.IGNORECASE)
                if borrow_res:
                    borrow_amount_s = borrow_res.group(1)
                    loan_request_borrow_amount = self._normalize_payment_amount(borrow_amount_s)

                repay_res = re.match(r'.*\(repay([^)]+?)(\(|,|by|on)([^)]+?)\)', post.title,
                                     re.RegexFlag.IGNORECASE)
                if repay_res:
                    created_date = datetime.datetime.fromtimestamp(
                        record['basic']['created_at']).date()
                    repay_amount_s = repay_res.group(1)
                    repay_date_s = repay_res.group(3)
                    loan_request_repay_amount = self._normalize_payment_amount(repay_amount_s)
                    loan_request_repay_date = self._try_parse_date(repay_date_s, created_date)
            except Exception as e:
                self.app.notify(
                    'Exception occurred parsing loan request post. Check logs for details',
                    severity='error')
                self.app.log.error(f'Failed to parse: {post.title}')
                self.app.log.error(f'Error: {e}')

            return UserLoan(
                lender=lender,
                borrower=borrower,
                currency_code=currency_code,
                borrow_amount=borrow_amount,
                repaid_amount=repaid_amount,
                borrow_date=borrow_date,
                repaid_date=repaid_date,
                is_borrower=is_borrower,
                loan_request=LoanRequest(
                    created_at=loan_request_created_at,
                    permalink=loan_request_permalink,
                    post_id=post_id,
                    borrow_amount=loan_request_borrow_amount,
                    repay_amount=loan_request_repay_amount,
                    repay_date=loan_request_repay_date
                )
            )

    async def _fetch_in_usl(self, username: str):
        async with aiohttp.ClientSession() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'
            })
            res = await session.get(
                f'https://api.reddit.com/r/RegExrSwapBot/wiki/confirmations/{username.lower()}.json')
            return res.status != 404

    def _try_parse_date(self, date_string: str, date_hint: datetime.date):
        month_variants = ['M', 'MM', 'MMM', 'MMMM']
        day_variants = ['D', 'DD', 'Do']
        year_variants = ['YY', 'YYYY']
        variants = []

        for m in month_variants:
            for d in day_variants:
                for y in year_variants:
                    variants.append((m, d, y))

        templates = [
            'YYYY-{M}-{D}',
            '{D}-{M}-YYYY',
            'YYYY/{M}/{D}',
            '{M}/{D}/{Y}',
            '{M} {D} {Y}',
            '{M}. {D} {Y}',
            '{M} {D}, {Y}',
            '{M}/{D}',
            '{M} {D}'
        ]

        date_formats = set()
        for template in templates:
            for variant in variants:
                (m, d, y) = variant
                date_formats.add(template.replace('{M}', m).replace('{D}', d).replace('{Y}', y))

        for date_format in date_formats:
            try:
                parsed_date = datetime.datetime.strptime(date_string, date_format).date()

                if parsed_date and parsed_date.year == 1:
                    # We parsed a date that was only a month/day (i.e. 12/25)
                    # We don't know what the year is, so we will guess based on the creation date
                    # Whichever guess is closer to the date_hint is the winner
                    guess_date_1 = datetime.date(date_hint.year, parsed_date.month, parsed_date.day)
                    guess_date_2 = datetime.date(date_hint.year + 1, parsed_date.month,
                                                 parsed_date.day)

                    if abs((guess_date_1 - date_hint).days) < abs((guess_date_2 - date_hint).days):
                        return guess_date_1
                    return guess_date_2

                return parsed_date
            except Exception as e:
                continue
        return None

    def _normalize_payment_amount(self, p: str):
        return float(re.sub(r'[^\d\\.]', '', p.strip()))
