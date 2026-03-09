import streamlit as st
import pdfplumber
from pptx import Presentation
import docx
from openai import OpenAI
import textwrap

# ==================================
# CONFIG
# ==================================

st.set_page_config(page_title="AI Study Engine", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

MAX_CHUNK_SIZE = 2000

# ==================================
# FILE TEXT EXTRACTION
# ==================================

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
        for p in doc.paragraphs:
            text += p.text + "\n"

    elif file.name.endswith(".txt"):
        text = file.read().decode()

    return text


# ==================================
# TEXT CHUNKING
# ==================================

def chunk_text(text, size=MAX_CHUNK_SIZE):

    chunks = textwrap.wrap(
        text,
        width=size,
        break_long_words=False,
        replace_whitespace=False
    )

    return chunks


# ==================================
# OPENAI PROCESSING
# ==================================

def ai_process(chunk, mode):

    if mode == "Quick":

        instruction = """
Create:

1. Short Summary
2. Bullet Cheat Sheet
3. Key Takeaways
"""

    elif mode == "Study Mode":

        instruction = """
Create structured study material:

1. Summary
2. Cheat Sheet
3. Study Notes
4. Memory Tricks
5. Key Takeaways
6. 5 Practice Questions
"""

    else:

        instruction = """
Create detailed structured notes including:

1. Executive Summary
2. Detailed Notes
3. Cheat Sheet
4. Key Concepts
5. Key Takeaways
6. 10 Practice Questions
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
            {
                "role": "system",
                "content": "You are an expert teacher that converts study material into clear learning notes."
            },
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# ==================================
# CACHE (SAVE API COST)
# ==================================

@st.cache_data(show_spinner=False)
def process_document(text, mode):

    chunks = chunk_text(text)

    results = []

    for c in chunks:
        result = ai_process(c, mode)
        results.append(result)

    return "\n\n".join(results)


# ==================================
# STREAMLIT UI
# ==================================

st.title("🧠 AI Study Engine")

st.markdown("""
Upload **PDF / PPT / DOCX / TXT**

AI will convert it into:

• Summary  
• Cheat Sheet  
• Study Notes  
• Memory Tricks  
• Practice Questions  
""")

uploaded_file = st.file_uploader(
    "Upload Study Material",
    type=["pdf","pptx","docx","txt"]
)

mode = st.radio(
    "Select Mode",
    [
        "Quick",
        "Study Mode",
        "Deep Learning Mode"
    ]
)

if uploaded_file:

    st.success("File Uploaded")

    if st.button("Generate Study Material"):

        with st.spinner("Extracting text..."):
            text = extract_text(uploaded_file)

        if len(text) < 100:
            st.error("File contains very little readable text.")
            st.stop()

        st.info(f"Text size: {len(text)} characters")

        with st.spinner("AI is building your study material..."):

            result = process_document(text, mode)

        st.success("Done!")

        tab1, tab2, tab3 = st.tabs(
            ["📖 Read", "⬇ Download", "🖨 Print"]
        )

        with tab1:
            st.markdown(result)

        with tab2:

            st.download_button(
                "Download TXT",
                result,
                file_name="study_notes.txt"
            )

            st.download_button(
                "Download Markdown",
                result,
                file_name="study_notes.md"
            )

        with tab3:

            st.code(result)

            st.caption(
                "Use browser print → Save as PDF"
            )

# ==================================
# SIDEBAR
# ==================================

st.sidebar.header("AI Study Engine")

st.sidebar.write("""
Turn any document into:

• Smart Notes  
• Cheat Sheets  
• Exam Prep  
• Practice Questions  
""")

st.sidebar.markdown("---")

st.sidebar.write("Model: gpt-4o-mini")

st.sidebar.write("Cost optimized for personal use")
