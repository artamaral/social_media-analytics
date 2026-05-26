import os
import re
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

from src.carrosnaweb_client import BASE_URL, create_session, safe_get


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data", "discovery")
DEBUG_DIR = os.path.join(SCRIPT_DIR, "data", "debug_html", "fabricantes")
FABRICANTES_CSV = os.path.join(DATA_DIR, "fabricantes.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "modelos.csv")
MAX_DEBUG_LINKS = 80


def safe_filename(text):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(text)).strip("_")


def save_debug_html(html, fabricante):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    path = os.path.join(DEBUG_DIR, f"{safe_filename(fabricante)}.html")

    with open(path, "w", encoding="utf-8", errors="ignore") as html_file:
        html_file.write(html)

    return path


def load_fabricantes_csv(csv_path):
    df = pd.read_csv(csv_path)

    print(f"[LOAD] Fabricantes carregados: {len(df)}")
    print("[LOAD] Colunas:", list(df.columns))
    print("[LOAD] Primeiras linhas:")
    print(df.head())

    return df


def inspect_page(html, fabricante, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    text = soup.get_text(" ", strip=True)
    all_links = soup.find_all("a", href=True)

    relevant_links = []
    for a_tag in all_links:
        href = a_tag.get("href", "")
        if (
            "catalog" in href.lower()
            or "fabricante" in href.lower()
            or "modelo" in href.lower()
            or "fichadetalhe" in href.lower()
        ):
            relevant_links.append((href, a_tag.get_text(" ", strip=True)))

    print("\n[DEBUG PAGE]")
    print("Fabricante:", fabricante)
    print("URL:", url)
    print("Title:", title)
    print("HTML size:", len(html))
    print("Total links <a>:", len(all_links))
    print("Links relevantes:", len(relevant_links))
    print("Contem 'Ocorreu um erro':", "Ocorreu um erro" in text)
    print("Contem 'Ficha Tecnica':", "Ficha T" in text)
    print("Contem 'Catalogo':", "Cat" in text and "logo" in text)

    print("\n[DEBUG LINKS RELEVANTES - AMOSTRA]")
    for href, label in relevant_links[:MAX_DEBUG_LINKS]:
        print(f"href={href} | text={label}")

    debug_path = save_debug_html(html, fabricante)
    print(f"\n[DEBUG HTML] salvo em: {debug_path}")
    return soup


def extract_model_links(html, fabricante, debug=False):
    soup = BeautifulSoup(html, "html.parser")
    modelos = []
    rejected = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        text = a_tag.get_text(" ", strip=True)
        href_lower = href.lower()

        is_model_candidate = (
            "catalogo.asp?" in href_lower
            or "catalogomodelo.asp?" in href_lower
        )
        if not is_model_candidate:
            continue

        full_url = urljoin(BASE_URL, href.replace("\\", "/"))
        parsed = urlparse(full_url)
        params = parse_qs(parsed.query)

        has_model_param = "varnome" in params or "modelo" in params
        if not has_model_param:
            rejected.append(
                {
                    "href": href,
                    "text": text,
                    "reason": "sem varnome/modelo nos parametros",
                    "params": params,
                }
            )
            continue

        modelo = (
            params.get("varnome", [None])[0]
            or params.get("modelo", [None])[0]
            or text
        )
        codigo_modelo = (
            params.get("codigo", [None])[0]
            or params.get("codmodelo", [None])[0]
            or params.get("modelo", [None])[0]
        )

        if not modelo:
            rejected.append(
                {
                    "href": href,
                    "text": text,
                    "reason": "modelo vazio",
                    "params": params,
                }
            )
            continue

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

    if debug:
        print("\n[DEBUG PARSER]")
        print("Candidatos aceitos:", len(modelos))
        print("Candidatos rejeitados:", len(rejected))

        print("\n[ACEITOS - AMOSTRA]")
        for item in modelos[:30]:
            print(item)

        print("\n[REJEITADOS - AMOSTRA]")
        for item in rejected[:30]:
            print(item)

    return modelos


def scrape_modelos(fabricantes_df, session):
    all_models = []
    total = len(fabricantes_df)

    for idx, row in fabricantes_df.iterrows():
        fabricante = row["fabricante"]
        fabricante_url = row["url"]

        print("\n" + "=" * 80)
        print(f"[{idx + 1}/{total}] Fabricante: {fabricante}")
        print("URL:", fabricante_url)

        try:
            response = safe_get(session, fabricante_url, timeout=30, delay_min=1.5, delay_max=3.0)

            inspect_page(
                html=response.text,
                fabricante=fabricante,
                url=fabricante_url,
            )

            modelos = extract_model_links(
                html=response.text,
                fabricante=fabricante,
                debug=True,
            )

            print(f"\n[RESULT] Modelos encontrados para {fabricante}: {len(modelos)}")
            all_models.extend(modelos)

        except Exception as exc:
            print(f"[ERROR] Erro em {fabricante}: {exc}")

    return pd.DataFrame(all_models)


def clean_modelos(modelos_df):
    if modelos_df.empty:
        print("[CLEAN] DataFrame vazio. Nada para limpar.")
        return modelos_df

    modelos_df = modelos_df.copy()
    before = len(modelos_df)

    modelos_df.drop_duplicates(
        subset=["fabricante", "modelo", "url_modelo"],
        inplace=True,
    )

    after = len(modelos_df)
    modelos_df.sort_values(by=["fabricante", "modelo"], inplace=True)
    print(f"[CLEAN] Antes: {before} | Depois duplicados: {after}")
    return modelos_df


def save_csv(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[SAVE] CSV salvo em: {output_path}")


def main():
    session = create_session()
    fabricantes_df = load_fabricantes_csv(FABRICANTES_CSV)
    modelos_df = scrape_modelos(fabricantes_df, session)
    modelos_df = clean_modelos(modelos_df)
    save_csv(modelos_df, OUTPUT_CSV)

    print("\nFINALIZADO")
    print("Total modelos:", len(modelos_df))
    if not modelos_df.empty:
        print(modelos_df.head(30))


if __name__ == "__main__":
    main()
