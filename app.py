"""StudyBuddy AI - Streamlit app that turns lecture notes into a summary,
flashcards or a quiz using a Large Language Model (Google Gemini)."""
import json
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)  # .env wins over stale system variables
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

SYSTEM = (
    "You are a helpful university tutor. Use ONLY the notes provided by the "
    "student. If the notes are too thin, say less rather than inventing facts. "
    "Respond with valid JSON only: no markdown, no commentary."
)

# Prompt engineering: one task description + strict output schema per mode.
PROMPTS = {
    "Summary": 'Return JSON: {"title": string, "bullets": [5-7 short key points], '
               '"keyTerms": [{"term": string, "def": string}] (max 5)}',
    "Flashcards": 'Return JSON: {"cards": [{"q": string, "a": string}]} with 8 flashcards.',
    "Quiz": 'Return JSON: {"questions": [{"q": string, "options": [4 strings], '
            '"answer": index 0-3, "why": string}]} with 5 multiple-choice questions.',
}

SAMPLE = (
    "Photosynthesis is the process by which plants, algae and some bacteria convert "
    "light energy into chemical energy. It takes place in chloroplasts, which contain "
    "chlorophyll. In the light-dependent reactions, light splits water, releasing oxygen "
    "and producing ATP and NADPH. In the Calvin cycle, which happens in the stroma, the "
    "plant uses ATP and NADPH to fix carbon dioxide into glucose. The overall equation "
    "is 6CO2 + 6H2O + light -> C6H12O6 + 6O2."
)


def parse_json(text: str) -> dict:
    """Parse model output, tolerating accidental ```json fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


def generate(mode: str, notes: str) -> dict:
    key = os.getenv("GEMINI_API_KEY", "")
    # Default: Gemini Developer API (Google AI Studio keys, which may start with "AQ.").
    # Set USE_VERTEX=true only for a Vertex AI project that has billing enabled.
    use_vertex = os.getenv("USE_VERTEX", "").strip().lower() == "true"
    client = genai.Client(vertexai=True, api_key=key) if use_vertex else genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=MODEL,
        contents=f"{PROMPTS[mode]}\n\nNOTES:\n{notes[:12000]}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            response_mime_type="application/json",  # forces JSON output
            max_output_tokens=2000,
        ),
    )
    return parse_json(resp.text)


def show_summary(r: dict):
    st.subheader(r.get("title", "Summary"))
    for b in r.get("bullets", []):
        st.markdown(f"- {b}")
    st.markdown("**Key terms**")
    for t in r.get("keyTerms", []):
        st.markdown(f"- **{t['term']}**: {t['def']}")


def show_cards(cards: list):
    if not cards:
        st.warning("No cards returned.")
        return
    i = st.session_state.card_i % len(cards)
    flipped = st.session_state.card_flip
    st.info(cards[i]["a"] if flipped else cards[i]["q"])
    st.caption(f"Card {i + 1} of {len(cards)} · {'answer' if flipped else 'question'}")
    c1, c2, c3 = st.columns(3)
    if c1.button("← Previous", use_container_width=True):
        st.session_state.card_i, st.session_state.card_flip = i - 1, False
        st.rerun()
    if c2.button("Flip", use_container_width=True):
        st.session_state.card_flip = not flipped
        st.rerun()
    if c3.button("Next →", use_container_width=True):
        st.session_state.card_i, st.session_state.card_flip = i + 1, False
        st.rerun()


def show_quiz(questions: list):
    score = answered = 0
    for n, q in enumerate(questions):
        st.markdown(f"**{n + 1}. {q['q']}**")
        pick = st.radio("Choose one", q["options"], index=None,
                        key=f"quiz_{n}", label_visibility="collapsed")
        if pick is not None:
            answered += 1
            if q["options"].index(pick) == q["answer"]:
                score += 1
                st.success("Correct! " + q.get("why", ""))
            else:
                st.error(f"Not quite. Answer: {q['options'][q['answer']]}. " + q.get("why", ""))
        st.divider()
    st.metric("Score", f"{score} / {len(questions)}")
    if answered == len(questions) and questions:
        st.balloons()


# ---------------------------- UI ----------------------------
st.set_page_config(page_title="StudyBuddy AI", page_icon="📚")
st.title("📚 StudyBuddy AI")
st.write("Paste lecture notes or a textbook passage. An LLM turns it into a "
         "summary, flashcards or a quiz.")

if not os.getenv("GEMINI_API_KEY"):
    st.error("GEMINI_API_KEY is missing. Add it to a .env file (see README) and restart.")
    st.stop()

st.text_area("Your notes", key="notes", height=200,
             placeholder="Paste your notes here (a few paragraphs works best)...")
st.button("Try sample text", on_click=lambda: st.session_state.update(notes=SAMPLE))
mode = st.radio("Output", list(PROMPTS), horizontal=True)

if st.button("Generate", type="primary"):
    notes = st.session_state.get("notes", "").strip()
    if len(notes) < 40:
        st.warning("Please paste a bit more text first.")
    else:
        with st.spinner("Thinking..."):
            try:
                st.session_state.result = generate(mode, notes)
                st.session_state.result_mode = mode
                st.session_state.card_i, st.session_state.card_flip = 0, False
                for k in [k for k in st.session_state if str(k).startswith("quiz_")]:
                    del st.session_state[k]
            except json.JSONDecodeError:
                st.error("The model returned an unexpected format. Try again.")
            except Exception as e:  # network, auth, rate limit...
                st.error(f"AI request failed: {e}")

result = st.session_state.get("result")
if result:
    shown = st.session_state.result_mode
    if shown == "Summary":
        show_summary(result)
    elif shown == "Flashcards":
        show_cards(result.get("cards", []))
    else:
        show_quiz(result.get("questions", []))

st.caption("AI can make mistakes. Check the output against your course material.")
