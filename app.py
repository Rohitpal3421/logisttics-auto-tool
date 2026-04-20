import streamlit as st
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import io
import re
import zipfile

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="LogiSmart Pro | Rohit Pal", layout="wide", page_icon="🚛")

st.sidebar.title("🚛 LogiSmart v3.5")
st.sidebar.markdown("### Developed by: **Rohit Pal**")
st.sidebar.write("System: **Dual-Set Invoice Matcher**")

# --- HELPER: EXTRACT INVOICE NO ---
def extract_invoice_no(pdf_bytes):
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Logistics common patterns: INV, Serial No, or direct numbers
                    match = re.search(r"(?:Invoice No|Inv No|Serial No|Invoice#)\s*[:.]?\s*([\w\-/]+)", text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
    except:
        pass
    return None

st.title("📂 Automated Invoice & E-Way Bill Pairing (Double Set Mode)")
st.info("How it works: It matches Invoice with E-Way Bill and creates **2 copies** of each pair automatically.")

col1, col2 = st.columns(2)
with col1:
    invoice_zip = st.file_uploader("Upload Invoices ZIP", type="zip")
with col2:
    eway_zip = st.file_uploader("Upload E-Way Bills ZIP (Optional)", type="zip")

if st.button("Process & Generate 2 Sets"):
    if invoice_zip:
        inv_dict = {}
        eway_dict = {}
        
        # 1. Process Invoices
        with zipfile.ZipFile(invoice_zip, 'r') as z:
            for filename in z.namelist():
                if filename.lower().endswith('.pdf'):
                    data = z.read(filename)
                    inv_no = extract_invoice_no(data)
                    if inv_no:
                        inv_dict[inv_no] = data

        # 2. Process E-Way Bills
        if eway_zip:
            with zipfile.ZipFile(eway_zip, 'r') as z:
                for filename in z.namelist():
                    if filename.lower().endswith('.pdf'):
                        data = z.read(filename)
                        inv_no = extract_invoice_no(data)
                        if inv_no:
                            eway_dict[inv_no] = data

        # 3. Match, Sequence, and Duplicate (2 Sets)
        final_doc = fitz.open()
        summary = []

        for inv_no, inv_pdf in inv_dict.items():
            # Create a temporary buffer for one complete set (Invoice + Eway)
            temp_set = fitz.open()
            
            # Add Invoice
            with fitz.open(stream=inv_pdf, filetype="pdf") as f_inv:
                temp_set.insert_pdf(f_inv)
            
            # Add Eway Bill if exists
            has_eway = False
            if inv_no in eway_dict:
                with fitz.open(stream=eway_dict[inv_no], filetype="pdf") as f_eway:
                    temp_set.insert_pdf(f_eway)
                has_eway = True
            
            # Now add this set TWICE to the final document
            final_doc.insert_pdf(temp_set) # Set 1
            final_doc.insert_pdf(temp_set) # Set 2
            
            summary.append({
                "Invoice No": inv_no,
                "E-Way Bill": "✅ Found" if has_eway else "⚠️ Not Found",
                "Sets Created": "2 Sets (Duplicate)"
            })
            temp_set.close()

        if summary:
            st.write("### Processing Summary")
            st.table(pd.DataFrame(summary))
            
            output_pdf = io.BytesIO()
            final_doc.save(output_pdf)
            st.success("Successfully generated dual-set document!")
            st.download_button(
                label="📥 Download Final PDF (2 Sets Each)",
                data=output_pdf.getvalue(),
                file_name="RohitPal_DualSet_Invoices.pdf",
                mime="application/pdf"
            )
        else:
            st.error("No valid Invoice numbers found. Please check PDF quality.")
    else:
        st.warning("Please upload at least the Invoices ZIP file.")

st.markdown("---")
st.markdown("<center><b>Developed by Rohit Pal | Logistics Operations Automation</b></center>", unsafe_allow_html=True)
