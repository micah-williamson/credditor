import re
import time
import datetime
from collections import defaultdict
from typing import List

import praw
import praw.models
import os

import arrow
from dotenv import load_dotenv
import plotext as plt
import requests
from rich.console import Console
from rich.progress import Progress
from rich.style import Style
from rich.table import Table

# Add reddit username here (without u/)
_INSPECT_USER = ''

# Requirements
_MIN_KARMA = 2000
_MIN_COMMENT_KARMA = 800
_MIN_AGE_DAYS = 120

# Settings
_ACTIVITY_DAYS_BACK = 365
_COMMENT_LIMIT = 1000

# Common Styles
_RED_FLAG = Style(color='red', bold=True)


def main():
    load_dotenv()
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')

    os.system('cls' if os.name == 'nt' else 'clear')

    console = Console()
    console.rule()

    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent='cledditor'
    )

    with Progress() as progress:
        task1 = progress.add_task('Fetching User Info')
        task2 = progress.add_task('Fetching Comment History')
        task3 = progress.add_task('Fetching Loan History')

        # Fetching User Info
        user: praw.models.Redditor = reddit.redditor(_INSPECT_USER)
        user_in_usl = _fetch_in_usl(user.name)
        progress.update(task1, completed=100.0)

        # Fetching Comment History
        date_floor = datetime.datetime.now() - datetime.timedelta(days=_ACTIVITY_DAYS_BACK)
        comment_buffer = []
        for comment in user.comments.new(limit=_COMMENT_LIMIT):
            comment_buffer.append(comment)
            progress.update(task2, completed=(len(comment_buffer) / _COMMENT_LIMIT) * 100)
        comments: List[praw.models.Comment] = [x for x in comment_buffer if
                                               datetime.datetime.fromtimestamp(
                                                   x.created_utc) >= date_floor]
        progress.update(task2, completed=100.0)

        # Fetching Loan History
        loan_ids = _fetch_loan_ids()
        loan_activity = []
        for loan_id in loan_ids:
            loan_activity.append(_fetch_loan_details(reddit, loan_id))
            progress.update(task3, completed=(len(loan_activity) / len(loan_ids)) * 100)
        loan_activity.sort(key=lambda r: r['basic']['created_at'])
        progress.update(task3, completed=100.0)

    console.rule()
    _render_user_info(console, user, user_in_usl)

    console.rule()
    _render_activity_history(console, comments)

    console.rule()
    _render_loan_history(console, user, loan_activity)


def _render_user_info(console: Console, user: praw.models.Redditor, user_in_usl: bool):
    table = Table(title='User Details')
    table.add_column('field')
    table.add_column('value')
    table.add_column('')

    now = time.time()
    age = now - user.created
    age_days = round(age / 86400)

    table.add_row('Name', user.name)
    table.add_row('Account Age', str(age_days),
                  style=_RED_FLAG if age_days < _MIN_AGE_DAYS else None)
    table.add_row('Total Karma', str(user.total_karma),
                  style=_RED_FLAG if user.total_karma < _MIN_KARMA else None)
    table.add_row('Comment Karma', str(user.comment_karma),
                  style=_RED_FLAG if user.comment_karma < _MIN_COMMENT_KARMA else None)
    table.add_row('USL Status', 'FOUND' if user_in_usl else 'NOT FOUND',
                  f'https://www.universalscammerlist.com/?username={user.name}',
                  style=_RED_FLAG if user_in_usl else None)

    console.print(table)


def _render_loan_history(console: Console, user: praw.models.Redditor, loan_activity: list):
    def _highlight_inspected_user(username: str) -> str:
        return f'[bold blue]{username}[/]' if username.lower() == user.name.lower() else username

    def _warn_if(value, predicate):
        return f'[yellow]{value}[/]' if predicate() else str(value)

    table = Table(title='Loan History')
    table.add_column('status')
    table.add_column('lender')
    table.add_column('borrower')
    table.add_column('currency')
    table.add_column('ask_borrow_amount', justify='right')
    table.add_column('ask_repay_amount', justify='right')
    table.add_column('ask_repay_date', justify='right')
    table.add_column('borrow_amount', justify='right')
    table.add_column('repaid_amount', justify='right')
    table.add_column('borrow_date', justify='right')
    table.add_column('repaid_date', justify='right')
    table.add_column('permalink')

    for row in loan_activity:
        basic = row['basic']
        currency_exponent = basic['currency_exponent']
        currency_divisor = 10 ** currency_exponent

        borrow_amount = basic['principal_minor'] / currency_divisor
        repaid_amount = basic['principal_repayment_minor'] / currency_divisor

        borrow_date = datetime.datetime.fromtimestamp(basic['created_at']).date()
        repaid_date = datetime.datetime.fromtimestamp(basic['repaid_at']).date() \
            if basic['repaid_at'] is not None else None

        ask_borrow_amount = basic['ask_borrow_amount']
        ask_repay_amount = basic['ask_repay_amount']
        ask_repay_date = basic['ask_repay_date']

        table.add_row(
            '[red bold]Unpaid[/]' if repaid_date is None else '[green bold]Paid[/]',
            _highlight_inspected_user(basic['lender']),
            _highlight_inspected_user(basic['borrower']),
            basic['currency_code'],
            _warn_if(ask_borrow_amount, lambda: ask_borrow_amount != borrow_amount),
            _warn_if(ask_repay_amount, lambda: ask_repay_amount != repaid_amount),
            _warn_if(ask_repay_date,
                     lambda: ask_repay_date is not None and ask_repay_date < repaid_date),
            str(borrow_amount),
            str(repaid_amount),
            str(borrow_date),
            str(repaid_date),
            row['creation_event']['creation_permalink'],
        )

    console.print(table)


