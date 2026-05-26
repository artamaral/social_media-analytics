import argparse
import os
import re
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

from src.carrosnaweb_client import BASE_URL, create_session, safe_get


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data", "discovery")
DEBUG_DIR = os.path.join(SCRIPT_DIR, "data", "debug_html", "anos_modelo")
MODELOS_CSV = os.path.join(DATA_DIR, "modelos.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "anos_modelo.csv")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai anos por modelo do Carros na Web a partir de modelos.csv."
    )
    parser.add_argument(
        "--modelos-csv",
        default=MODELOS_CSV,
        help="Caminho do CSV de modelos.",
    )
    parser.add_argument(
        "--output-csv",
        default=OUTPUT_CSV,
        help="Caminho do CSV final de anos por modelo.",
    )
    return parser.parse_args()


def resolve_modelos_csv(csv_path):
    if os.path.exists(csv_path):
        return csv_path

    search_roots = [
        DATA_DIR,
        os.path.join(SCRIPT_DIR, "data"),
        SCRIPT_DIR,
    ]
    for root in search_roots:
        for current_root, _, files in os.walk(root):
            if "modelos.csv" in files:
                candidate = os.path.join(current_root, "modelos.csv")
                print(f"[LOAD] modelos.csv encontrado automaticamente em: {candidate}")
                return candidate

    raise FileNotFoundError(
        "Nao foi encontrado modelos.csv. "
        f"Caminho esperado: {csv_path}. "
        "Gere primeiro a camada de modelos ou informe "
        "--modelos-csv com o caminho correto."
    )


def safe_filename(text):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(text)).strip("_")


def save_debug_html(html, fabricante, modelo):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    file_name = f"{safe_filename(fabricante)}__{safe_filename(modelo)}.html"
    path = os.path.join(DEBUG_DIR, file_name)

    with open(path, "w", encoding="utf-8", errors="ignore") as html_file:
        html_file.write(html)

    return path


def load_modelos_csv(csv_path):
    csv_path = resolve_modelos_csv(csv_path)
    df = pd.read_csv(csv_path)

    print(f"[LOAD] Modelos carregados: {len(df)}")
    print("[LOAD] Colunas:", list(df.columns))
    print(df.head())

    return df


def extract_year_from_text(text):
    match = re.search(r"\b(19\d{2}|20\d{2})\b", str(text))
    if match:
        return match.group(1)
    return None


def inspect_page(html, fabricante, modelo, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    all_links = soup.find_all("a", href=True)

    print("\n[DEBUG PAGE]")
    print("Fabricante:", fabricante)
    print("Modelo:", modelo)
    print("URL:", url)
    print("Title:", title)
    print("HTML size:", len(html))
    print("Total links:", len(all_links))

    relevant = []
    for a_tag in all_links:
        href = a_tag.get("href", "")
        text = a_tag.get_text(" ", strip=True)
        if (
            "ano" in href.lower()
            or "anomod" in href.lower()
            or "catalogo" in href.lower()
            or "fichadetalhe" in href.lower()
            or extract_year_from_text(text)
        ):
            relevant.append((href, text))

    print("Links potencialmente relevantes:", len(relevant))
    for href, text in relevant[:60]:
        print(f"href={href} | text={text}")

    debug_path = save_debug_html(html, fabricante, modelo)
    print("[DEBUG HTML] salvo em:", debug_path)
    return soup


def extract_year_links(html, fabricante, modelo, url_modelo):
    soup = BeautifulSoup(html, "html.parser")
    anos = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        texto_link = a_tag.get_text(" ", strip=True)

        full_url = urljoin(BASE_URL, href.replace("\\", "/"))
        parsed = urlparse(full_url)
        params = parse_qs(parsed.query)

        ano = None
        for key in ["ano", "anomod", "anofim", "anoini"]:
            if key in params:
                possible_year = extract_year_from_text(params[key][0])
                if possible_year:
                    ano = possible_year
                    break

        if not ano:
            ano = extract_year_from_text(texto_link)

        if not ano:
            ano = extract_year_from_text(full_url)

        if not ano:
            continue

        href_lower = href.lower()
        is_candidate = "catalogo" in href_lower or "fichadetalhe" in href_lower
        if not is_candidate:
            continue

        anos.append(
            {
                "fabricante": fabricante,
                "modelo": modelo,
                "ano": ano,
                "url_ano": full_url,
                "url_modelo_origem": url_modelo,
                "href_original": href,
                "texto_link": texto_link,
                "params": str(params),
            }
        )

    return anos


def scrape_anos_modelo(modelos_df, session):
    all_years = []
    total = len(modelos_df)

    for idx, row in modelos_df.iterrows():
        fabricante = row["fabricante"]
        modelo = row["modelo"]
        url_modelo = row["url_modelo"]

        print("\n" + "=" * 80)
        print(f"[{idx + 1}/{total}] {fabricante} | {modelo}")
        print("URL modelo:", url_modelo)

        try:
            response = safe_get(session, url_modelo, timeout=30, delay_min=1.5, delay_max=3.0)

            inspect_page(
                html=response.text,
                fabricante=fabricante,
                modelo=modelo,
                url=url_modelo,
            )

            years = extract_year_links(
                html=response.text,
                fabricante=fabricante,
                modelo=modelo,
                url_modelo=url_modelo,
            )

            print(f"[RESULT] Anos encontrados: {len(years)}")
            for item in years[:20]:
                print(item)

            all_years.extend(years)

        except Exception as exc:
            print(f"[ERROR] Erro em {fabricante} | {modelo}: {exc}")

    return pd.DataFrame(all_years)


def clean_anos_modelo(df):
    if df.empty:
        print("[CLEAN] DataFrame vazio.")
        return df

    df = df.copy()
    before = len(df)
    df.drop_duplicates(
        subset=["fabricante", "modelo", "ano", "url_ano"],
        inplace=True,
    )
    df.sort_values(by=["fabricante", "modelo", "ano"], inplace=True)
    after = len(df)

    print(f"[CLEAN] Antes: {before} | Depois: {after}")
    return df


def save_csv(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print("[SAVE] CSV salvo em:", output_path)


def main():
    args = parse_args()
    session = create_session()
    modelos_df = load_modelos_csv(args.modelos_csv)
    anos_df = scrape_anos_modelo(modelos_df=modelos_df, session=session)
    anos_df = clean_anos_modelo(anos_df)
    save_csv(df=anos_df, output_path=args.output_csv)

    print("\nFINALIZADO")
    print("Total anos encontrados:", len(anos_df))
    if not anos_df.empty:
        print(anos_df.head(30))


if __name__ == "__main__":
    main()
