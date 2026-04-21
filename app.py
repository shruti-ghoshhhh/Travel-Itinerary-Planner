import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Travel Itinerary Planner", page_icon="✈️", layout="wide")

# ── PERFECTED UI CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0e1117;
    color: #fafafa;
}

.stApp { background-color: #0e1117; }

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #1a1d27;
    border-right: 1px solid #2d2f3e;
    width: 260px !important;
}
section[data-testid="stSidebar"] * { color: #e0e0e0; }

/* CENTER CONTENT */
.block-container {
    max-width: 980px !important;
    margin: 0 auto !important;
    padding-top: 2rem !important;
}

/* HEADER */
.main-heading {
    text-align: center;
    font-size: 2.4rem;
    font-weight: 700;
}
.main-sub {
    text-align: center;
    font-size: 1rem;
    color: #9ca3af;
    max-width: 640px;
    margin: 0 auto 2rem auto;
    line-height: 1.6;
}

/* CHAT */
.stChatMessage {
    max-width: 720px;
    margin: 0 auto;
}
[data-testid="stChatMessageContent"] {
    background-color: #1e2130 !important;
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 0.95rem;
    line-height: 1.65;
}

/* INPUT */
div[data-testid="stChatInput"] {
    max-width: 720px;
    margin: 0 auto;
}
.stChatInputContainer {
    background-color: #1a1d27 !important;
    border: 1px solid #3a3d4a !important;
    border-radius: 14px !important;
    padding: 6px !important;
}
textarea[data-testid="stChatInputTextArea"] {
    color: #ffffff !important;
}

/* CLEAN UI */
header, footer { visibility: hidden; }

</style>
""", unsafe_allow_html=True)

# ── Session state ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0
if "cache" not in st.session_state:
    st.session_state.cache = {}

# ── Sidebar ──
with st.sidebar:
    st.markdown("### API Usage")
    st.markdown("<p style='font-size: 0.8rem; color: #9ca3af; margin-bottom: 0;'>API Calls</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 2.5rem; margin-top: -10px; margin-bottom: 20px;'>{st.session_state.api_calls}</p>", unsafe_allow_html=True)

    st.checkbox("Use cached responses when available", key="use_cached_response")

    st.divider()

    st.markdown("#### How to Use")
    st.markdown("""
1. **Tell us about your trip** - Include destination, duration, and preferences
2. **Ask for specific recommendations** - Food, attractions, hidden gems
3. **Refine your itinerary** - Ask to modify or get more details
4. **Export your plan** - Download, email, or add to calendar
    """)

    st.markdown("#### Example Prompts")
    st.markdown("""
<p style="font-size: 0.9rem;">
&bull; I'm going to Tokyo for 5 days and love food and technology<br><br>
&bull; Planning a 3-day hiking trip to the Grand Canyon<br><br>
&bull; Weekend getaway to New York with kids<br><br>
&bull; Add more food options to my itinerary
</p>
    """, unsafe_allow_html=True)

    if len(st.session_state.messages) > 0:
        itinerary_content = ""
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "Planner"
            itinerary_content += f"{role}: {msg['content']}\\n\\n"
        
        st.divider()
        st.download_button(
            label="💾 Download Plan",
            data=itinerary_content,
            file_name="travel_itinerary.txt",
            mime="text/plain",
            use_container_width=True
        )

# ── Header ──
st.markdown('<div class="main-heading">✈️ Travel Itinerary Planner</div>', unsafe_allow_html=True)
st.markdown("<div class=\\"main-sub\\">Plan your perfect trip with our AI-powered chatbot! Tell me about your trip, and I'll create a personalized itinerary.</div>", unsafe_allow_html=True)

# ── Chat history ──
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── System prompt ──
SYSTEM_PROMPT = "You are an expert travel planner AI."

# ── Chat input ──
if prompt := st.chat_input("Tell me about your trip!"):

    if not GROQ_API_KEY:
        st.error("Missing GROQ API key")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    cache_key = prompt.lower().strip()

    # ── Cached response ──
    use_cached = st.session_state.get("use_cached_response", False)
    if use_cached and cache_key in st.session_state.cache:
        response_text = st.session_state.cache[cache_key]

        with st.chat_message("assistant"):
            st.markdown(response_text)
            st.caption("⚡ Cached")

    # ── REAL STREAMING ──
    else:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_text = ""

            client = Groq(api_key=GROQ_API_KEY)

            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *st.session_state.messages
                ],
                temperature=0.7,
                max_tokens=1500,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_text += chunk.choices[0].delta.content
                    placeholder.markdown(full_text + "▌")

            placeholder.markdown(full_text)

            response_text = full_text
            st.session_state.api_calls += 1
            st.session_state.cache[cache_key] = response_text

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()