def _render_activity_history(console: Console, comments: List[praw.models.Comment]):
    plt.canvas_color('black')
    plt.axes_color('black')
    plt.ticks_color('red')

    # Top 10 subreddits
    subreddit_counter = defaultdict(int)
    for comment in comments:
        subreddit_counter[comment.subreddit_name_prefixed] += 1
    counts = list(subreddit_counter.items())
    counts.sort(key=lambda c: c[1], reverse=True)
    top_10 = counts[:10]

    plt.clear_data()
    plt.title('Top subreddit')
    plt.bar([c[0] for c in top_10], [c[1] for c in top_10])
    plt.show()

    console.line(1)

    # Activity Line Chats
    _plot_activity(comments)
    console.line(1)
    _plot_activity(comments, days_back=60)


def _fetch_loan_ids():
    lend_history = f"https://redditloans.com/api/loans?lender_name={_INSPECT_USER}"
    lend_ids = requests.get(lend_history).json()

    borrow_history = f"https://redditloans.com/api/loans?borrower_name={_INSPECT_USER}"
    borrow_ids = requests.get(borrow_history).json()

    return lend_ids + borrow_ids


def _fetch_loan_details(reddit: praw.Reddit, loan_id: int):
    # Fetch loan details from loans API
    loan_url = f"https://redditloans.com/api/loans/{loan_id}/detailed"
    record = requests.get(loan_url).json()
    for event in record['events']:
        if event['event_type'] == 'creation':
            record['creation_event'] = event
    record['is_borrower'] = _INSPECT_USER.lower() == record['basic']['borrower']

    # Fetch additional details from reddit comment
    record['basic']['ask_borrow_amount'] = None
    record['basic']['ask_repay_amount'] = None
    record['basic']['ask_repay_date'] = None

    res = re.match('https://www.reddit.com/comments/([^/]+)',
                   record['creation_event']['creation_permalink'])
    post_id = res.group(1)
    post = reddit.submission(post_id)

    try:
        borrow_res = re.match(r'.*]\s*\(([^)]+)\)', post.title,
                              re.RegexFlag.IGNORECASE | re.RegexFlag.U)
        if borrow_res:
            borrow_amount_s = borrow_res.group(1)
            record['basic']['ask_borrow_amount'] = _normalize_payment_amount(borrow_amount_s)

        repay_res = re.match(r'.*\(repay(.*)(by|on)([^)]+)\)', post.title,
                             re.RegexFlag.IGNORECASE | re.RegexFlag.U)
        if repay_res:
            repay_amount_s = repay_res.group(1)
            repay_date_s = repay_res.group(3)
            record['basic']['ask_repay_amount'] = _normalize_payment_amount(repay_amount_s)
            record['basic']['ask_repay_date'] = _try_parse_date(repay_date_s)
    except Exception as e:
        raise Exception(f'Failed to parse: {post.title}') from e

    return record


def _fetch_in_usl(username: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'
    }
    res = requests.get(
        f'https://api.reddit.com/r/RegExrSwapBot/wiki/confirmations/{username.lower()}.json',
        headers=headers,
    )
    return res.status_code != 404


def _plot_activity(points: List[praw.models.Comment], days_back=_ACTIVITY_DAYS_BACK):
    start_day = (datetime.datetime.now() - datetime.timedelta(days=days_back)).date()
    end_day = datetime.datetime.now().date()

    # Trim and normalize point data
    points = [datetime.datetime.fromtimestamp(p.created_utc).date() for p in points]
    points = [p for p in points if p >= start_day]

    # Fill buckets
    buckets = {start_day + datetime.timedelta(days=i): 0 for i in range(days_back + 1)}
    for point in points:
        buckets[point] += 1

    # Plot
    plt.clear_data()
    plt.title(f'Activity Chart [Last {days_back} Days]')
    plt.plot([(d - end_day).days for d in buckets.keys()], buckets.values())
    plt.xlabel('Date')
    plt.ylabel('Activity')

    plt.show()


def _try_parse_date(date_string: str):
    date_formats = [
        "YYYY-MM-DD",
        "DD-MM-YYYY",
        "MM/DD/YYYY",
        "MM/DD/YY",
        "MM/D/YY",
        "M/DD/YY",
        "M/D/YY",
        "YYYY/MM/DD",
        "DD MMM YYYY",
        "MMM DD, YYYY",
        "DD.MM.YYYY",
    ]
    for date_format in date_formats:
        try:
            parsed_date = arrow.get(date_string, date_format).date()
            return parsed_date
        except arrow.parser.ParserError as e:
            continue
    return None


def _normalize_payment_amount(p: str):
    return int(re.sub(r'[^\d\\.]', '', p.strip()))


if __name__ == '__main__':
    main()
