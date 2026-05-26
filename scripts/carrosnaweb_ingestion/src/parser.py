from dataclasses import asdict, dataclass
from typing import List

from bs4 import BeautifulSoup


BASE_URL = "https://www.carrosnaweb.com.br"


@dataclass
class TechnicalRow:
    fabricante: str
    modelo: str
    ano: str
    versao: str
    codigo_ficha: str
    url_ficha: str
    page_title: str
    group: str
    field: str
    value: str
    image_urls: str
    collection_status: str
    raw_html_path: str


def clean_text(text):
    if not text:
        return ""
    return " ".join(text.replace("\xa0", " ").split()).strip()


def extract_image_urls(cell):
    urls = []
    for img in cell.find_all("img"):
        src = clean_text(img.get("src", ""))
        if not src:
            continue
        src = src.replace("\\", "/")
        if src.startswith("http://") or src.startswith("https://"):
            urls.append(src)
        else:
            urls.append(f"{BASE_URL}/{src.lstrip('./')}")
    return urls


def looks_like_group_header(values):
    if len(values) != 1:
        return False

    value = values[0]
    if not value:
        return False

    has_digit = any(char.isdigit() for char in value)
    alpha_ratio = sum(char.isalpha() for char in value) / max(len(value), 1)
    return (
        not has_digit
        and len(value) <= 40
        and alpha_ratio >= 0.6
        and value == value.upper()
    )


def parse_ficha_tables(
    html,
    ficha_url,
    codigo_ficha,
    fabricante="",
    modelo="",
    ano="",
    versao="",
    collection_status="success",
    raw_html_path="",
) -> List[TechnicalRow]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = clean_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    rows: List[TechnicalRow] = []
    current_group = "GERAL"
    seen = set()

    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue

        cell_texts = [clean_text(cell.get_text(" ", strip=True)) for cell in cells]
        non_empty = [text for text in cell_texts if text]
        if not non_empty:
            continue

        if looks_like_group_header(non_empty):
            current_group = non_empty[0]
            continue

        for index in range(0, len(cells) - 1, 2):
            field_cell = cells[index]
            value_cell = cells[index + 1]

            field_name = clean_text(field_cell.get_text(" ", strip=True))
            field_value = clean_text(value_cell.get_text(" ", strip=True))

            if not field_name or not field_value:
                continue

            if field_name.lower() in {"compartilhe", "busca detalhada", "avalie"}:
                continue

            unique_key = (current_group, field_name, field_value)
            if unique_key in seen:
                continue
            seen.add(unique_key)

            rows.append(
                TechnicalRow(
                    fabricante=fabricante,
                    modelo=modelo,
                    ano=ano,
                    versao=versao,
                    codigo_ficha=codigo_ficha,
                    url_ficha=ficha_url,
                    page_title=page_title,
                    group=current_group,
                    field=field_name,
                    value=field_value,
                    image_urls=" | ".join(extract_image_urls(value_cell)),
                    collection_status=collection_status,
                    raw_html_path=raw_html_path,
                )
            )

    return rows


def technical_rows_to_dicts(rows: List[TechnicalRow]):
    return [asdict(row) for row in rows]

