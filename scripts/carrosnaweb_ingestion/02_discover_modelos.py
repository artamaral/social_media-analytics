import os
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

from src.carrosnaweb_client import BASE_URL, create_session, safe_get


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data", "discovery")
FABRICANTES_CSV = os.path.join(DATA_DIR, "fabricantes.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "modelos.csv")


def load_fabricantes_csv(csv_path):
    df = pd.read_csv(csv_path)
    print(f"Fabricantes carregados: {len(df)}")
    return df


def extract_model_links(html, fabricante):
    soup = BeautifulSoup(html, "html.parser")
    modelos = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        href_lower = href.lower()

        if "catalogomodelo.asp?" not in href_lower and "catalogo.asp?" not in href_lower:
            continue

        text = a.get_text(" ", strip=True)
        if not text:
            continue

        full_url = urljoin(BASE_URL, href.replace("\\", "/"))
        parsed = urlparse(full_url)
        params = parse_qs(parsed.query)

        modelo = params.get("modelo", [None])[0] or params.get("varnome", [text])[0]
        codigo_modelo = params.get("codigo", [None])[0]

        modelos.append(
            {
                "fabricante": fabricante,
                "modelo": modelo,
                "codigo_modelo": codigo_modelo,
                "url_modelo": full_url,
                "href_original": href,
                "texto_link": text,
                "params": str(params),
            }
        )

    return modelos


def scrape_modelos(fabricantes_df, session):
    all_models = []
    total = len(fabricantes_df)

    for idx, row in fabricantes_df.iterrows():
        fabricante = row["fabricante"]
        fabricante_url = row["url"]

        print(f"\n[{idx + 1}/{total}] {fabricante}")

        try:
            response = safe_get(session, fabricante_url, timeout=30, delay_min=1.5, delay_max=3.0)
            modelos = extract_model_links(html=response.text, fabricante=fabricante)

            print(f"Modelos encontrados: {len(modelos)}")
            all_models.extend(modelos)

        except Exception as exc:
            print(f"Erro em {fabricante}: {exc}")

    return pd.DataFrame(all_models)


def clean_modelos(modelos_df):
    modelos_df = modelos_df.copy()
    modelos_df.drop_duplicates(
        subset=["fabricante", "modelo", "url_modelo"],
        inplace=True,
    )
    modelos_df.sort_values(by=["fabricante", "modelo"], inplace=True)
    return modelos_df


def save_csv(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\nCSV salvo em: {output_path}")


def main():
    session = create_session()
    fabricantes_df = load_fabricantes_csv(FABRICANTES_CSV)
    modelos_df = scrape_modelos(fabricantes_df, session)
    modelos_df = clean_modelos(modelos_df)
    save_csv(modelos_df, OUTPUT_CSV)

    print("\nFINALIZADO")
    print(f"Total modelos: {len(modelos_df)}")
    print(modelos_df.head(20))


if __name__ == "__main__":
    main()

