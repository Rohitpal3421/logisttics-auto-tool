import streamlit as st
import pandas as pd
import pdfplumber
import re
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="LogiSmart Pro | Rohit Pal", layout="wide", page_icon="📊")

st.sidebar.title("🚛 LogiSmart v6.0")
st.sidebar.markdown("### Developer: **Rohit Pal**")
st.sidebar.write("System: **Delivery to Contact Matcher**")

st.title("📊 Ceragem Delivery-Contact Reconciliation")
st.info("Logic: Matching **Delivery No** (from PDF) with **Contact No** (from GI Report).")

col1, col2 = st.columns(2)
with col1:
    uploaded_pdfs = st.file_uploader("1. Upload Invoices (PDF)", type="pdf", accept_multiple_files=True)
with col2:
    gi_file = st.file_uploader("2. Upload GI Report (Excel/CSV)", type=["xlsx", "csv"])

if st.button("Run Reconciliation"):
    if uploaded_pdfs and gi_file:
        # --- 1. PDF EXTRACTION (Focus on Delivery No) ---
        all_inv_data = []
        for pdf_file in uploaded_pdfs:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Extracting Delivery No (Pattern: Delivery no : 8XXXXXXXX)
                        delivery_match = re.search(r"Delivery\s*no\s*[:.]?\s*(\d+)", text, re.IGNORECASE)
                        
                        # Other details for the MIS
                        inv_no = re.search(r"(?:Serial No\. Of Challan|RAL-)\s*[:.]?\s*([\w-]+)", text)
                        order_no = re.search(r"S\.Order No\s*(\d+)", text)
                        date_match = re.search(r"Date of Challan\s*([\d\w-]+)", text)
                        
                        if delivery_match:
                            del_no = delivery_match.group(1).strip()
                            all_inv_data.append({
                                "Delivery No": del_no,
                                "Invoice No": inv_no.group(1) if inv_no else pdf_file.name.replace(".pdf",""),
                                "S.Order No": order_no.group(1) if order_no else "",
                                "Invoice Date": date_match.group(1) if date_match else ""
                            })
        
        df_pdf = pd.DataFrame(all_inv_data).drop_duplicates(subset=["Delivery No"])
        
        # --- 2. GI REPORT PROCESSING ---
        if gi_file.name.endswith('.csv'):
            df_gi = pd.read_csv(gi_file)
        else:
            df_gi = pd.read_excel(gi_file)
        
        df_gi.columns = df_gi.columns.str.strip()
        
        # Finding the matching column in GI report (User said it's 'Contact No' here)
        gi_match_col = None
        for col in ['Contact No', 'CONTACT', 'Mobile', 'Customer Contact']:
            if col in df_gi.columns:
                gi_match_col = col
                break
        
        if gi_match_col:
            # Clean both columns to ensure exact matching
            df_gi[gi_match_col] = df_gi[gi_match_col].astype(str).str.extract('(\d+)')
            df_pdf['Delivery No'] = df_pdf['Delivery No'].astype(str)

            # --- 3. MERGING ON DELIVERY == CONTACT ---
            final_df = pd.merge(df_pdf, df_gi, left_on='Delivery No', right_on=gi_match_col, how='left')

            # --- 4. FORMATTING ACCORDING TO SAMPLE ---
            desired_columns = [
                "Sr.No", "Invoice No.", "S. Order No.", "Invoice Date", "Delivery No",
                "CUSTOMER_CODE", "Center Name", "Delivery location", "State", 
                "PRODUCT_NAME", "GI_QTY", "Date of Dispatch", "TRACKING NO", 
                "Courier Name", "Status", "Remark"
            ]

            # Mapping
            final_df = final_df.rename(columns={
                "Invoice No": "Invoice No.",
                "S.Order No": "S. Order No.",
                "TRACKING NO_y": "TRACKING NO",
                "STATUS": "Status"
            })

            # Add missing columns
            for col in desired_columns:
                if col not in final_df.columns:
                    final_df[col] = ""

            final_ordered_df = final_df[desired_columns]

            st.success(f"Matched {len(final_ordered_df)} records using Delivery <-> Contact logic.")
            st.dataframe(final_ordered_df.head(20), use_container_width=True)

            # Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_ordered_df.to_excel(writer, index=False, sheet_name='Reconciled_Outward')
            
            st.download_button(
                label="📥 Download Updated MIS",
                data=output.getvalue(),
                file_name="Ceragem_Delivery_Matched_MIS.xlsx"
            )
        else:
            st.error("GI Report mein Matching column (Contact No) nahi mila.")
