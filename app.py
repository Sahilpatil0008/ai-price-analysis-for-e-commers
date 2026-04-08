import streamlit as st
import pandas as pd
import os
import random

st.set_page_config(layout="wide")

# -----------------------------
# SESSION STATE
# -----------------------------
if "cart" not in st.session_state:
    st.session_state.cart = {}

if "negotiation" not in st.session_state:
    st.session_state.negotiation = {}

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(base_dir, "dataset")

    all_dfs = []

    for file in os.listdir(dataset_path):
        if file.endswith(".csv"):
            path = os.path.join(dataset_path, file)

            try:
                df = pd.read_csv(path, nrows=200)
                df.columns = df.columns.str.lower().str.strip()
                df = df.loc[:, ~df.columns.duplicated()]

                name_col = next((c for c in df.columns if "title" in c or "name" in c), None)
                price_col = next((c for c in df.columns if "price" in c), None)
                image_col = next((c for c in df.columns if "image" in c), None)

                if name_col and price_col:
                    df["name"] = df[name_col].astype(str)
                    df["price"] = df[price_col]

                    if image_col:
                        df["image"] = df[image_col]
                    else:
                        df["image"] = "https://via.placeholder.com/150"

                    df["category"] = file.replace(".csv", "")
                    df = df[["name", "price", "image", "category"]]
                    df = df.dropna(subset=["name", "price"])

                    all_dfs.append(df)

            except:
                continue

    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()


df = load_data()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("📂 Categories")

if df.empty:
    st.error("No data loaded")
    st.stop()

categories = df["category"].unique().tolist()
selected_category = st.sidebar.selectbox("Select Category", categories)

# -----------------------------
# CART
# -----------------------------
st.sidebar.title("🛒 Cart")

total = 0

if len(st.session_state.cart) == 0:
    st.sidebar.write("Cart is empty")
else:
    for item in st.session_state.cart.values():
        st.sidebar.write(f"{item['name'][:30]} - ₹{item['price']}")
        total += item["price"]

st.sidebar.write(f"### Total: ₹{total}")

if st.sidebar.button("Clear Cart"):
    st.session_state.cart = {}
    st.rerun()

# -----------------------------
# PRICE LOGIC
# -----------------------------
def get_ai_price(price):
    return int(price * random.uniform(0.95, 1.0))


def get_bounds(price):
    if price < 5000:
        return int(price * 0.9), int(price * 1.05)
    return int(price * 0.95), price


# -----------------------------
# MAIN UI
# -----------------------------
st.title("🛒 AI Smart Pricing + Negotiation Engine")

filtered_df = df[df["category"] == selected_category]

for i, row in filtered_df.iterrows():

    name = str(row["name"])

    try:
        price = int(float(str(row["price"]).replace(",", "").replace("₹", "")))
    except:
        price = random.randint(500, 5000)

    image = row["image"]

    ai_price = get_ai_price(price)
    low, high = get_bounds(price)

    st.markdown("---")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.image(image, width=150)

    with col2:
        st.subheader(name[:80])
        st.caption(f"📦 {selected_category}")

        st.markdown(f"### 💰 ₹{price}")
        st.markdown(f"🤖 AI Price: ₹{ai_price}")

        # BUY NOW
        if st.button(f"🛒 Buy Now ₹{price}", key=f"buy_{i}"):
            st.session_state.cart[i] = {"name": name, "price": price}
            st.success("Added to cart")

        # OFFER
        offer = st.number_input("Your Offer", min_value=0, value=price, key=f"offer_{i}")

        # NEGOTIATE
        if st.button("💬 Negotiate", key=f"neg_{i}"):

            st.session_state.negotiation[i] = {
                "offer": offer,
                "low": low,
                "high": high,
                "status": "checking"
            }

        # -----------------------------
        # SHOW RESULT (PERSISTENT)
        # -----------------------------
        if i in st.session_state.negotiation:

            data = st.session_state.negotiation[i]
            offer = data["offer"]

            st.info("🤖 AI is evaluating your offer...")
            st.info(f"💡 Range: ₹{low} – ₹{high}")

            if offer < low:
                st.error(f"❌ Too low (Min ₹{low})")

            elif offer > high:
                st.warning("⚠️ Too high — you can pay less")

            else:
                st.success(f"✅ Deal Accepted at ₹{offer}")

                if st.button("➕ Add to Cart", key=f"add_{i}"):
                    st.session_state.cart[i] = {"name": name, "price": offer}
                    st.success("Added to cart")