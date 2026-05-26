import argparse
import os
from urllib.parse import urlencode

import pandas as pd
from bs4 import BeautifulSoup

from src.carrosnaweb_client import BASE_URL, create_session, safe_get


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data", "discovery")
OUTPUT_CSV = os.path.join(DATA_DIR, "fabricantes.csv")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai fabricantes do Carros na Web a partir de avancada.asp."
    )
    parser.add_argument(
        "--output-csv",
        default=OUTPUT_CSV,
        help="Caminho do CSV final de fabricantes.",
    )
    return parser.parse_args()


def inspect_selects(soup):
    print("\nSELECTS encontrados:")
    for select in soup.find_all("select"):
        print(
            "name:", select.get("name"),
            "| id:", select.get("id"),
            "| options:", len(select.find_all("option")),
        )


def extract_fabricantes(html):
    soup = BeautifulSoup(html, "html.parser")
    inspect_selects(soup)

    fabricantes = []
    for select in soup.find_all("select"):
        select_name = select.get("name", "").lower()
        if "fabricante" not in select_name and "marca" not in select_name:
            continue

        for opt in select.find_all("option"):
            value = opt.get("value")
            text = opt.get_text(" ", strip=True)

            if not value or not value.strip() or not text:
                continue

            if text.lower() in {"selecione", "todos", "-"}:
                continue

            fabricantes.append(
                {
                    "fabricante": text,
                    "value": value,
                    "url": (
                        f"{BASE_URL}/catalogofabricante.asp?"
                        f"{urlencode({'fabricante': value})}"
                    ),
                }
            )

    fabricantes = list({item["url"]: item for item in fabricantes}.values())
    return pd.DataFrame(fabricantes)


def save_csv(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n[SAVE] CSV salvo em: {output_path}")


def main():
    args = parse_args()
    session = create_session()
    url = f"{BASE_URL}/avancada.asp"
    response = safe_get(session, url, timeout=20, delay_min=1.0, delay_max=2.0)

    print("status:", response.status_code)
    print("html_size:", len(response.text))

    fabricantes_df = extract_fabricantes(response.text)

    print(f"\nFabricantes encontrados: {len(fabricantes_df)}")
    print(fabricantes_df.head(50))
    save_csv(fabricantes_df, args.output_csv)


if __name__ == "__main__":
    main()
