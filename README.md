credditor
---------

Combines results from reddit, redditloans, and universal scan list APIs and produces a user report
in terminal.

- UI: [Textual](https://textual.textualize.io/).
- Reddit API: [PRAW](https://asyncpraw.readthedocs.io/en/stable/)
- Loan data: [LoansBot](https://github.com/LoansBot/loansbot)

## Usage

Load reddit user data by username
![Homescreen](./docs/homescreen.png)

See user overview, reddit activity, and loan history
![User info](./docs/userinfo.png)
![Reddit activity](./docs/redditactivity.png)
![Loan history](./docs/loanhistory.png)

## Setup & Run

- `python3 -m venv {path_to_project}`
- Run activate script from scripts dir
- Copy `.env.tpl` to `.env` and add reddit app credentials
- Install python requirements `pip3 install -r requirements.txt`
- Download [ollama](https://github.com/ollama/ollama?tab=readme-ov-file)
- Run `ollama pull llama3.2`
- Run with `python main.py {user_name}`

## Develop

Because Textual uses the terminal to display the UI you need a second terminal to see logs.

- Terminal A: `textual console`
- Terminal B: `textual run --dev main.py`

![Dev Mode](./docs/devmode.png)

## Troubleshooting

- If the app fails to start with a dacite error then delete the `data/` dir and try again