# StudyBuddy AI

A small Generative AI web app for university students. Paste lecture notes or a
textbook passage and a Large Language Model (Google Gemini) turns it into:

- **Summary**: key points and key terms
- **Flashcards**: flip-card revision
- **Quiz**: multiple-choice questions with instant feedback and explanations

## Use case
Students spend a lot of time converting notes into revision material. This app
automates that step so they can spend the time actually studying.

## GenAI / LLM concepts demonstrated
- **Prompt engineering**: a system prompt sets the tutor role; a separate task prompt per mode.
- **Grounding**: the model is told to use *only* the supplied notes, which reduces hallucination.
- **Structured output**: the model is set to JSON mode (`response_mime_type`) and must return JSON, which the front end renders as cards and quizzes.
- **Context-window management**: input is truncated to 12,000 characters.
- **LLM API integration**: a Streamlit app calls the Google Gemini API server-side, so the API key never reaches the browser.

## Architecture
```
Browser  <-->  Streamlit app (app.py)  -->  Gemini API (JSON mode)
                 renders summary / flashcards / quiz  <--  parsed JSON
```

## Run it
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your Gemini API key in .env
streamlit run app.py
```
Get a free key at https://aistudio.google.com/apikey, Streamlit opens the app in your browser (usually http://localhost:8501)

## API key note
`GEMINI_API_KEY` can be a Google AI Studio key or a Vertex AI express-mode key
(the app auto-detects keys starting with `AQ.`). If you get "API key not valid",
set `USE_VERTEX=true` or `USE_VERTEX=false` in `.env` to force the other mode.

## Limitations and ethics
- LLMs can make mistakes: students should verify output against course material.
- The app is a study aid, not a substitute for learning; it should not be used to generate work submitted as one's own.
- Pasted notes are sent to a third-party API, and on the free tier Google may use requests to improve its products; do not paste confidential data.

## Ideas for extension
PDF upload, difficulty levels, spaced-repetition scheduling, multilingual notes.
