import datetime
import sys

from ai.borrow_request_extractor import extract_borrow_request


def main():
    post_title = sys.argv[1]
    if len(sys.argv) > 2:
        post_date = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d').date()
    else:
        post_date = datetime.datetime.now().date()

    ai_out = extract_borrow_request(post_date, post_title)
    print(ai_out)


if __name__ == '__main__':
    main()
