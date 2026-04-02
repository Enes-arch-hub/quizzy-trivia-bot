import streamlit as st
import anthropic

st.set_page_config(
    page_title="Quizzy — Trivia Bot",
    page_icon="🎯",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0e0e12;
}

section.main > div {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.quizzy-header {
    text-align: center;
    margin-bottom: 2rem;
}

.quizzy-header h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 3rem;
    color: #f0e940;
    letter-spacing: -1px;
    line-height: 1;
    margin: 0;
}

.quizzy-header p {
    font-size: 1rem;
    color: #7a7a8c;
    margin-top: 0.4rem;
}

.score-bar {
    display: flex;
    justify-content: center;
    gap: 2rem;
    background: #1a1a24;
    border: 1px solid #2a2a38;
    border-radius: 50px;
    padding: 0.6rem 2rem;
    margin-bottom: 1.5rem;
    width: fit-content;
    margin-left: auto;
    margin-right: auto;
}

.score-item {
    text-align: center;
}

.score-num {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #f0e940;
}

.score-label {
    font-size: 0.7rem;
    color: #7a7a8c;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.chat-bubble-bot {
    background: #1a1a24;
    border: 1px solid #2a2a38;
    border-radius: 18px;
    border-bottom-left-radius: 4px;
    padding: 0.9rem 1.2rem;
    color: #e8e8f0;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 0.5rem;
    max-width: 85%;
}

.chat-bubble-user {
    background: #f0e940;
    border-radius: 18px;
    border-bottom-right-radius: 4px;
    padding: 0.9rem 1.2rem;
    color: #0e0e12;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 0.5rem;
    max-width: 85%;
    margin-left: auto;
}

.bubble-row-bot {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 0.4rem;
}

.bubble-row-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.4rem;
}

.chat-container {
    background: #13131c;
    border: 1px solid #2a2a38;
    border-radius: 16px;
    padding: 1.2rem;
    min-height: 320px;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

.stTextInput input {
    background: #1a1a24 !important;
    border: 1px solid #2a2a38 !important;
    border-radius: 50px !important;
    color: #e8e8f0 !important;
    padding: 0.6rem 1.2rem !important;
    font-family: 'DM Sans', sans-serif !important;
}

.stTextInput input:focus {
    border-color: #f0e940 !important;
    box-shadow: 0 0 0 2px rgba(240,233,64,0.15) !important;
}

.stButton button {
    background: #f0e940 !important;
    color: #0e0e12 !important;
    border: none !important;
    border-radius: 50px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.15s !important;
}

.stButton button:hover {
    opacity: 0.85 !important;
}

div[data-testid="column"] .stButton button {
    width: 100%;
    font-size: 0.85rem !important;
    padding: 0.4rem 0.8rem !important;
    background: #1a1a24 !important;
    color: #e8e8f0 !important;
    border: 1px solid #2a2a38 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 50px !important;
}

div[data-testid="column"] .stButton button:hover {
    border-color: #f0e940 !important;
    color: #f0e940 !important;
    background: #1a1a24 !important;
    opacity: 1 !important;
}

.category-grid {
    margin-bottom: 1rem;
}

.hint-text {
    text-align: center;
    color: #7a7a8c;
    font-size: 0.82rem;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are Quizzy, an energetic and witty trivia host. Your vibe: sharp, fun, never boring.

Rules:
- Ask ONE trivia question at a time with 4 options labeled A) B) C) D)
- After the user answers, react with energy (right/wrong), reveal the answer if wrong, then offer to continue
- Mix categories unless the user picks one
- Vary difficulty — easy warmups, hard ones to keep it spicy
- Keep responses concise and punchy
- At the END of every response where you evaluate an answer, add exactly one of these tags on its own line:
  [CORRECT] — if the user got it right
  [WRONG] — if the user got it wrong
  [NEUTRAL] — for any other response (greetings, category picks, etc.)
- Never put anything after the tag line"""

CATEGORIES = ["🌍 Geography", "🔬 Science", "🎬 Pop Culture", "⚽ Sports", "📜 History", "🎵 Music", "🍕 Food & Drink", "🎲 Random Mix"]

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "total" not in st.session_state:
        st.session_state.total = 0
    if "started" not in st.session_state:
        st.session_state.started = False
    if "pending_send" not in st.session_state:
        st.session_state.pending_send = None

def get_reply(user_text):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    history = []
    for m in st.session_state.messages:
        history.append({"role": m["role"], "content": m["content"]})
    history.append({"role": "user", "content": user_text})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=history,
    )
    return response.content[0].text

def process_reply(reply):
    tag = None
    clean = reply
    for t in ["[CORRECT]", "[WRONG]", "[NEUTRAL]"]:
        if t in reply:
            tag = t
            clean = reply.replace(t, "").strip()
            break
    if tag == "[CORRECT]":
        st.session_state.score += 1
        st.session_state.total += 1
    elif tag == "[WRONG]":
        st.session_state.total += 1
    return clean

def send(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    reply = get_reply(user_text)
    clean = process_reply(reply)
    st.session_state.messages.append({"role": "assistant", "content": clean})

init_state()

st.markdown('<div class="quizzy-header"><h1>QUIZZY</h1><p>the trivia bot that keeps score</p></div>', unsafe_allow_html=True)

pct = int((st.session_state.score / st.session_state.total * 100)) if st.session_state.total > 0 else 0
st.markdown(f"""
<div class="score-bar">
  <div class="score-item"><div class="score-num">{st.session_state.score}</div><div class="score-label">Correct</div></div>
  <div class="score-item"><div class="score-num">{st.session_state.total}</div><div class="score-label">Played</div></div>
  <div class="score-item"><div class="score-num">{pct}%</div><div class="score-label">Accuracy</div></div>
</div>
""", unsafe_allow_html=True)

chat_html = '<div class="chat-container">'
for m in st.session_state.messages:
    text = m["content"].replace("\n", "<br>")
    if m["role"] == "assistant":
        chat_html += f'<div class="bubble-row-bot"><div class="chat-bubble-bot">{text}</div></div>'
    else:
        chat_html += f'<div class="bubble-row-user"><div class="chat-bubble-user">{text}</div></div>'
if not st.session_state.messages:
    chat_html += '<div style="color:#7a7a8c;font-size:0.9rem;text-align:center;margin-top:6rem;">Pick a category below or type to start!</div>'
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

if not st.session_state.started:
    st.markdown('<div class="category-grid">', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, cat in enumerate(CATEGORIES):
        with cols[i % 4]:
            if st.button(cat, key=f"cat_{i}"):
                st.session_state.started = True
                st.session_state.pending_send = f"Let's play! Category: {cat}. Fire away!"
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
with col1:
    user_input = st.text_input("", placeholder="Type your answer or message...", label_visibility="collapsed", key="input_box")
with col2:
    send_clicked = st.button("Send")

if st.session_state.pending_send:
    msg = st.session_state.pending_send
    st.session_state.pending_send = None
    with st.spinner("Quizzy is thinking..."):
        send(msg)
    st.rerun()

if (send_clicked or user_input) and user_input.strip():
    st.session_state.started = True
    with st.spinner("Quizzy is thinking..."):
        send(user_input.strip())
    st.rerun()

if st.session_state.messages:
    st.markdown('<p class="hint-text">Type A, B, C, or D — or just say "next question" anytime</p>', unsafe_allow_html=True)

if st.session_state.messages:
    if st.button("🔄 Reset Game", key="reset"):
        st.session_state.messages = []
        st.session_state.score = 0
        st.session_state.total = 0
        st.session_state.started = False
        st.rerun()
