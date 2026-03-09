import streamlit as st
import pdfplumber
from pptx import Presentation
import docx
from openai import OpenAI
import textwrap
import hashlib

# ==========================
# CONFIG
# ==========================

st.set_page_config(page_title="AI Notes Generator", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

MAX_CHUNK_SIZE = 2000

# ==========================
# FILE TEXT EXTRACTION
# ==========================

def extract_text(file):

    text = ""

    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    elif file.name.endswith(".pptx"):
        prs = Presentation(file)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"

    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif file.name.endswith(".txt"):
        text = file.read().decode()

    return text


# ==========================
# TEXT CHUNKING
# ==========================

def chunk_text(text, size=MAX_CHUNK_SIZE):

    chunks = textwrap.wrap(
        text,
        width=size,
        break_long_words=False,
        replace_whitespace=False
    )

    return chunks


# ==========================
# OPENAI CALL
# ==========================

def summarize_chunk(chunk, mode):

    if mode == "Quick":
        instruction = "Create a concise summary and cheat sheet."
    else:
        instruction = """
        Convert the content into:

        1. Summary
        2. Cheat Sheet
        3. Study Notes
        4. Key Takeaways
        """

    prompt = f"""
    {instruction}

    Content:
    {chunk}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": "You are an expert study assistant that creates concise study material."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# ==========================
# CACHE TO SAVE API COST
# ==========================

@st.cache_data(show_spinner=False)
def process_document(text, mode):

    chunks = chunk_text(text)

    results = []

    for chunk in chunks:
        summary = summarize_chunk(chunk, mode)
        results.append(summary)

    return "\n\n".join(results)


# ==========================
# STREAMLIT UI
# ==========================

st.title("📚 AI Notes + Cheat Sheet Generator")

st.markdown(
"""
Upload **PDF / PPTX / DOCX / TXT** and convert them into:

• Summary  
• Cheat Sheet  
• Study Notes  
• Key Takeaways  
"""
)

uploaded_file = st.file_uploader(
    "Upload your document",
    type=["pdf", "pptx", "docx", "txt"]
)

mode = st.radio(
    "Processing Mode",
    ["Quick (Cheaper)", "Detailed"]
)

if uploaded_file:

    st.success("File uploaded successfully")

    if st.button("Generate Notes"):

        with st.spinner("Extracting text..."):

            text = extract_text(uploaded_file)

        if len(text) < 100:
            st.error("Not enough readable text in file.")
            st.stop()

        st.info(f"Document length: {len(text)} characters")

        with st.spinner("Generating AI Notes..."):

            result = process_document(text, mode)

        st.success("Notes Generated!")

        tab1, tab2 = st.tabs(["📖 Read", "⬇ Download"])

        with tab1:
            st.markdown(result)

        with tab2:

            st.download_button(
                label="Download Notes",
                data=result,
                file_name="ai_notes.txt"
            )

            st.download_button(
                label="Download Markdown",
                data=result,
                file_name="ai_notes.md"
            )

        st.markdown("---")

        st.markdown("### 🖨 Print")

        st.code(result)

        st.caption("Use browser print → Save as PDF")


# ==========================
# SIDEBAR
# ==========================

st.sidebar.header("About")

st.sidebar.write(
"""
This tool converts study material into:

• AI Summaries  
• Cheat Sheets  
• Quick Notes  

Optimized to minimize OpenAI API costs.
"""
)

st.sidebar.markdown("---")

st.sidebar.write("Model: gpt-4o-mini")
