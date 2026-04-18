import streamlit as st
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
import io
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Logistics Automation | Rohit Pal", layout="wide", page_icon="📦")

# --- USER AUTHENTICATION SYSTEM ---
USER_DB = {
    "rohit_pal": {"password": "admin@rohit", "plan": "Premium"},
    "client_guest": {"password": "guest@123", "plan": "Free"}
}

def authenticate():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_plan"] = "Free"

    if not st.session_state["authenticated"]:
        st.sidebar.title("🔐 Secure Login")
        st.sidebar.info("Developed by: Rohit Pal")
        user = st.sidebar.text_input("Username")
        pw = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            if user in USER_DB and USER_DB[user]["password"] == pw:
                st.session_state["authenticated"] = True
                st.session_state["user_plan"] = USER_DB[user]["plan"]
                st.session_state["username"] = user
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials. Please contact Rohit Pal.")
        st.stop() 

authenticate()

# --- SIDEBAR NAVIGATION ---
st.sidebar.success(f"Welcome, {st.session_state['username']}")
st.sidebar.write(f"Account Status: **{st.session_state['user_plan']}**")

option = st.sidebar.radio(
    "Select Module",
    ("Excel MIS Extractor", "Fast PDF Merger", "SKU Sequence Sorter")
)

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

# --- MODULE 1: EXCEL MIS EXTRACTOR ---
if option == "Excel MIS Extractor":
    st.title("📄 Invoice Data Extraction (MIS)")
    st.markdown("#### System Provider: **Rohit Pal**")
    
    if st.session_state["user_plan"] != "Premium":
        st.warning("🔒 This is a Premium Feature. Please contact Rohit Pal for access.")
    else:
        uploaded_files = st.file_uploader("Upload PDF Invoices", type="pdf", accept_multiple_files=True)
        
        if st.button("Generate Report"):
            if uploaded_files:
                all_rows = []
                for uploaded_file in uploaded_files:
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
                                        "Invoice No": inv_no.group(1) if inv_no else "N/A",
                                        "Order No": order_no.group(1),
                                        "Delivery No": delivery_no.group(1) if delivery_no else "N/A",
                                        "Value": invoice_val.group(1) if invoice_val else "0"
                                    })
                
                if all_rows:
                    df = pd.DataFrame(all_rows).drop_duplicates()
                    st.dataframe(df, use_container_width=True)
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button("📥 Download Excel Report", data=output.getvalue(), file_name="MIS_Report_RohitPal.xlsx")
            else:
                st.error("No files uploaded.")

# --- MODULE 2: FAST PDF MERGER ---
elif option == "Fast PDF Merger":
    st.title("🔗 Fast PDF Merger")
    st.write("Merge documents instantly. Powered by Rohit Pal.")
    
    uploaded_pdfs = st.file_uploader("Select PDF Files", type="pdf", accept_multiple_files=True)
    
    if st.button("Execute Merge"):
        if uploaded_pdfs:
            merged_pdf = fitz.open()
            for pdf in uploaded_pdfs:
                with fitz.open(stream=pdf.read(), filetype="pdf") as temp:
                    merged_pdf.insert_pdf(temp)
            
            output_stream = io.BytesIO()
            merged_pdf.save(output_stream)
            st.success(f"Successfully merged {len(uploaded_pdfs)} documents.")
            st.download_button("📥 Download Merged PDF", data=output_stream.getvalue(), file_name="Merged_By_RohitPal.pdf")
        else:
            st.error("Please upload PDF files to proceed.")

# --- MODULE 3: SKU SEQUENCE SORTER ---
elif option == "SKU Sequence Sorter":
    st.title("🔀 SKU-Based Intelligent Sorting")
    st.write("Automated Label Sorting System")

    col1, col2 = st.columns(2)
    with col1:
        label_pdf = st.file_uploader("Upload Bulk Labels (PDF)", type="pdf")
    with col2:
        sequence_csv = st.file_uploader("Upload SKU Sequence (CSV)", type="csv")

    if st.button("Analyze & Sort"):
        if label_pdf and sequence_csv:
            try:
                df_sku = pd.read_csv(sequence_csv)
                sku_col = 'SKU' if 'SKU' in df_sku.columns else df_sku.columns[0]
                sku_order = df_sku[sku_col].astype(str).tolist()

                reader = PdfReader(label_pdf)
                writer = PdfWriter()
                
                page_map = {sku: [] for sku in sku_order}
                unmatched = []

                for page in reader.pages:
                    content = page.extract_text() or ""
                    found = False
                    for sku in sku_order:
                        if sku in content:
                            page_map[sku].append(page)
                            found = True
                            break
                    if not found:
                        unmatched.append(page)

                for sku in sku_order:
                    for p in page_map[sku]:
                        writer.add_page(p)
                
                for p in unmatched:
                    writer.add_page(p)

                final_out = io.BytesIO()
                writer.write(final_out)
                st.success("Sequence Sorting Completed.")
                st.download_button("📥 Download Sorted PDF", data=final_out.getvalue(), file_name="Sorted_Labels_RohitPal.pdf")
            except Exception as e:
                st.error(f"Sorting Error: {e}")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("🚀 **Developer: Rohit Pal**")
st.sidebar.caption("© 2026 Logistics Intelligence Portal")
