import argparse
import os
import re
from collections import deque
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

from src.carrosnaweb_client import BASE_URL, create_session, safe_get


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data", "discovery")
DEBUG_DIR = os.path.join(SCRIPT_DIR, "data", "debug_html", "aplicacoes_modelo_ano")
ANOS_CSV = os.path.join(DATA_DIR, "anos_modelo.csv")
TEST_ANOS_CSV = os.path.join(DATA_DIR, "anos_modelo_test.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "aplicacoes_modelo_ano.csv")
TEST_OUTPUT_CSV = os.path.join(DATA_DIR, "aplicacoes_modelo_ano_test.csv")
MAX_DEBUG_LINKS = 120
PAGE_PARAM_KEYS = ("pagina", "page", "pag", "pg")
CATALOG_SIGNATURE_KEYS = (
    "fabricante",
    "varnome",
    "modelo",
    "anoini",
    "anofim",
    "ano",
    "codmodelo",
    "codigo",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai aplicacoes por modelo/ano do Carros na Web com suporte a paginacao."
    )
    parser.add_argument(
        "--anos-csv",
        default=ANOS_CSV,
        help="Caminho do CSV de anos por modelo.",
    )
    parser.add_argument(
        "--use-test-csv",
        action="store_true",
        help="Usa o CSV curto de teste versionado no repo.",
    )
    parser.add_argument(
        "--output-csv",
        default=OUTPUT_CSV,
        help="Caminho do CSV final de aplicacoes por modelo/ano.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=30,
        help="Limite maximo de paginas por URL de ano.",
    )
    return parser.parse_args()


def resolve_anos_csv(csv_path):
    if os.path.exists(csv_path):
        return csv_path

    search_roots = [
        DATA_DIR,
        os.path.join(SCRIPT_DIR, "data"),
        SCRIPT_DIR,
    ]
    for root in search_roots:
        for current_root, _, files in os.walk(root):
            if "anos_modelo.csv" in files:
                candidate = os.path.join(current_root, "anos_modelo.csv")
                print(f"[LOAD] anos_modelo.csv encontrado automaticamente em: {candidate}")
                return candidate

    raise FileNotFoundError(
        "Nao foi encontrado anos_modelo.csv. "
        f"Caminho esperado: {csv_path}. "
        "Gere primeiro a camada de anos ou informe "
        "--anos-csv com o caminho correto."
    )


def resolve_input_output_paths(args):
    anos_csv = args.anos_csv
    output_csv = args.output_csv

    if args.use_test_csv:
        anos_csv = TEST_ANOS_CSV
        if args.output_csv == OUTPUT_CSV:
            output_csv = TEST_OUTPUT_CSV

    return anos_csv, output_csv


def safe_filename(text):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(text)).strip("_")


def normalize_text(text):
    value = str(text or "").strip().lower()
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return re.sub(r"\s+", " ", value)


def save_debug_html(html, fabricante, modelo, ano, page_number):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    file_name = (
        f"{safe_filename(fabricante)}__{safe_filename(modelo)}__{safe_filename(ano)}"
        f"__page_{page_number}.html"
    )
    path = os.path.join(DEBUG_DIR, file_name)

    with open(path, "w", encoding="utf-8", errors="ignore") as html_file:
        html_file.write(html)

    return path


def load_anos_csv(csv_path):
    csv_path = resolve_anos_csv(csv_path)
    df = pd.read_csv(csv_path)

    print(f"[LOAD] Linhas de anos carregadas: {len(df)}")
    print("[LOAD] Colunas:", list(df.columns))
    print(df.head())

    return df


