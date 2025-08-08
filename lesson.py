import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime
import openpyxl  # Required for Excel writing

# -------------------------------
# 🔐 Load Gemini API Key
# -------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Gemini API key not found in .env file.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------------
# 🧼 Clean text
# -------------------------------
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

# -------------------------------
# 📄 Extract PDF content
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
# 🤖 Gemini Answer Generation
# -------------------------------
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
        if response.text:
            return response.text
        return "No answer generated."
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# 💾 Save Feedback (Radio + Text)
# -------------------------------
def save_feedback(rating, suggestion):
    feedback_file = "feedback.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_data = {"Timestamp": [now], "Helpful": [rating], "Suggestion": [suggestion]}
    df_new = pd.DataFrame(feedback_data)

    try:
        if os.path.exists(feedback_file):
            df_existing = pd.read_excel(feedback_file)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_excel(feedback_file, index=False)
        st.success(f"✅ Feedback saved successfully!")
    except PermissionError:
        st.error("❌ Please close the feedback file before saving.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

def save_open_feedback(feedback):
    feedback_file = "feedback_data.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[now, feedback]], columns=["Timestamp", "Feedback"])

    try:
        if os.path.exists(feedback_file):
            old_df = pd.read_excel(feedback_file)
            df = pd.concat([old_df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_excel(feedback_file, index=False)
        st.success("✅ Thank you for your feedback!")
    except PermissionError:
        st.error("❌ Please close the feedback file before saving.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

# -------------------------------
# 🎯 Streamlit UI
# -------------------------------
st.set_page_config(page_title="Preprimary Syllabus Assistant")

# Sidebar contact info
with st.sidebar:
    st.header("📬 Get in Touch")
    st.markdown("""
**Mahwish Kiran**  
📧 [mahwishpy@gmail.com](mailto:mahwishpy@gmail.com)  
🔗 [Facebook](https://www.facebook.com/share/1BBXjgbXPS/)  
🔗 [LinkedIn](https://www.linkedin.com/in/mahwish-kiran-842945353)  

_Made with ❤️ for every child's first step._
""")

# Title and intro
st.title("🎒 Preprimary Syllabus Assistant")
st.markdown("Hi there! 👋 Ask me anything about the lesson plan below — I’ll reply with clear, point-based answers.")

# -------------------------------
# 📁 Load PDF
# -------------------------------
PDF_FILE_PATH = "yearly year lesson plan by mahwish.pdf"

if 'pdf_content' not in st.session_state:
    st.session_state['pdf_content'] = extract_text_from_pdf(PDF_FILE_PATH)

if st.session_state['pdf_content'].startswith("Error"):
    st.error(st.session_state['pdf_content'])

# -------------------------------
# 💬 User Query
# -------------------------------
user_query = st.text_input("💬 What would you like to know?")

if 'helpful_feedback' not in st.session_state:
    st.session_state['helpful_feedback'] = None

# -------------------------------
# 📘 Answer Section
# -------------------------------
if st.button("🔍 Get Answer") and st.session_state['pdf_content']:
    if user_query.strip() == "":
        st.warning("❗ Please enter a question.")
    else:
        answer = generate_answers(st.session_state['pdf_content'], user_query)
        st.subheader("📘 Here's what I found:")
        st.markdown(answer)

        # Feedback radio
        st.markdown("### ✨ Was this helpful?")
        helpful = st.radio("Select an option:", 
                           ("👍 Yes, it was super helpful!", "👎 Hmm, not really."), 
                           key="helpful_feedback")

        if st.button("✅ Submit Feedback"):
            save_feedback(helpful, user_query)

# -------------------------------
# 📝 Open Text Feedback
# -------------------------------
st.subheader("✍️ Help Us Make It Even More Fun!")
feedback = st.text_area("🐞 Found something buggy or tricky? Let us know!", height=150)

if st.button("🚀 Share Feedback"):
    if feedback.strip():
        save_open_feedback(feedback)
    else:
        st.warning("⚠️ Please write some feedback before submitting.")







