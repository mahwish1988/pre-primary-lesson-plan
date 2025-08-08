import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime
import openpyxl  # Required for Excel writing

# Load environment variables and API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Clean and preprocess text
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    except Exception as e:
        return f"Error reading PDF: {e}"
    return clean_text(text)

# Gemini Q&A generation
def generate_answers(content, query):
    prompt = f"""
You are a helpful assistant trained to answer ONLY from the following preprimary phonics syllabus content:

\"\"\" 
{content} 
\"\"\"


Your job is to:
- ONLY use the information provided in the syllabus
- Format answers using **bullet points** or **numbered lists**
- Use short, clear sections like:

**📌 Topic:**  
[Summary of relevant topic]

**📚 Key Information:**  
• Point 1  
• Point 2  
• Point 3  

**🎯 Suggested Activities or Notes:**  
• Tip or activity  
• Game or method  

If the question is not related to the syllabus, gently reply:

👋 I'm here to help only with what's inside the lesson plan PDF. Could you please ask something related to the phonics or topics listed there?

Now, answer the user's question:
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

# Save feedback from radio buttons (helpful or not)
def save_feedback(rating, suggestion):
    feedback_file = "feedback.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_data = {
        "Timestamp": [now],
        "Helpful": [rating],
        "Suggestion": [suggestion]
    }
    df_new = pd.DataFrame(feedback_data)
    try:
        if os.path.exists(feedback_file):
            df_existing = pd.read_excel(feedback_file)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_excel(feedback_file, index=False)
        st.success(f"✅ Feedback saved successfully!\n📁 Saved at: `{os.path.abspath(feedback_file)}`")
    except PermissionError:
        st.error("❌ Permission denied: Please close the feedback Excel file if it is open.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

# Save open-form textual feedback
def save_open_feedback(feedback):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[now, feedback]], columns=["Timestamp", "Feedback"])
    feedback_file = "feedback_data.xlsx"
    try:
        if os.path.exists(feedback_file):
            old_df = pd.read_excel(feedback_file)
            df = pd.concat([old_df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_excel(feedback_file, index=False)
        st.success("✅ Feedback saved successfully! Thank you for your input.")
    except PermissionError:
        st.error("❌ Permission denied: Please close the feedback Excel file if it is open.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

# Set up Streamlit
st.set_page_config(page_title="Preprimary Syllabus Assistant")

# Sidebar Contact Info
with st.sidebar:
    st.header("📬 Get in Touch")
    st.markdown("""
**Mahwish Kiran**  
📧 [mahwishpy@gmail.com](mailto:mahwishpy@gmail.com)  
🔗 [Facebook](https://www.facebook.com/share/1BBXjgbXPS/)  
🔗 [LinkedIn](https://www.linkedin.com/in/mahwish-kiran-842945353)  

_Made with ❤️ for every child's first step._
    """)

# Main Title & Intro
st.title("🎒 Preprimary Syllabus Assistant")
st.markdown("Hi there! 👋 I'm here to help you explore the lesson plan. Ask me anything about phonics, monthly topics, or classroom activities listed in the plan below ⬇️")

# Load PDF content
PDF_FILE_PATH = r"yearly year lesson plan by mahwish.pdf.pdf"

if 'pdf_content' not in st.session_state:
    st.session_state['pdf_content'] = extract_text_from_pdf(PDF_FILE_PATH)

if st.session_state['pdf_content'].startswith("Error"):
    st.error(st.session_state['pdf_content'])

# User query
user_query = st.text_input("💬 What would you like to know?")

# Store feedback radio choice in session state to avoid re-selection after rerun
if 'helpful_feedback' not in st.session_state:
    st.session_state['helpful_feedback'] = None

# Q&A Answer Section
if st.button("🔍 Get Answer") and st.session_state['pdf_content']:
    if user_query.strip() == "":
        st.warning("Oops! Please type your question before clicking.")
    else:
        answer = generate_answers(st.session_state['pdf_content'], user_query)
        st.subheader("📘 Here's what I found:")
        st.markdown(answer)

        # Feedback radio
        st.markdown("### ✨ We'd love to know if this helped!")
        helpful = st.radio("Please choose an option:", ("👍 Yes, it was super helpful!", "👎 Hmm, not really."), index=0, key="helpful_feedback")

        # Save feedback button for radio feedback
        if st.button("Submit Feedback on Answer"):
            save_feedback(helpful, user_query)

# ------------------------------------
# 📝 Additional Feedback Section (open-form)
# ------------------------------------

st.subheader("✍️ Help Us Make It Even More Fun!🎨")

feedback = st.text_area("🐞 Found something buggy or tricky? Let us know!👨‍👩‍👧‍👦", height=150)

if st.button("🚀 Share and Help Us Grow!"):
    if feedback.strip():
        save_open_feedback(feedback)
    else:
        st.warning("⚠️ Please enter feedback before submitting.")
