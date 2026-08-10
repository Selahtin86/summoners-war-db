# summoners-war-db

Kleine Streamlit-Datenbank für Summoners War.

## Ziel

1. Alle Monster aus `https://summonerswarskyarena.info/monster-list/` einlesen.
2. Pro Monster Name, Familie, Element, Sterne und Original-Bild-URL speichern.
3. Die Daten in einer filterbaren Streamlit-Oberfläche anzeigen.
4. Danach R5-Rollen wie Tank, Damage Reducer, Cleanser/Healer, Healer und Damage Dealer ergänzen.

## Start

```bash
pip install -r requirements.txt
python scraper.py
streamlit run app.py
```

Nach dem Scraping liegt die erzeugte Datei unter `data/monsters.csv`.
