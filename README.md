# AI-Resilient Smart Coding Assessment Portal

A college-project Django portal where faculty author coding assessments and review both hidden-test scores and code-history evidence. Process logs support review only; they do **not** detect or prove AI use.

## Quick start

1. Create and activate a virtual environment.
2. Run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set Judge0 details if needed.
4. Run `python manage.py migrate`.
5. Run `python manage.py createsuperuser` (optional for Django admin).
6. Run `python manage.py runserver` and open `http://127.0.0.1:8000/`.

## Demo users

Use Django admin to create users. A Profile is created automatically; set its role to `faculty` or `student`. Faculty then create an assessment, assign students, add questions/tests, and publish it.

## Judge0

Execution is sent to Judge0 only; no student code is executed by Django. The Run action uses just the first non-hidden sample test. Submit uses hidden tests and returns only aggregate pass count and score. The public Judge0 endpoint can be rate-limited; configure `JUDGE0_URL` and `JUDGE0_API_KEY` for a hosted provider in `.env`.

## Coding logs

The browser sends a snapshot every `CODE_LOG_INTERVAL_SECONDS` (default 30). The server saves it only when code differs from the previous snapshot and records line count plus simple function additions. A final snapshot is retained on submission.

## Faculty AI review

Faculty can request an optional logic review from the evaluation page. It sends the question, student source code, language, mark ceiling, automatic score, and aggregate hidden-test pass count to the configured OpenAI-compatible chat completions endpoint. Student identity and hidden test inputs/expected outputs are not sent. The review gives likely logic issues, a complexity estimate, confidence, and a tentative mark; it never changes the saved mark. Faculty must review the evidence and save any final manual mark themselves.

By default, AI review uses local Ollama and does not need an API key. Install Ollama, then download the configured model (default `qwen2.5-coder:3b`) with `ollama pull qwen2.5-coder:3b`. Keep Ollama running and leave `AI_REVIEW_PROVIDER=ollama` in `.env`. The default Ollama URL is `http://127.0.0.1:11434/api/chat`.

To use a cloud OpenAI-compatible provider instead, set `AI_REVIEW_PROVIDER=openai`, `AI_REVIEW_API_URL`, `AI_REVIEW_API_KEY`, and `AI_REVIEW_MODEL` in `.env`. Source code is sent to the selected provider when faculty request a review. The app does not send student identity or hidden test input/expected output; choose a provider whose data-handling terms are appropriate for student work.
