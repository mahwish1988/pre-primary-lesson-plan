import streamlit as st 
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime

# -------------------------------
# 🔐 Load API Key from .env
# -------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ API key not found. Please check your .env file.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------------
# 🧹 Clean and preprocess text
# -------------------------------
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

# -------------------------------
# 📄 Extract text from PDF
# -------------------------------
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    except Exception as e:
        return f"Error reading PDF: {e}"
    return clean_text(text)

# -------------------------------
# 🤖 Gemini Prompt Logic
# -------------------------------
def generate_answers(content, query):
    prompt = f"""
You are a helpful assistant trained to answer ONLY from the following preprimary phonics syllabus content:

\"\"\" 
{content} 
\"\"\"

If the user's question is NOT clearly related to the content (like general education tips, other subjects, or off-topic questions), gently reply:

👋 I'm here to help only with what's inside the lesson plan PDF. Could you please ask something related to the phonics or topics listed there?

Now, using the above syllabus content, answer the question clearly and concisely:
**{query}**
"""
    try:
        response = model.generate_content(prompt)
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                parts = getattr(candidate.content, 'parts', [])
                return parts[0].text if parts else candidate.content.text
        return "No answer generated."
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# 💾 Feedback: Radio + Open Text
# -------------------------------
def save_feedback(rating, suggestion):
    feedback_file = "feedback.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_data = {
        "Timestamp": [now],
        "Helpful": [rating],
        "Suggestion": [suggestion]
    }
    df_new = pd.DataFrame(feedback_data)
    if os.path.exists(feedback_file):
        df_existing = pd.read_excel(feedback_file)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new
    df_combined.to_excel(feedback_file, index=False)

def save_open_feedback(feedback):
    feedback_file = "open_feedback.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_data = {
        "Timestamp": [now],
        "Feedback": [feedback]
    }
    df_new = pd.DataFrame(feedback_data)
    if os.path.exists(feedback_file):
        df_existing = pd.read_excel(feedback_file)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new
    df_combined.to_excel(feedback_file, index=False)

# -------------------------------
# 🖼️ Streamlit UI
# -------------------------------
st.set_page_config(page_title="Preprimary Syllabus Assistant")

# Sidebar Info
with st.sidebar:
    st.header("📬 Get in Touch")
    st.markdown("""
**Mahwish Kiran**  
📧 [mahwishpy@gmail.com](mailto:mahwishpy@gmail.com)  
🔗 [Facebook](https://www.facebook.com/share/1BBXjgbXPS/)  
🔗 [LinkedIn](https://www.linkedin.com/in/mahwish-kiran-842945353)  

_Made with ❤️ for every child's first step._
""")

# App Title & Intro
st.title("🎒 Preprimary Syllabus Assistant")
st.markdown("Hi there! 👋 I'm here to help you explore the lesson plan. Ask me anything about phonics, monthly topics, or classroom activities listed in the plan below ⬇️")

# -------------------------------
# 📁 Load PDF
# -------------------------------
PDF_FILE_PATH = "yearly year lesson plan by mahwish.pdf"

if 'pdf_content' not in st.session_state:
    st.session_state['pdf_content'] = extract_text_from_pdf(PDF_FILE_PATH)

if st.session_state['pdf_content'].startswith("Error"):
    st.error(st.session_state['pdf_content'])
else:
    # -------------------------------
    # 💬 User Query
    # -------------------------------
    user_query = st.text_input("💬 What would you like to know?")
    if 'helpful_feedback' not in st.session_state:
        st.session_state['helpful_feedback'] = None

    if st.button("🔍 Get Answer"):
        if user_query.strip() == "":
            st.warning("Oops! Please type your question before clicking.")
        else:
            answer = generate_answers(st.session_state['pdf_content'], user_query)
            st.subheader("📘 Here's what I found:")
            st.markdown(answer)

            # Feedback Radio
            st.markdown("### ✨ We'd love to know if this helped!")
            helpful = st.radio("Please choose an option:", 
                               ("👍 Yes, it was super helpful!", "👎 Hmm, not really."), 
                               index=0, key="helpful_feedback")

            if st.button("Submit Feedback on Answer"):
                save_feedback(helpful, user_query)
                st.success("Thanks for your feedback! 💖")

# -------------------------------
# 📝 Open Form Feedback
# -------------------------------
st.subheader("✍️ Help Us Make It Even More Fun! 🎨")
feedback = st.text_area("🐞 Found something buggy or tricky? Let us know! 👨‍👩‍👧‍👦", height=150)

if st.button("🚀 Share and Help Us Grow!"):
    if feedback.strip():
        save_open_feedback(feedback)
        st.success("Feedback submitted. Thank you! 🙌")
    else:
        st.warning("⚠️ Please enter feedback before submitting.")




