# -*- coding: utf-8 -*-
import os
import unicodedata
import streamlit as st
from mistralai import Mistral

st.set_page_config(page_title="Financial Advisor Bot", page_icon="💰")

# ---- Helpers ----
def normalize_text(s: str) -> str:
    """Normalize text to handle smart quotes and unicode issues"""
    if not isinstance(s, str):
        return s
    # Replace smart quotes and normalize to NFC
    s = (s.replace("\u2019", "'")
           .replace("\u2018", "'")
           .replace("\u201C", '"')
           .replace("\u201D", '"'))
    return unicodedata.normalize("NFC", s)

# ---- API key ----
api_key = os.getenv("MISTRAL_API_KEY") or st.sidebar.text_input(
    "MISTRAL_API_KEY", 
    type="password",
    help="Enter your Mistral API key. Best practice: add this in Streamlit → Settings → Secrets."
)

if not api_key:
    st.info("🔑 Please add your MISTRAL_API_KEY in Secrets or enter it in the sidebar.")
    st.stop()

# Initialize Mistral client
client = Mistral(api_key=api_key)
MODEL = "mistral-large-latest"
SYSTEM_PROMPT = """You are a helpful financial advisor assistant.
Provide advice on budgeting, investing, savings, and personal finance.
Keep answers clear and practical. Always mention this is educational, not professional financial advice."""

# ---- Initialize Session State ----
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# ---- UI ----
st.title("💰 Financial Advisor Bot")
st.markdown("*Ask me anything about budgeting, investing, savings, and personal finance!*")

# ---- Display chat history ----
for m in st.session_state.messages:
    if m["role"] == "system":  # Don't display system prompt
        continue
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(normalize_text(m["content"]))

# ---- Chat Input ----
user_msg = st.chat_input("Type your financial question here...")
if user_msg:
    user_msg = normalize_text(user_msg)
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # ---- Call Mistral API ----
    try:
        with st.spinner("Thinking..."):
            resp = client.chat.complete(
                model=MODEL,
                messages=[
                    {"role": m["role"], "content": normalize_text(m["content"])}
                    for m in st.session_state.messages
                ],
                temperature=0.7,
                max_tokens=500,
            )
            bot_reply = normalize_text(resp.choices[0].message.content)
    except Exception as e:
        bot_reply = f"⚠️ Error: {normalize_text(str(e))}"

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

# ---- Sidebar ----
with st.sidebar:
    st.header("Settings")
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    st.markdown("""
    ### About
    This is a financial advisor chatbot powered by Mistral AI.
    
    **Disclaimer:** This bot provides educational information only. 
    Always consult with a qualified financial professional for 
    personalized advice.
    """)
    
    st.divider()
    
    # Display message count
    msg_count = len([m for m in st.session_state.messages if m["role"] != "system"])
    st.caption(f"Messages in conversation: {msg_count}")
