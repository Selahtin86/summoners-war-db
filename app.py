from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path("data/monsters.csv")
ELEMENT_ORDER = ["Fire", "Water", "Wind", "Light", "Dark"]
ELEMENT_ICONS = {
    "Fire": "🔥",
    "Water": "💧",
    "Wind": "🍃",
    "Light": "☀️",
    "Dark": "🌑",
}

st.set_page_config(page_title="Summoners War Monster DB", page_icon="⚔️", layout="wide")

st.title("⚔️ Summoners War Monster Database")
st.caption(
    "Filterbare Monsterliste auf Basis von summonerswarskyarena.info. "
    "Die Monsterbilder werden über die Original-Bild-URLs der Quelle angezeigt."
)

if not DATA_PATH.exists():
    st.info("Die Monsterdaten werden gerade automatisch erstellt. Bitte später nochmals laden.")
    st.stop()


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, dtype=str).fillna("")
    df["source_order_num"] = pd.to_numeric(df.get("source_order", ""), errors="coerce")
    return df


df = load_data()

with st.sidebar:
    st.header("Filter")
    search = st.text_input("Monster oder Familie", placeholder="z. B. Riley, Inugami, Panda …")

    available_elements = [e for e in ELEMENT_ORDER if e in set(df["element"])]
    selected_elements = st.multiselect("Element", available_elements)

    stars = sorted(
        [s for s in df["star_grade"].unique() if s],
        key=lambda value: int(value) if str(value).isdigit() else 99,
    )
    selected_stars = st.multiselect("Nat-Sterne", stars)

    monster_types = sorted(t for t in df["monster_type"].unique() if t)
    selected_types = st.multiselect("Typ", monster_types)

    families = sorted(f for f in df["monster_family"].unique() if f)
    selected_families = st.multiselect("Monsterfamilie", families)

    only_with_image = st.toggle("Nur Monster mit Bild", value=True)

filtered = df.copy()

if search:
    needle = search.casefold().strip()
    mask = (
        filtered["awakened_name"].str.casefold().str.contains(needle, regex=False)
        | filtered["monster_family"].str.casefold().str.contains(needle, regex=False)
    )
    filtered = filtered[mask]

if selected_elements:
    filtered = filtered[filtered["element"].isin(selected_elements)]
if selected_stars:
    filtered = filtered[filtered["star_grade"].isin(selected_stars)]
if selected_types:
    filtered = filtered[filtered["monster_type"].isin(selected_types)]
if selected_families:
    filtered = filtered[filtered["monster_family"].isin(selected_families)]
if only_with_image:
    filtered = filtered[filtered["image_url"].astype(bool)]

filtered = filtered.sort_values(["source_order_num", "awakened_name"], kind="stable")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Gefunden", len(filtered))
c2.metric("Gesamt", len(df))
c3.metric("Familien", df["monster_family"].nunique())
c4.metric("Mit Bild", int(df["image_url"].astype(bool).sum()))

st.divider()

if filtered.empty:
    st.warning("Für diese Filter wurden keine Monster gefunden.")
    st.stop()

cards_per_row = 6
rows = filtered.to_dict("records")
for start in range(0, len(rows), cards_per_row):
    columns = st.columns(cards_per_row)
    for column, monster in zip(columns, rows[start : start + cards_per_row]):
        with column:
            with st.container(border=True):
                if monster.get("image_url"):
                    st.image(monster["image_url"], use_container_width=True)

                name = monster.get("awakened_name") or monster.get("monster_family") or "Unbekannt"
                st.markdown(f"**{name}**")

                element = monster.get("element", "")
                icon = ELEMENT_ICONS.get(element, "")
                family = monster.get("monster_family", "")
                stars = monster.get("star_grade", "")
                monster_type = monster.get("monster_type", "")
                details = [
                    f"{icon} {element}".strip() if element else "",
                    family,
                    f"Nat {stars}" if stars else "",
                    monster_type,
                ]
                st.caption(" · ".join(part for part in details if part))

                if monster.get("monster_url"):
                    st.link_button("Monsterseite", monster["monster_url"], use_container_width=True)
