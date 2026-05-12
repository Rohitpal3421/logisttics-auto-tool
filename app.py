import streamlit as st
import pdfplumber
import os

st.set_page_config(page_title="Logistics PDF Auto-Tool", layout="wide")

st.title("📄 PDF Data Extraction Tool")
st.subheader("PDF upload karein aur zaroori data select karein")

# Sidebar for PDF Operations
option = st.sidebar.selectbox("Kya karna chahte hain?", ["Data Extract Karna", "PDF Merge (Coming Soon)"])

uploaded_file = st.file_uploader("Apni PDF file yahan drop karein", type="pdf")

if uploaded_file is not None:
    # PDF ko read karna
    with pdfplumber.open(uploaded_file) as pdf:
        all_text_lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text_lines.extend(text.split('\n'))

    if all_text_lines:
        st.write("### PDF se nikala gaya data:")
        st.info("Niche se wo lines select karein jo aapko chahiye.")
        
        # Checkboxes for each line
        selected_data = []
        
        # 'Select All' button ka option
        if st.checkbox("Sabhi lines select karein"):
            selected_data = all_text_lines
        else:
            for i, line in enumerate(all_text_lines):
                if st.checkbox(line, key=f"line_{i}"):
                    selected_data.append(line)

        # Final Extraction Result
        if st.button("Final Data Copy Karein"):
            if selected_data:
                st.success("Aapka selected data niche hai:")
                final_text = "\n".join(selected_data)
                st.text_area("Selected Text:", value=final_text, height=300)
                st.download_button("File Download Karein", final_text, file_name="extracted_data.txt")
            else:
                st.warning("Pahle kuch lines select karein!")
    else:
        st.error("Is PDF mein koi text nahi mila. Kya ye scanned image hai?")
