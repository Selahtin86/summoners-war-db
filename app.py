from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path("data/monsters.csv")

st.set_page_config(page_title="Summoners War DB", page_icon="⚔️", layout="wide")
st.title("Summoners War Monster Database")
st.caption("Monsterdaten aus summonerswarskyarena.info – mit Original-Bild-URLs")

if not DATA_PATH.exists():
    st.warning(
        "Noch keine Daten gefunden. Führe zuerst `python scraper.py` aus, "
        "damit `data/monsters.csv` erstellt wird."
    )
    st.stop()

@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH).fillna("")


df = load_data()

with st.sidebar:
    st.header("Filter")
    search = st.text_input("Suche", placeholder="z. B. Riley, Inugami …")

    elements = sorted([x for x in df["element"].unique() if x])
    selected_elements = st.multiselect("Element", elements)

    stars = sorted([x for x in df["star_grade"].astype(str).unique() if x])
    selected_stars = st.multiselect("Sterne", stars)

filtered = df.copy()

if search:
    needle = search.casefold()
    filtered = filtered[
        filtered.apply(
            lambda row: needle in str(row["awakened_name"]).casefold()
            or needle in str(row["monster_family"]).casefold(),
            axis=1,
        )
    ]

if selected_elements:
    filtered = filtered[filtered["element"].isin(selected_elements)]

if selected_stars:
    filtered = filtered[filtered["star_grade"].astype(str).isin(selected_stars)]

st.write(f"**{len(filtered)} Monster gefunden**")

cols = st.columns(5)
for index, (_, monster) in enumerate(filtered.iterrows()):
    col = cols[index % len(cols)]
    with col:
        with st.container(border=True):
            if monster["image_url"]:
                st.image(monster["image_url"], use_container_width=True)
            name = monster["awakened_name"] or monster["monster_family"] or "Unbekannt"
            st.subheader(name)
            details = " · ".join(
                part
                for part in [
                    str(monster["element"]),
                    str(monster["monster_family"]),
                    f"⭐ {monster['star_grade']}" if monster["star_grade"] else "",
                ]
                if part
            )
            st.caption(details)
