import streamlit as st
import pandas as pd
import pdfplumber
import os
import re
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
import io

# --- Page Config ---
st.set_page_config(page_title="Logistics Automation Tool", layout="wide")
st.title("🚀 Daily Operation ")

# Sidebar for Navigation
option = st.sidebar.selectbox(
    'Kaunsa kaam karna hai?',
    ('Excel MIS Extractor', 'Fast PDF Merger', 'SKU Sorting (CSV Based)')
)

# --- 1. EXCEL MIS EXTRACTOR ---
if option == 'Excel MIS Extractor':
    st.header("📄 Invoice Data Extractor")
    st.write("Multiple PDFs upload karein, ye unse Invoice aur Order details nikal lega.")
    
    uploaded_files = st.file_uploader("Upload PDF Files", type="pdf", accept_multiple_files=True)
    
    if st.button("Generate MIS Report"):
        if uploaded_files:
            all_rows = []
            progress_bar = st.progress(0)
            
            for idx, uploaded_file in enumerate(uploaded_files):
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            inv_no = re.search(r"Serial No\. Of Invoice\s*:\s*([\w-]+)", text)
                            order_no = re.search(r"S\.Order No\s*:\s*(\d+)", text)
                            delivery_no = re.search(r"Delivery no\s*:\s*(\d+)", text)
                            invoice_val = re.search(r"Total Invoice Value \(In figure\)\s*:\s*([\d,.]+)", text)
                            
                            if order_no:
                                all_rows.append({
                                    "File Name": uploaded_file.name,
                                    "Invoice No": inv_no.group(1) if inv_no else "N/A",
                                    "S.Order No": order_no.group(1),
                                    "Delivery No": delivery_no.group(1) if delivery_no else "N/A",
                                    "Invoice Value": invoice_val.group(1) if invoice_val else "0"
                                })
                progress_bar.progress((idx + 1) / len(uploaded_files))

            if all_rows:
                df = pd.DataFrame(all_rows)
                df.drop_duplicates(subset=["Invoice No", "S.Order No"], inplace=True)
                st.dataframe(df)
                
                # Excel Download Button
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')
                st.download_button(label="📥 Download Excel Report", data=output.getvalue(), file_name="MIS_Report.xlsx")
        else:
            st.error("Pehle PDF files upload karein!")

# --- 2. FAST PDF MERGER ---
elif option == 'Fast PDF Merger':
    st.header("🔗 Fast PDF Merger")
    st.write("Bahut saari PDFs ko jaldi se ek file mein merge karein.")
    
    uploaded_pdfs = st.file_uploader("Upload PDFs to Merge", type="pdf", accept_multiple_files=True)
    
    if st.button("Merge Files"):
        if uploaded_pdfs:
            result = fitz.open()
            for uploaded_pdf in uploaded_pdfs:
                pdf_bytes = uploaded_pdf.read()
                with fitz.open(stream=pdf_bytes, filetype="pdf") as temp:
                    result.insert_pdf(temp)
            
            output_pdf = io.BytesIO()
            result.save(output_pdf)
            st.success(f"✅ {len(uploaded_pdfs)} Files Merge ho gayi hain!")
            st.download_button("📥 Download Merged PDF", data=output_pdf.getvalue(), file_name="Merged_Labels.pdf")
        else:
            st.warning("Kuch PDFs to upload karo bhai!")

# --- 3. SKU SORTING (CSV BASED) ---
elif option == 'SKU Sorting (CSV Based)':
    st.header("🔀 SKU Sorting (CSV Sequence)")
    st.write("PDF labels ko CSV mein diye gaye SKU sequence ke hisaab se arrange karein.")
    
    col1, col2 = st.columns(2)
    with col1:
        main_pdf = st.file_uploader("Main PDF (Labels)", type="pdf")
    with col2:
        sku_csv = st.file_uploader("CSV (Sequence List)", type="csv")
    
    if st.button("Reorder PDF"):
        if main_pdf and sku_csv:
            try:
                df = pd.read_csv(sku_csv)
                sku_list = df.iloc[:, 0].astype(str).tolist() if 'SKU' not in df.columns else df['SKU'].astype(str).tolist()
                
                reader = PdfReader(main_pdf)
                writer = PdfWriter()
                
                pdf_pages_map = {sku: [] for sku in sku_list}
                leftover_pages = []

                for page in reader.pages:
                    text = page.extract_text() or ""
                    matched = False
                    for sku in sku_list:
                        if sku in text:
                            pdf_pages_map[sku].append(page)
                            matched = True
                            break
                    if not matched:
                        leftover_pages.append(page)

                # Build New PDF
                for sku in sku_list:
                    for page in pdf_pages_map.get(sku, []):
                        writer.add_page(page)
                
                for page in leftover_pages:
                    writer.add_page(page)

                output_stream = io.BytesIO()
                writer.write(output_stream)
                st.success("Sorting Complete!")
                st.download_button("📥 Download Sorted PDF", data=output_stream.getvalue(), file_name="Sorted_Labels.pdf")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Donon files (PDF aur CSV) zaroori hain.")

st.sidebar.markdown("---")
st.sidebar.info("Developed for Rohit Pal")