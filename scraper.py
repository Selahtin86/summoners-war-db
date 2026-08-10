from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://summonerswarskyarena.info/monster-list/"
OUTPUT_PATH = Path("data/monsters.csv")


def _clean(text: str) -> str:
    return " ".join(text.split())


def scrape_monsters() -> list[dict[str, str]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        )
    }
    response = requests.get(SOURCE_URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table tbody tr")

    monsters: list[dict[str, str]] = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        row_text = [_clean(cell.get_text(" ", strip=True)) for cell in cells]
        if not any(row_text):
            continue

        image = row.find("img")
        image_url = ""
        if image:
            image_url = (
                image.get("data-src")
                or image.get("data-lazy-src")
                or image.get("src")
                or ""
            )
            image_url = urljoin(SOURCE_URL, image_url)

        links = row.find_all("a", href=True)
        monster_url = ""
        for link in links:
            href = link.get("href", "")
            if href and "monster-list" not in href and not href.startswith("#"):
                monster_url = urljoin(SOURCE_URL, href)
                break

        # The site currently exposes rows similar to:
        # Star Grade | Monster family | Element | Awakened name | Awakening Essences | Skill Ups
        # We intentionally keep both normalized fields and the full row text so that
        # changes in the website structure do not silently destroy information.
        star_grade = row_text[0] if len(row_text) > 0 else ""
        monster_family = row_text[1] if len(row_text) > 1 else ""

        element = ""
        awakened_name = ""
        known_elements = {"Fire", "Water", "Wind", "Light", "Dark"}

        for value in row_text:
            if value in known_elements:
                element = value
                break

        # The awakened name is usually the first meaningful text value after the element.
        if element:
            try:
                idx = row_text.index(element)
                for candidate in row_text[idx + 1 :]:
                    if candidate and candidate not in known_elements and not candidate.isdigit():
                        awakened_name = candidate
                        break
            except ValueError:
                pass

        # Fallback: use the strongest heading/label available in the row.
        if not awakened_name:
            heading = row.find(["h2", "h3", "h4", "strong"])
            if heading:
                awakened_name = _clean(heading.get_text(" ", strip=True))

        monsters.append(
            {
                "star_grade": star_grade,
                "monster_family": monster_family,
                "element": element,
                "awakened_name": awakened_name,
                "image_url": image_url,
                "monster_url": monster_url,
                "source_url": SOURCE_URL,
                "raw_row": " | ".join(row_text),
            }
        )

    # Remove exact duplicates while preserving page order.
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for monster in monsters:
        key = (
            monster["monster_family"],
            monster["element"],
            monster["awakened_name"],
            monster["image_url"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(monster)

    return unique


def save_csv(monsters: list[dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "star_grade",
        "monster_family",
        "element",
        "awakened_name",
        "image_url",
        "monster_url",
        "source_url",
        "raw_row",
    ]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(monsters)


if __name__ == "__main__":
    monsters = scrape_monsters()
    save_csv(monsters)
    print(f"Saved {len(monsters)} monster rows to {OUTPUT_PATH}")
