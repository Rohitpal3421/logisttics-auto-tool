import streamlit as st
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
import io
import re
import zipfile

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="LogiSmart Pro | Rohit Pal", layout="wide", page_icon="🚛")

st.sidebar.title("🚛 LogiSmart v6.5")
st.sidebar.markdown("### Developer: **Rohit Pal**")

# Sidebar navigation - Saare options wapas lane ke liye
option = st.sidebar.radio(
    "Select Operational Tool",
    ("Delivery-Contact Matcher", "Dual-Set Invoice Matcher", "Fast PDF Merger", "MIS Data Extractor")
)

# --- MODULE 1: DELIVERY-CONTACT MATCHING (Ceragem Specific) ---
if option == "Delivery-Contact Matcher":
    st.title("📊 Ceragem Delivery-Contact Reconciliation")
    st.info("Logic: Matching Delivery No (PDF) with Contact No (GI Report).")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_pdfs = st.file_uploader("1. Upload Invoices (PDF)", type="pdf", accept_multiple_files=True)
    with col2:
        gi_file = st.file_uploader("2. Upload GI Report (Excel/CSV)", type=["xlsx", "csv"])

    if st.button("Run Reconciliation"):
        if uploaded_pdfs and gi_file:
            try:
                # PDF Extraction logic
                all_inv_data = []
                for pdf_file in uploaded_pdfs:
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                delivery_match = re.search(r"Delivery\s*no\s*[:.]?\s*(\d+)", text, re.IGNORECASE)
                                inv_no = re.search(r"(?:Serial No\. Of Challan|RAL-)\s*[:.]?\s*([\w-]+)", text)
                                order_no = re.search(r"S\.Order No\s*(\d+)", text)
                                date_match = re.search(r"Date of Challan\s*([\d\w-]+)", text)
                                
                                if delivery_match:
                                    all_inv_data.append({
                                        "Delivery No": delivery_match.group(1).strip(),
                                        "Invoice No.": inv_no.group(1) if inv_no else "",
                                        "S. Order No.": order_no.group(1) if order_no else "",
                                        "Invoice Date": date_match.group(1) if date_match else ""
                                    })
                df_pdf = pd.DataFrame(all_inv_data).drop_duplicates(subset=["Delivery No"])

                # GI Report Reading (Using openpyxl engine)
                if gi_file.name.endswith('.csv'):
                    df_gi = pd.read_csv(gi_file)
                else:
                    df_gi = pd.read_excel(gi_file, engine='openpyxl')
                
                df_gi.columns = df_gi.columns.str.strip()

                # Matching Column Identification
                gi_match_col = None
                for col in ['Contact No', 'CONTACT', 'Mobile', 'Customer Contact']:
                    if col in df_gi.columns:
                        gi_match_col = col
                        break
                
                if gi_match_col:
                    df_gi[gi_match_col] = df_gi[gi_match_col].astype(str).str.extract('(\d+)')
                    df_pdf['Delivery No'] = df_pdf['Delivery No'].astype(str)

                    # Merge
                    final_df = pd.merge(df_pdf, df_gi, left_on='Delivery No', right_on=gi_match_col, how='left')
                    
                    # Exact Sample Sequence as requested
                    desired_columns = ["Invoice No.", "S. Order No.", "Invoice Date", "Delivery No", "Status", "TRACKING NO", "Courier Name", "Remark"]
                    for col in desired_columns:
                        if col not in final_df.columns: final_df[col] = ""
                    
                    st.success("Matching Complete!")
                    st.dataframe(final_df[desired_columns])
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        final_df[desired_columns].to_excel(writer, index=False)
                    st.download_button("📥 Download Result", data=output.getvalue(), file_name="Ceragem_Reconciled_MIS.xlsx")
            except Exception as e:
                st.error(f"Error: {e}")

# --- MODULE 2: DUAL-SET MATCHER (Zip Based) ---
elif option == "Dual-Set Invoice Matcher":
    st.title("📂 Dual-Set Invoice & E-Way Bill Pairing")
    # ... (Aapka purana ZIP matching code yahan insert karein)
    st.warning("Please upload your ZIP files for Invoice and E-Way bill matching.")

# --- MODULE 3: FAST PDF MERGER ---
elif option == "Fast PDF Merger":
    st.title("🔗 Fast PDF Merger")
    uploaded_pdfs = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if st.button("Merge"):
        if uploaded_pdfs:
            merged = fitz.open()
            for p in uploaded_pdfs:
                with fitz.open(stream=p.read(), filetype="pdf") as t: merged.insert_pdf(t)
            out = io.BytesIO()
            merged.save(out)
            st.download_button("Download Merged", out.getvalue(), "Merged.pdf")

# --- MODULE 4: MIS DATA EXTRACTOR ---
elif option == "MIS Data Extractor":
    st.title("📄 MIS Data Extractor (PDF to Excel)")
    # ... (Aapka purana MIS extraction logic yahan insert karein)

st.sidebar.markdown("---")
st.sidebar.caption("🚀 Developed by Rohit Pal")
