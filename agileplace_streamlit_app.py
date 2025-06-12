import pandas as pd
import requests
import argparse

# === CONFIGURATION ===
API_TOKEN = "658cc5e20e7fb8ce904aa393865f3f1aa8386b0632980cba909268ddb98928e07a44c90c09ae6b9779f1310e6229736f60a6dd5160b613b07fe4b0076450a4c8"
DOMAIN = "ngarrett"
TYPE_ID = "2313027591"
LANE_ID = "2313067301"
BOARD_ID = "2313027588"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# === FUNCTIONS ===
def create_card(title, description):
    payload = {
        "title": title,
        "description": description or "",
        "typeId": TYPE_ID,
        "laneId": LANE_ID,
        "boardId": BOARD_ID,
        "cardId": "newCard"
    }
    url = f"https://{DOMAIN}.leankit.com/io/card"
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()["id"]

def connect_cards(parent_id, child_id):
    payload = {
        "fromCardId": parent_id,
        "toCardId": child_id,
        "connectionType": "parent"
    }
    url = f"https://{DOMAIN}.leankit.com/io/card/connect"
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()

# === MAIN ===
parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True, help="Path to Excel file")
args = parser.parse_args()

df = pd.read_excel(args.file)
df.columns = df.columns.str.strip()

card_id_map = {}  # Title → ID

for i, row in df.iterrows():
    l1_title, l1_desc = row["L1"], row["L1 Description"]
    l2_title, l2_desc = row["L2"], row["L2 Description"]
    l3_title, l3_desc = row["L3"], row["L3 Description"]

    # L1
    if pd.notna(l1_title) and l1_title not in card_id_map:
        l1_id = create_card(l1_title, l1_desc)
        card_id_map[l1_title] = l1_id
        print(f"✅ Created L1: {l1_title} (ID: {l1_id})")

    # L2
    if pd.notna(l2_title) and l2_title not in card_id_map:
        l2_id = create_card(l2_title, l2_desc)
        card_id_map[l2_title] = l2_id
        print(f"✅ Created L2: {l2_title} (ID: {l2_id})")
        if pd.notna(l1_title):
            connect_cards(card_id_map[l1_title], l2_id)
            print(f"🔗 Connected {l1_title} → {l2_title}")

    # L3
    if pd.notna(l3_title) and l3_title not in card_id_map:
        l3_id = create_card(l3_title, l3_desc)
        card_id_map[l3_title] = l3_id
        print(f"✅ Created L3: {l3_title} (ID: {l3_id})")
        if pd.notna(l2_title):
            connect_cards(card_id_map[l2_title], l3_id)
            print(f"🔗 Connected {l2_title} → {l3_title}")
        
