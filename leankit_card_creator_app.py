
import streamlit as st
import pandas as pd
import requests

# === LeanKit CONFIGURATION ===
API_TOKEN = "658cc5e20e7fb8ce904aa393865f3f1aa8386b0632980cba909268ddb98928e07a44c90c09ae6b9779f1310e6229736f60a6dd5160b613b07fe4b0076450a4c8"
DOMAIN = "ngarrett"
TYPE_ID = "1701665404"
LANE_ID = "1701665420"
BOARD_ID = "1701665398"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# === Streamlit UI ===
st.title("LeanKit Card Creator")
st.write("Upload an Excel (.xlsx) file with 'Card Title' and 'Card Description' columns.")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    st.write("Preview of uploaded file:")
    st.dataframe(df.head())

    if st.button("Create Cards"):
        created_count = 0
        for idx, row in df.iterrows():
            payload = {
                "title": row.get("Card Title", ""),
                "description": row.get("Card Description", ""),
                "typeId": TYPE_ID,
                "laneId": LANE_ID,
                "boardId": BOARD_ID,
                "cardId": "newCard"
            }
            url = f"https://{DOMAIN}.leankit.com/io/card"
            response = requests.post(url, json=payload, headers=HEADERS)

            if response.status_code in (200, 201):
                created_count += 1
            else:
                st.error(f"❌ Row {idx + 1}: Failed — {response.status_code} {response.text}")

        st.success(f"✅ {created_count} cards created successfully.")
