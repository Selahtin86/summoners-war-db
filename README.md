# Summoners War Monster Database

Eine kleine, filterbare Streamlit-Datenbank für **Summoners War: Sky Arena**.

## Datenbasis

Die Monsterdaten werden aus der Monsterliste von `summonerswarskyarena.info` eingelesen:

`https://summonerswarskyarena.info/monster-list/`

Der aktuelle Datensatz enthält **1'025 Monstereinträge**. Für jeden Eintrag werden unter anderem gespeichert:

- erwachter Monstername
- Monsterfamilie
- Element
- Nat-Sterne
- Monstertyp
- Original-Bild-URL des erwachten Monsters
- Original-Bild-URL der Basisform
- Link zur Monsterseite
- Awakening-Essenzen
- Skill-Ups

## Dateien

- `app.py` – Streamlit-Weboberfläche
- `scrape_monsters.py` – Scraper und Datenvalidierung
- `data/monsters.csv` – erzeugter Monster-Datensatz
- `.github/workflows/scrape-monsters.yml` – automatische Aktualisierung des Datensatzes
- `requirements.txt` – Python-Abhängigkeiten

## Filter in der App

Aktuell kann nach folgenden Merkmalen gefiltert werden:

- Monstername / Monsterfamilie
- Element
- Nat-Sterne
- Monstertyp
- Monsterfamilie

Die App zeigt die **Original-Monsterbilder aus der Quelldatenbank** und keine generierten Ersatzbilder.

## Automatische Aktualisierung

GitHub Actions führt den Scraper automatisch aus:

- bei Änderungen am Scraper oder Workflow
- manuell über `workflow_dispatch`
- einmal wöchentlich

Der erzeugte Datensatz wird nach erfolgreicher Validierung automatisch nach `data/monsters.csv` committed.

## Nächster Ausbauschritt

Als Nächstes werden R5-Rollen ergänzt, insbesondere:

- Tank
- Damage Reducer
- Cleanser / Healer
- Healer
- Damage Dealer

Ein Monster kann dabei mehreren Rollen gleichzeitig zugeordnet werden.

## Lokaler Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Der Datensatz liegt bereits im Repository. Ein manuelles Scraping ist für die normale Nutzung nicht erforderlich.
