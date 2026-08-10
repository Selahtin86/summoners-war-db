from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

SOURCE_URL = "https://summonerswarskyarena.info/monster-list/"
OUTPUT_PATH = Path("data/monsters.csv")
ELEMENTS = {"fire": "Fire", "water": "Water", "wind": "Wind", "light": "Light", "dark": "Dark"}
KNOWN_MONSTERS = {"Darion", "Colleen", "Xiong Fei", "Riley", "Kro", "Xiao Lin"}


def clean(text: str) -> str:
    return " ".join(text.split())


def get_image_url(cell: Tag) -> str:
    img = cell.find("img")
    if not img:
        return ""
    raw = (
        img.get("data-src")
        or img.get("data-lazy-src")
        or img.get("data-original")
        or img.get("src")
        or ""
    )
    if not raw:
        srcset = img.get("data-srcset") or img.get("srcset") or ""
        if srcset:
            raw = srcset.split(",")[0].strip().split(" ")[0]
    return urljoin(SOURCE_URL, raw) if raw else ""


def parse_row(row: Tag, source_order: int) -> dict[str, str] | None:
    # Current source layout:
    # 0 stars | 1 base icon | 2 family+element | 3 awakened icon |
    # 4 awakened name | 5 awakening essences | 6 skillups
    cells = row.find_all("td", recursive=False)
    if len(cells) < 7 or "searchable" not in (row.get("class") or []):
        return None

    star_grade = clean(str(row.get("data-stars", ""))) or clean(cells[0].get_text(" ", strip=True))
    if star_grade not in {"1", "2", "3", "4", "5"}:
        return None

    raw_element = clean(str(row.get("data-element", ""))).lower()
    element = ELEMENTS.get(raw_element, "")
    if not element:
        element_text = clean(cells[2].get_text(" ", strip=True))
        for key, label in ELEMENTS.items():
            if key in element_text.lower().split():
                element = label
                break

    monster_family = clean(str(cells[1].get("data-sort-value", "")))
    if not monster_family:
        heading = cells[2].find(["h2", "h3", "h4", "strong"])
        monster_family = clean(heading.get_text(" ", strip=True)) if heading else ""

    awakened_name = clean(str(cells[3].get("data-sort-value", "")))
    if not awakened_name:
        awakened_name = clean(cells[4].get_text(" ", strip=True))

    monster_url = clean(str(row.get("data-link", "")))
    if monster_url:
        monster_url = urljoin(SOURCE_URL, monster_url)

    return {
        "source_order": str(source_order),
        "star_grade": star_grade,
        "monster_type": clean(str(row.get("data-type", ""))),
        "monster_family": monster_family,
        "element": element,
        "awakened_name": awakened_name,
        "image_url": get_image_url(cells[3]),
        "base_image_url": get_image_url(cells[1]),
        "monster_url": monster_url,
        "awakening_essences": clean(cells[5].get_text(" ", strip=True)),
        "skill_ups": clean(cells[6].get_text(" ", strip=True)),
        "source_url": SOURCE_URL,
    }


def scrape_monsters() -> list[dict[str, str]]:
    response = requests.get(
        SOURCE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36"
            )
        },
        timeout=45,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    monsters: list[dict[str, str]] = []

    for row in soup.select("tr.searchable"):
        parsed = parse_row(row, len(monsters) + 1)
        if parsed:
            monsters.append(parsed)

    # Deduplicate while preserving the exact source order.
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for monster in monsters:
        key = (monster["monster_family"], monster["element"], monster["awakened_name"])
        if key in seen:
            continue
        seen.add(key)
        monster["source_order"] = str(len(unique) + 1)
        unique.append(monster)

    return unique


def validate(monsters: list[dict[str, str]]) -> None:
    if len(monsters) < 900:
        raise RuntimeError(f"Only {len(monsters)} rows parsed; expected at least 900.")

    missing_element = [m for m in monsters if not m["element"]]
    missing_name = [m for m in monsters if not m["awakened_name"]]
    missing_family = [m for m in monsters if not m["monster_family"]]
    missing_image = [m for m in monsters if not m["image_url"]]

    names = {m["awakened_name"] for m in monsters}
    missing_known = sorted(KNOWN_MONSTERS - names)

    print(f"Parsed monsters: {len(monsters)}")
    print(f"Missing element: {len(missing_element)}")
    print(f"Missing family: {len(missing_family)}")
    print(f"Missing awakened name: {len(missing_name)}")
    print(f"Missing awakened image URL: {len(missing_image)}")

    if missing_known:
        raise RuntimeError(f"Known monsters not found: {', '.join(missing_known)}")
    if missing_element:
        raise RuntimeError(f"{len(missing_element)} rows have no element.")
    if missing_name:
        raise RuntimeError(f"{len(missing_name)} rows have no awakened name.")
    if missing_image > [] and len(missing_image) > max(10, len(monsters) // 100):
        raise RuntimeError(f"Too many rows without awakened images: {len(missing_image)}")

    for sample_name in sorted(KNOWN_MONSTERS):
        sample = next(m for m in monsters if m["awakened_name"] == sample_name)
        print(
            f"CHECK {sample_name}: {sample['element']} | {sample['monster_family']} | "
            f"{sample['image_url']}"
        )


def save_csv(monsters: list[dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_order",
        "star_grade",
        "monster_type",
        "monster_family",
        "element",
        "awakened_name",
        "image_url",
        "base_image_url",
        "monster_url",
        "awakening_essences",
        "skill_ups",
        "source_url",
    ]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(monsters)


if __name__ == "__main__":
    data = scrape_monsters()
    validate(data)
    save_csv(data)
    print(f"Saved {len(data)} rows to {OUTPUT_PATH}")
