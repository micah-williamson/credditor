import datetime

from ollama import chat, Options
from ollama import ChatResponse


def extract_borrow_request(post_date: datetime.date, post_title: str):
    with open('ai/extract_borrow_request.prompt', 'r') as f:
        prompt = f.read()

    options = Options()
    options.temperature = 0

    query = f'(Post Date: {post_date}) {post_title}'

    response: ChatResponse = chat(
        model='llama3.2',
        options=options,
        messages=[
            {
                'role': 'system',
                'content': prompt,
            },
            {
                'role': 'user',
                'content': query
            }
        ])
    print(response)
    return response.message.content
