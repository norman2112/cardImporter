
import streamlit as st
import pandas as pd
import requests
import random
import time
from datetime import datetime

st.set_page_config(page_title="AgilePlace Card Importer", layout="wide")
st.title("📋 AgilePlace Hierarchy Uploader")

# === Sidebar Configuration ===
st.sidebar.header("🔐 API Configuration")
domain = st.sidebar.text_input("Domain (e.g., ngarrett)", key="domain")
token = st.sidebar.text_input("API Token", type="password", key="token")
board_id = st.sidebar.text_input("Board ID", key="board")
# Sample template download
with open("sample_template.xlsx", "rb") as f:
    st.sidebar.download_button(
        label="⬇️ Download Sample Excel Template",
        data=f,
        file_name="agileplace_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# === File Upload ===
uploaded_file = st.file_uploader("Upload your Excel file with card data", type=["xlsx"])

COMMENTS = [
    "This is going well.",
    "This card is at risk.",
    "Waiting on input.",
    "Escalated to manager.",
    "Dependencies cleared.",
    "High priority item."
]

def format_date(date_val):
    if pd.isna(date_val):
        return None
    return pd.to_datetime(date_val).strftime("%Y-%m-%d")

def create_card(title, description, custom_id, start_date, finish_date, header, lane_id):
    payload = {
        "title": title,
        "description": description or "",
        "typeId": TYPE_ID,
        "laneId": int(lane_id) if pd.notna(lane_id) else None,
        "boardId": board_id,
        "cardId": "newCard"
    }
    if custom_id:
        payload["customId"] = str(custom_id)
    if start_date:
        payload["plannedStart"] = format_date(start_date)
    if finish_date:
        payload["plannedFinish"] = format_date(finish_date)
    if header:
        payload["header"] = header

    url = f"https://{domain}.leankit.com/io/card"
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    card_id = response.json()["id"]
    comment = random.choice(COMMENTS)
    post_comment(card_id, comment)
    time.sleep(0.25)  # Rate limit: pause after create
    return card_id

def connect_cards(parent_id, child_id):
    url = f"https://{domain}.leankit.com/io/card/{parent_id}/connection/many"
    payload = {"connectedCardIds": [str(child_id)]}
    response = requests.post(url, json=payload, headers=HEADERS)
    time.sleep(0.25)  # Rate limit: pause after connect
    response.raise_for_status()

def post_comment(card_id, comment_text):
    url = f"https://{domain}.leankit.com/io/card/{card_id}/comment"
    payload = {"text": comment_text}
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()

if uploaded_file and domain and token and board_id:
    HEADERS = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    TYPE_ID = "2313027591"  # You can make this dynamic if needed

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    st.success("✅ File loaded and configuration accepted!")
if st.button("🚀 Run Import"):

        card_id_map = {}
        current_l1 = None
        current_l2 = None

        progress = st.progress(0)
        total_rows = len(df)

        for i, row in df.iterrows():
            l1_title, l1_desc = row["L1"], row["L1 Description"]
            l2_title, l2_desc = row["L2"], row["L2 Description"]
            l3_title, l3_desc = row["L3"], row["L3 Description"]

            if pd.isna(l1_title):
                l1_title = current_l1
            else:
                current_l1 = l1_title

            if pd.isna(l2_title):
                l2_title = current_l2
            else:
                current_l2 = l2_title

            if pd.notna(l1_title) and l1_title not in card_id_map:
                l1_id = create_card(
                    l1_title, l1_desc,
                    row.get("L1 CustomID (Header)"),
                    row.get("L1 Start Date"),
                    row.get("L1 Finish Date"),
                    row.get("L1 CustomID (Header)"),
                    row.get("L1 Lane")
                )
                card_id_map[l1_title] = l1_id
                st.write(f"✅ Created L1: {l1_title}")

            if pd.notna(l2_title) and l2_title not in card_id_map:
                l2_id = create_card(
                    l2_title, l2_desc,
                    row.get("L2 CustomID (Header)"),
                    row.get("L2 Start Date"),
                    row.get("L2 Finish Date"),
                    row.get("L2 CustomID (Header)"),
                    row.get("L2 Lane")
                )
                card_id_map[l2_title] = l2_id
                connect_cards(card_id_map[l1_title], l2_id)
                st.write(f"🔗 Connected {l1_title} → {l2_title}")

            if pd.notna(l3_title) and l3_title not in card_id_map:
                l3_id = create_card(
                    l3_title, l3_desc,
                    row.get("L3 CustomID (Header)"),
                    row.get("L3 Start Date"),
                    row.get("L3 Finish Date"),
                    row.get("L3 CustomID (Header)"),
                    row.get("L3 Lane")
                )
                card_id_map[l3_title] = l3_id
                connect_cards(card_id_map[l2_title], l3_id)
                st.write(f"🔗 Connected {l2_title} → {l3_title}")

            progress.progress((i + 1) / total_rows)

        st.success("🎉 All cards created and connected!")
        st.subheader("📄 Card Hierarchy Preview")

        levels = {"L1": [], "L2": [], "L3": []}
        edges = []
        current_l1 = None
        current_l2 = None

        for _, row in df.iterrows():
            l1, l2, l3 = row["L1"], row["L2"], row["L3"]

            if pd.notna(l1):
                current_l1 = l1
                if l1 not in levels["L1"]:
                    levels["L1"].append(l1)
            if pd.notna(l2):
                current_l2 = l2
                if l2 not in levels["L2"]:
                    levels["L2"].append(l2)
                if current_l1:
                    edges.append((current_l1, l2))
            if pd.notna(l3):
                if l3 not in levels["L3"]:
                    levels["L3"].append(l3)
                if current_l2:
                    edges.append((current_l2, l3))

        st.markdown("📁 **Hierarchy Preview**", unsafe_allow_html=True)
        for l1 in levels["L1"]:
            st.markdown(f"🔷 **{l1}**", unsafe_allow_html=True)
        for l2 in [child for parent, child in edges if parent == l1]:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🔹 {l2}", unsafe_allow_html=True)
        for l3 in [child for parent, child in edges if parent == l2]:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔸 {l3}", unsafe_allow_html=True)
        for l1 in levels["L1"]:
            st.text(f"• {l1}")
        for l2 in [child for parent, child in edges if parent == l1]:
            st.text(f"    └─ {l2}")
        for l3 in [child for parent, child in edges if parent == l2]:
            st.text(f"            └── {l3}")
        # === HIERARCHY TREE VISUALIZATION ===
        else:
            st.info("Fill in the sidebar fields and upload a file to begin.")
        # === SIMPLE HIERARCHY TEXT PREVIEW ===
