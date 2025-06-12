
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.title("Card Creator from Excel")

st.markdown("Upload an Excel (.xlsx) file with the following **required columns**: 'Card Title', 'Card Description', and optional: 'Custom ID (Header)', 'Start Date', 'Finish Date'.")

# === Required user inputs ===
domain = st.text_input("LeanKit Domain (e.g. 'ngarrett')", help="Your LeanKit subdomain (before .leankit.com)")
token = st.text_input("LeanKit API Token", type="password")
board_id = st.text_input("Board ID", help="The ID of the LeanKit board")

uploaded_file = st.file_uploader("Choose Excel File", type=["xlsx"])

def format_date(date_val):
    if pd.isna(date_val):
        return None
    try:
        return pd.to_datetime(date_val).strftime('%Y-%m-%d')
    except:
        return None

if uploaded_file and domain and token and board_id:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    st.write("Preview of uploaded file:")
    st.dataframe(df.head())

    if st.button("Create Cards"):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        created_count = 0
        for idx, row in df.iterrows():
            payload = {
                "title": row.get("Card Title", ""),
                "description": row.get("Card Description", ""),
                "boardId": board_id,
                "cardId": "newCard"
            }

            # Optional: customId
            custom_id = row.get("Custom ID (Header)")
            if pd.notna(custom_id):
                payload["customId"] = str(custom_id)

            # Optional: start/finish dates
            start_date = format_date(row.get("Start Date"))
            finish_date = format_date(row.get("Finish Date"))
            if start_date:
                payload["plannedStart"] = start_date
            if finish_date:
                payload["plannedFinish"] = finish_date

            url = f"https://{domain}.leankit.com/io/card"
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code in (200, 201):
                created_count += 1
            else:
                st.error(f"❌ Row {idx + 1} failed: {response.status_code} — {response.text}")

        st.success(f"✅ {created_count} cards created successfully.")

elif uploaded_file:
    st.warning("Please enter domain, token, and board ID before submitting.")