def page_number_from_url(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    for key in PAGE_PARAM_KEYS:
        if key in params:
            match = re.search(r"\d+", str(params[key][0]))
            if match:
                return int(match.group(0))

    return 1


def catalog_signature(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    signature = {}

    for key in CATALOG_SIGNATURE_KEYS:
        if key in params and params[key]:
            signature[key] = params[key][0]

    return signature


def same_catalog_signature(candidate_url, seed_url):
    candidate_signature = catalog_signature(candidate_url)
    seed_signature = catalog_signature(seed_url)

    for key, seed_value in seed_signature.items():
        candidate_value = candidate_signature.get(key)
        if candidate_value is None:
            continue
        if str(candidate_value) != str(seed_value):
            return False

    return True


def inspect_page(html, fabricante, modelo, ano, url, page_number):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    all_links = soup.find_all("a", href=True)
    text = soup.get_text(" ", strip=True)

    relevant = []
    for a_tag in all_links:
        href = a_tag.get("href", "")
        label = a_tag.get_text(" ", strip=True)
        href_lower = href.lower()
        if (
            "fichadetalhe" in href_lower
            or "catalogo.asp" in href_lower
            or "catalogomodelo.asp" in href_lower
            or "proxim" in normalize_text(label)
            or label.strip() in {">", ">>"}
        ):
            relevant.append((href, label))

    print("\n[DEBUG PAGE]")
    print("Fabricante:", fabricante)
    print("Modelo:", modelo)
    print("Ano:", ano)
    print("Pagina logica:", page_number)
    print("URL:", url)
    print("Title:", title)
    print("HTML size:", len(html))
    print("Total links:", len(all_links))
    print("Contem 'Ocorreu um erro':", "Ocorreu um erro" in text)
    print("Links relevantes:", len(relevant))

    print("\n[DEBUG LINKS RELEVANTES - AMOSTRA]")
    for href, label in relevant[:MAX_DEBUG_LINKS]:
        print(f"href={href} | text={label}")

    debug_path = save_debug_html(html, fabricante, modelo, ano, page_number)
    print("[DEBUG HTML] salvo em:", debug_path)


def extract_application_links(html, fabricante, modelo, ano, url_ano_origem, current_url, page_number):
    soup = BeautifulSoup(html, "html.parser")
    applications = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        texto_link = a_tag.get_text(" ", strip=True)
        href_lower = href.lower()

        if "fichadetalhe.asp" not in href_lower:
            continue

        full_url = urljoin(BASE_URL, href.replace("\\", "/"))
        parsed = urlparse(full_url)
        params = parse_qs(parsed.query)
        codigo_ficha = params.get("codigo", [None])[0]

        if not codigo_ficha:
            continue

        versao = texto_link or params.get("varnome", [""])[0]

        applications.append(
            {
                "fabricante": fabricante,
                "modelo": modelo,
                "ano": ano,
                "pagina_lista": page_number,
                "url_ano_origem": url_ano_origem,
                "url_lista_atual": current_url,
                "codigo_ficha": codigo_ficha,
                "url_ficha": full_url,
                "versao": versao,
                "href_original": href,
                "texto_link": texto_link,
                "params": str(params),
            }
        )

    return applications


def extract_pagination_links(html, current_url, seed_url):
    soup = BeautifulSoup(html, "html.parser")
    current_page = page_number_from_url(current_url)
    pagination_candidates = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        label = a_tag.get_text(" ", strip=True)

        full_url = urljoin(BASE_URL, href.replace("\\", "/"))
        parsed = urlparse(full_url)
        href_lower = href.lower()
        label_normalized = normalize_text(label)

        if parsed.netloc and parsed.netloc != urlparse(BASE_URL).netloc:
            continue

        if "catalogo.asp" not in parsed.path.lower() and "catalogo.asp" not in href_lower:
            continue

        if not same_catalog_signature(full_url, seed_url):
            continue

        candidate_page = page_number_from_url(full_url)
        looks_like_pagination = (
            any(key in parse_qs(parsed.query) for key in PAGE_PARAM_KEYS)
            or "proxim" in label_normalized
            or label.strip() in {">", ">>"}
            or label_normalized.isdigit()
        )

        if not looks_like_pagination:
            continue

        if candidate_page < current_page:
            continue

        pagination_candidates.append((candidate_page, full_url, label))

    unique_candidates = []
    seen = set()
    for candidate_page, full_url, label in sorted(pagination_candidates, key=lambda item: (item[0], item[1])):
        if full_url in seen or full_url == current_url:
            continue
        seen.add(full_url)
        unique_candidates.append(
            {
                "candidate_page": candidate_page,
                "url": full_url,
                "label": label,
            }
        )

    return unique_candidates


def scrape_applications_for_year(session, row, max_pages):
    fabricante = row["fabricante"]
    modelo = row["modelo"]
    ano = row["ano"]
    seed_url = row["url_ano"]

    queue = deque([seed_url])
    visited = set()
    queued = {seed_url}
    page_counter = 0
    all_rows = []

    while queue and page_counter < max_pages:
        current_url = queue.popleft()
        queued.discard(current_url)

        if current_url in visited:
            continue

        visited.add(current_url)
        page_counter += 1

        print("\n" + "-" * 80)
        print(f"[PAGE {page_counter}] {fabricante} | {modelo} | {ano}")
        print("URL lista:", current_url)

        response = safe_get(session, current_url, timeout=30, delay_min=1.5, delay_max=3.0)
        inspect_page(
            html=response.text,
            fabricante=fabricante,
            modelo=modelo,
            ano=ano,
            url=current_url,
            page_number=page_counter,
        )

        current_rows = extract_application_links(
            html=response.text,
            fabricante=fabricante,
            modelo=modelo,
            ano=ano,
            url_ano_origem=seed_url,
            current_url=current_url,
            page_number=page_counter,
        )
        print(f"[RESULT] Aplicacoes encontradas na pagina: {len(current_rows)}")
        for item in current_rows[:20]:
            print(item)

        all_rows.extend(current_rows)

        next_candidates = extract_pagination_links(
            html=response.text,
            current_url=current_url,
            seed_url=seed_url,
        )
        print(f"[PAGINATION] Candidatas encontradas: {len(next_candidates)}")
        for candidate in next_candidates[:20]:
            print(candidate)

        for candidate in next_candidates:
            next_url = candidate["url"]
            if next_url in visited or next_url in queued:
                continue
            queue.append(next_url)
            queued.add(next_url)

    if queue:
        print(
            f"[WARN] Limite de paginacao atingido para {fabricante} | {modelo} | {ano}. "
            f"Paginas visitadas: {page_counter}."
        )

    return all_rows


def scrape_aplicacoes_modelo_ano(anos_df, session, max_pages):
    all_applications = []
    total = len(anos_df)

    for idx, row in anos_df.iterrows():
        print("\n" + "=" * 80)
        print(f"[{idx + 1}/{total}] {row['fabricante']} | {row['modelo']} | {row['ano']}")
        print("URL ano:", row["url_ano"])

        try:
            applications = scrape_applications_for_year(session=session, row=row, max_pages=max_pages)
            print(f"[RESULT] Aplicacoes totais no ano: {len(applications)}")
            all_applications.extend(applications)
        except Exception as exc:
            print(f"[ERROR] Erro em {row['fabricante']} | {row['modelo']} | {row['ano']}: {exc}")

    return pd.DataFrame(all_applications)


def clean_aplicacoes(df):
    if df.empty:
        print("[CLEAN] DataFrame vazio.")
        return df

    df = df.copy()
    before = len(df)
    df.drop_duplicates(
        subset=["fabricante", "modelo", "ano", "codigo_ficha", "url_ficha"],
        inplace=True,
    )
    df.sort_values(by=["fabricante", "modelo", "ano", "versao", "codigo_ficha"], inplace=True)
    after = len(df)

    print(f"[CLEAN] Antes: {before} | Depois: {after}")
    return df


def save_csv(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print("[SAVE] CSV salvo em:", output_path)


def main():
    args = parse_args()
    anos_csv, output_csv = resolve_input_output_paths(args)
    session = create_session()
    anos_df = load_anos_csv(anos_csv)
    aplicacoes_df = scrape_aplicacoes_modelo_ano(
        anos_df=anos_df,
        session=session,
        max_pages=args.max_pages,
    )
    aplicacoes_df = clean_aplicacoes(aplicacoes_df)
    save_csv(aplicacoes_df, output_csv)

    print("\nFINALIZADO")
    print("Total aplicacoes encontradas:", len(aplicacoes_df))
    if not aplicacoes_df.empty:
        print(aplicacoes_df.head(30))


if __name__ == "__main__":
    main()
