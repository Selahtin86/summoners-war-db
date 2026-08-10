from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

SOURCE_URL = "https://summonerswarskyarena.info/monster-list/"
OUTPUT_PATH = Path("data/monsters.csv")
ELEMENTS = {"Fire", "Water", "Wind", "Light", "Dark"}
KNOWN_MONSTERS = {"Darion", "Colleen", "Xiong Fei", "Riley", "Kro", "Xiao Lin"}


def clean(text: str) -> str:
    return " ".join(text.split())


def image_url(img: Tag | None) -> str:
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


def first_link_url(cell: Tag | None) -> str:
    if not cell:
        return ""
    link = cell.find("a", href=True)
    return urljoin(SOURCE_URL, link["href"]) if link else ""


def detect_element(cell: Tag, row: Tag) -> str:
    for img in cell.find_all("img"):
        for attr in ("alt", "title"):
            value = clean(str(img.get(attr, "")))
            if value in ELEMENTS:
                return value
    text = clean(cell.get_text(" ", strip=True))
    for element in ELEMENTS:
        if re.search(rf"\b{element}\b", text):
            return element
    row_text = clean(row.get_text(" ", strip=True))
    for element in ELEMENTS:
        if re.search(rf"\b{element}\b", row_text):
            return element
    return ""


def parse_row(row: Tag, source_order: int) -> dict[str, str] | None:
    cells = row.find_all("td", recursive=False)
    if len(cells) < 3:
        return None

    star_grade = clean(cells[0].get_text(" ", strip=True))
    if not re.fullmatch(r"[1-5]", star_grade):
        return None

    monster_cell = cells[1]
    awakened_cell = cells[2]

    family_heading = monster_cell.find(["h2", "h3", "h4", "strong"])
    monster_family = clean(family_heading.get_text(" ", strip=True)) if family_heading else ""
    if not monster_family:
        # The family name is normally visible as text in the Monster column.
        monster_family = clean(monster_cell.get_text(" ", strip=True))
        for element in ELEMENTS:
            monster_family = re.sub(rf"\b{element}\b", "", monster_family).strip()

    element = detect_element(monster_cell, row)

    awakened_name = clean(awakened_cell.get_text(" ", strip=True))
    if not awakened_name:
        awakened_img = awakened_cell.find("img")
        if awakened_img:
            for attr in ("alt", "title"):
                candidate = clean(str(awakened_img.get(attr, "")))
                if candidate and candidate not in ELEMENTS and candidate.lower() != "image":
                    awakened_name = candidate
                    break

    awakened_img = awakened_cell.find("img")
    base_img = monster_cell.find("img")

    awakening_essences = clean(cells[3].get_text(" ", strip=True)) if len(cells) > 3 else ""
    skill_ups = clean(cells[4].get_text(" ", strip=True)) if len(cells) > 4 else ""

    if not awakened_name and not monster_family:
        return None

    return {
        "source_order": str(source_order),
        "star_grade": star_grade,
        "monster_family": monster_family,
        "element": element,
        "awakened_name": awakened_name,
        "image_url": image_url(awakened_img),
        "base_image_url": image_url(base_img),
        "monster_url": first_link_url(awakened_cell) or first_link_url(monster_cell),
        "awakening_essences": awakening_essences,
        "skill_ups": skill_ups,
        "source_url": SOURCE_URL,
    }


def scrape_monsters() -> list[dict[str, str]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        )
    }
    response = requests.get(SOURCE_URL, headers=headers, timeout=45)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table tr")

    monsters: list[dict[str, str]] = []
    for row in rows:
        parsed = parse_row(row, len(monsters) + 1)
        if parsed:
            monsters.append(parsed)

    # Exact deduplication while preserving site order.
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for monster in monsters:
        key = (
            monster["monster_family"],
            monster["element"],
            monster["awakened_name"],
        )
        if key in seen:
            continue
        seen.add(key)
        monster["source_order"] = str(len(unique) + 1)
        unique.append(monster)

    return unique


def validate(monsters: list[dict[str, str]]) -> None:
    if len(monsters) < 500:
        raise RuntimeError(f"Only {len(monsters)} rows parsed; expected at least 500.")

    missing_element = [m for m in monsters if not m["element"]]
    missing_name = [m for m in monsters if not m["awakened_name"]]
    missing_image = [m for m in monsters if not m["image_url"]]

    names = {m["awakened_name"] for m in monsters}
    missing_known = sorted(KNOWN_MONSTERS - names)

    print(f"Parsed monsters: {len(monsters)}")
    print(f"Missing element: {len(missing_element)}")
    print(f"Missing awakened name: {len(missing_name)}")
    print(f"Missing awakened image URL: {len(missing_image)}")

    if missing_known:
        raise RuntimeError(f"Known monsters not found: {', '.join(missing_known)}")

    # A few missing fields are tolerable for special/collaboration rows, but widespread
    # failures indicate that the source HTML changed and should stop the automation.
    if len(missing_name) > max(10, len(monsters) // 50):
        raise RuntimeError("Too many rows without awakened names; source layout likely changed.")
    if len(missing_image) > max(20, len(monsters) // 20):
        raise RuntimeError("Too many rows without awakened images; source layout likely changed.")


def save_csv(monsters: list[dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_order",
        "star_grade",
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
