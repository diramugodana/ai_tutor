import streamlit as st
from src.ai_engine import summarize_chapter, answer_revision_questions, answer_general_question
import sys
import os
sys.path.append(os.path.abspath("."))

# ------------------------
# App State
# ------------------------
if "show_app" not in st.session_state:
    st.session_state.show_app = False
if "history" not in st.session_state:
    st.session_state.history = []

BIO_CHAPTERS = ["1", "2", "3", "4", "5"]
GEO_CHAPTERS = ["1", "2", "3"]
CHAPTER_LABELS = {
    "1": "Chapter 1: Introduction",
    "2": "Chapter 2",
    "3": "Chapter 3",
    "4": "Chapter 4",
    "5": "Chapter 5"
}

# ------------------------
# Styling & Animations
# ------------------------
# JS injection to apply pastel background
st.markdown("""
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        const style = document.createElement('style');
        style.innerHTML = `
            body {
                background: linear-gradient(to right, #fff5fa, #fbc2eb);
                font-family: 'Open Sans', sans-serif;
            }
        `;
        document.head.appendChild(style);
    });
    </script>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    .navbar {
        background: linear-gradient(90deg, #fbc2eb, #a6c1ee);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-family: Georgia, serif;
        font-size: 28px;
        font-weight: bold;
        color: #4a1942;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        font-size: 14px;
        color: #666;
        border-top: 1px solid #ddd;
    }
    .pastel-box {
        padding: 1.5rem;
        border-radius: 18px;
        margin-bottom: 2rem;
        color: #333;
        box-shadow: 0px 4px 16px rgba(0,0,0,0.05);
        backdrop-filter: blur(4px);
        transition: transform 0.3s ease;
    }
    .pastel-box:hover {
        transform: scale(1.01);
    }
    .pastel-purple {
        background-color: #f0e6f7;
    }
    .pastel-pink {
        background-color: #ffe3ec;
    }
    .question-title {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 0.75rem;
        font-family: Georgia, serif;
    }
    .dual-column {
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
    }
    .column {
        flex: 1;
        min-width: 250px;
    }
    .custom-button button {
        background-color: #fcd5ce;
        color: #4a1942;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: bold;
        transition: 0.3s ease;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    }
    .custom-button button:hover {
        background-color: #ffe3ec;
        transform: scale(1.03);
    }
    .loader {
        display: inline-block;
        width: 80px;
        height: 24px;
        position: relative;
    }
    .loader div {
        position: absolute;
        width: 16px;
        height: 16px;
        background: #a6c1ee;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    .loader div:nth-child(1) {
        left: 8px;
        animation-delay: -0.32s;
    }
    .loader div:nth-child(2) {
        left: 32px;
        animation-delay: -0.16s;
    }
    .loader div:nth-child(3) {
        left: 56px;
    }
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1.0); }
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Landing Page
# ------------------------
if not st.session_state.show_app:
    st.markdown("<div class='navbar'>🌸 Swahili-English Curriculum Tutor 🌸</div>", unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align: center; font-size: 18px; margin-top: 1rem;'>
            Your pastel-powered, bilingual AI study buddy — focused on Form 1 Biology & Geography.
        </div>
        <hr style='margin: 2rem 0;'>
        
        **✨ What this tool helps you do:**
        - 📚 Summarize textbook chapters
        - ❓ Answer curriculum revision questions
        - 🤔 Handle your custom questions in English or Kiswahili

        ### 🧠 How to Use:
        1. Select subject
        2. Pick a mode
        3. Choose a chapter or type your question
        4. Compare the English & Swahili answers side-by-side
    """)

    if st.button("🌈 Start Learning", key="start_btn"):
        with st.spinner("Launching your tutor..."):
            st.session_state.show_app = True

    st.markdown("<div class='footer'>Built with 💜 for Kenyan learners | © 2025 Your Name</div>", unsafe_allow_html=True)

# ------------------------
# Main Tutor Interface
# ------------------------
else:
    st.markdown("<div class='navbar'>📘 Study Assistant</div>", unsafe_allow_html=True)

    subject = st.selectbox("Select Subject", ["Form 1 Biology", "Form 1 Geography"])
    mode = st.radio("Choose Learning Mode", ["Summarize Chapter", "Answer Revision Questions", "Ask a General Question"])

    chapters = BIO_CHAPTERS if subject == "Form 1 Biology" else GEO_CHAPTERS
    user_input = ""
    chapter = ""

    if mode in ["Summarize Chapter", "Answer Revision Questions"]:
        chapter = st.selectbox("Choose Chapter", chapters, format_func=lambda x: CHAPTER_LABELS.get(x, f"Chapter {x}"))
        user_input = f"{'summarize' if mode == 'Summarize Chapter' else 'answer revision questions for'} chapter {chapter}"
    else:
        user_input = st.text_input("Type your question below 👇", placeholder="e.g., What is osmosis?")

    if st.button("🚀 Submit", key="submit_btn"):
        st.markdown("""
            <div class="loader">
                <div></div><div></div><div></div>
            </div>
        """, unsafe_allow_html=True)
        
        if mode == "Summarize Chapter":
            response = summarize_chapter(chapter)
        elif mode == "Answer Revision Questions":
            response = answer_revision_questions(chapter)
        else:
            response = answer_general_question(user_input)

        st.session_state.history.append({"query": user_input, "response": response.strip()})

    for i, item in enumerate(reversed(st.session_state.history)):
        bg_class = "pastel-purple" if i % 2 == 0 else "pastel-pink"

        if "Summary in Swahili:" in item["response"]:
            english_part = item["response"].split("Summary in Swahili:")[0].strip()
            swahili_part = item["response"].split("Summary in Swahili:")[1].strip()
        else:
            english_part = item["response"]
            swahili_part = "(Swahili version not available)"

        st.markdown(f"""
        <div class='pastel-box {bg_class}'>
            <div class='question-title'>Question:</div>
            <div style='margin-bottom: 1rem;'>{item['query']}</div>
            <div class='dual-column'>
                <div class='column'>
                    <strong>🇬🇧 English</strong>
                    <div style='margin-top: 0.5rem;'>{english_part}</div>
                </div>
                <div class='column'>
                    <strong>🇰🇪 Kiswahili</strong>
                    <div style='margin-top: 0.5rem;'>{swahili_part}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='footer'>Built with 💜 for Kenyan learners | © 2025 Your Name</div>", unsafe_allow_html=True)
