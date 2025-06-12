# AILearn

## ChatGPT Demo

This repository includes a small Django project located in `chatgpt_project`.
It shows how to build a simple chat interface that talks to OpenAI's API (or
echoes the input when the API is unavailable).

To run the server:

```bash
cd chatgpt_project
python3 manage.py migrate  # create SQLite database
python3 manage.py runserver
```

Then open `http://localhost:8000/` in your browser.

