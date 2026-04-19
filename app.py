import streamlit as st
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import io
import re

# --- PAGE CONFIGURATION ---
st.page_config(page_title="LogiSmart Pro | Rohit Pal", layout="wide", page_icon="🚛")

# Sidebar - Navigations
st.sidebar.title("🚛 LogiSmart v7.0")
st.sidebar.markdown("### Developer: **Rohit Pal**")

option = st.sidebar.selectbox(
    "Select Operational Tool",
    ("Delivery-Contact Matcher", "Fast PDF Merger", "MIS Data Extractor")
)

# --- 1. DELIVERY-CONTACT MATCHER (Ceragem) ---
if option == "Delivery-Contact Matcher":
    st.title("📊 Ceragem Delivery-Contact Matcher")
    st.info("Logic: Matching Delivery No (PDF) with Contact No (GI Report).")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_pdfs = st.file_uploader("1. Upload Invoices (PDF)", type="pdf", accept_multiple_files=True, key="del_pdf")
    with col2:
        gi_file = st.file_uploader("2. Upload GI Report (Excel/CSV)", type=["xlsx", "csv"], key="del_gi")

    if st.button("Run Reconciliation"):
        if uploaded_pdfs and gi_file:
            try:
                all_inv_data = []
                for pdf_file in uploaded_pdfs:
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                delivery_match = re.search(r"Delivery\s*no\s*[:.]?\s*(\d+)", text, re.IGNORECASE)
                                inv_no = re.search(r"(?:Serial No\. Of Challan|RAL-)\s*[:.]?\s*([\w-]+)", text)
                                order_no = re.search(r"S\.Order No\s*(\d+)", text)
                                
                                if delivery_match:
                                    all_inv_data.append({
                                        "Delivery No": delivery_match.group(1).strip(),
                                        "Invoice No.": inv_no.group(1) if inv_no else pdf_file.name,
                                        "S. Order No.": order_no.group(1) if order_no else ""
                                    })
                
                df_pdf = pd.DataFrame(all_inv_data).drop_duplicates(subset=["Delivery No"])

                # Reading GI Report
                if gi_file.name.endswith('.csv'):
                    df_gi = pd.read_csv(gi_file)
                else:
                    df_gi = pd.read_excel(gi_file, engine='openpyxl')
                
                df_gi.columns = df_gi.columns.str.strip()
                
                # Matching Column
                gi_match_col = next((c for c in ['CONTACT', 'Contact No', 'Mobile'] if c in df_gi.columns), None)
                
                if gi_match_col:
                    df_gi[gi_match_col] = df_gi[gi_match_col].astype(str).str.extract('(\d+)')
                    df_pdf['Delivery No'] = df_pdf['Delivery No'].astype(str)

                    final_df = pd.merge(df_pdf, df_gi, left_on='Delivery No', right_on=gi_match_col, how='left')
                    st.success("Matching Completed!")
                    st.dataframe(final_df)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        final_df.to_excel(writer, index=False)
                    st.download_button("📥 Download Result", data=output.getvalue(), file_name="Ceragem_Match.xlsx")
                else:
                    st.error("GI Report mein Contact/Mobile column nahi mila.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 2. FAST PDF MERGER ---
elif option == "Fast PDF Merger":
    st.title("🔗 Fast PDF Merger")
    st.write("Sare PDFs ek saath select karke merge karein.")
    merge_files = st.file_uploader("Upload PDFs to Merge", type="pdf", accept_multiple_files=True, key="merger")
    
    if st.button("Merge Now"):
        if merge_files:
            merged_pdf = fitz.open()
            for f in merge_files:
                with fitz.open(stream=f.read(), filetype="pdf") as temp_pdf:
                    merged_pdf.insert_pdf(temp_pdf)
            
            out_bio = io.BytesIO()
            merged_pdf.save(out_bio)
            st.success("Merged Successfully!")
            st.download_button("📥 Download Merged PDF", data=out_bio.getvalue(), file_name="Combined_Invoices.pdf")

# --- 3. MIS DATA EXTRACTOR ---
elif option == "MIS Data Extractor":
    st.title("📄 PDF to MIS Extractor")
    st.write("Invoice PDFs se data nikal kar Excel banayein.")
    mis_files = st.file_uploader("Upload Invoices", type="pdf", accept_multiple_files=True, key="mis_ext")
    
    if st.button("Extract Data"):
        if mis_files:
            # Basic extraction logic
            data = []
            for f in mis_files:
                with pdfplumber.open(f) as pdf:
                    text = pdf.pages[0].extract_text()
                    inv = re.search(r"RAL-[\d]+", text)
                    data.append({"File": f.name, "Invoice": inv.group(0) if inv else "N/A"})
            st.table(data)

st.sidebar.markdown("---")
st.sidebar.info("Tip: Agar Error aaye toh 'requirements.txt' mein 'openpyxl' check karein.")
