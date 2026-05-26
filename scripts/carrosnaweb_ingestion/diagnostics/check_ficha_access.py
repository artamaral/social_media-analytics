import argparse
import csv
import os
import sys
import time
from dataclasses import asdict, dataclass
from random import uniform
from typing import Iterable, List
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.carrosnaweb.com.br"
DEFAULT_REFERER = f"{BASE_URL}/avancada.asp"
DEFAULT_OUTPUT_CSV = "scripts/carrosnaweb_ingestion/data/debug_html/ficha_access_check.csv"
DEFAULT_OUTPUT_TABLE_CSV = "scripts/carrosnaweb_ingestion/data/debug_html/ficha_table_rows.csv"
DEFAULT_RAW_HTML_DIR = "scripts/carrosnaweb_ingestion/data/debug_html/raw_html"

# Small, fixed sample for manual diagnostics only.
DEFAULT_SAMPLE_CODES = [
    "44763",  # pilot ficha validated in docs
    "22547",  # sample extracted from ano page in docs
    "4801",   # direct ficha with 500 observed in docs
    "4789",   # HTML error page observed in docs
    "44764",  # nearby code that may trigger validation flow
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Referer": DEFAULT_REFERER,
    "Connection": "keep-alive",
}


@dataclass
class AccessResult:
    input_value: str
    codigo_ficha: str
    requested_url: str
    final_url: str
    http_status: int
    html_size: int
    status: str
    reason: str
    page_title: str
    checked_at: str


@dataclass
class TechnicalRow:
    codigo_ficha: str
    ficha_url: str
    page_title: str
    group_name: str
    field_name: str
    field_value: str
    image_urls: str
    source_row_text: str


def build_ficha_url(codigo: str) -> str:
    return f"{BASE_URL}/fichadetalhe.asp?codigo={codigo}"


def extract_codigo_from_value(value: str) -> str:
    if value.isdigit():
        return value

    parsed = urlparse(value)
    codigo = parse_qs(parsed.query).get("codigo", [""])[0]
    return codigo


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def warm_up_session(session: requests.Session) -> None:
    for path in ("/default.asp", "/avancada.asp"):
        url = f"{BASE_URL}{path}"
        response = session.get(url, timeout=20)
        print(
            f"[SESSION] warm-up {path} "
            f"status={response.status_code} size={len(response.text)}"
        )
        time.sleep(uniform(1.0, 2.0))


def iter_targets(args: argparse.Namespace) -> Iterable[str]:
    if args.urls:
        return args.urls

    if args.codes:
        return args.codes

    return DEFAULT_SAMPLE_CODES


def resolve_target(value: str):
    codigo = extract_codigo_from_value(value)
    if value.startswith("http://") or value.startswith("https://"):
        return value, codigo

    return build_ficha_url(value), codigo


def classify_response(response: requests.Response):
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    title = " ".join(soup.title.get_text(" ", strip=True).split()) if soup.title else ""
    final_url = response.url.lower()
    html_lower = html.lower()
    page_text = soup.get_text(" ", strip=True).lower()

    if response.status_code != 200:
        return "http_error", f"http_status_{response.status_code}", title

    if "fichadetalhevalida.asp" in final_url:
        return "validation_required", "redirected_to_fichadetalhevalida", title

    validation_terms = [
        "preencha o campo com os caracteres",
        "captcha",
        "valida",
        "validacao",
    ]
    if any(term in html_lower or term in page_text for term in validation_terms):
        return "validation_required", "captcha_or_validation_detected", title

    error_terms = [
        "ocorreu um erro",
        "internal server error",
        "500 - internal server error",
    ]
    if any(term in html_lower or term in page_text for term in error_terms):
        return "site_error", "site_error_page", title

    if "ficha t" not in page_text:
        return "unexpected_page", "missing_ficha_tecnica_text", title

    return "success", "", title


def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.replace("\xa0", " ").split()).strip()


def extract_image_urls(cell) -> List[str]:
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


def looks_like_group_header(values: List[str]) -> bool:
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


def parse_ficha_tables(html: str, ficha_url: str, codigo_ficha: str, page_title: str) -> List[TechnicalRow]:
    soup = BeautifulSoup(html, "html.parser")
    rows: List[TechnicalRow] = []
    current_group = "GERAL"
    seen = set()

    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue

        cell_texts = [clean_text(cell.get_text(" ", strip=True)) for cell in cells]
        non_empty = [text for text in cell_texts if text]
        row_text = " | ".join(non_empty)

        if not non_empty:
            continue

        if looks_like_group_header(non_empty):
            current_group = non_empty[0]
            continue

        pair_indexes = range(0, len(cells) - 1, 2)
        for index in pair_indexes:
            field_cell = cells[index]
            value_cell = cells[index + 1]

            field_name = clean_text(field_cell.get_text(" ", strip=True))
            field_value = clean_text(value_cell.get_text(" ", strip=True))

            if not field_name or not field_value:
                continue

            # Ignore obvious navigation or sharing UI rows.
            if field_name.lower() in {"compartilhe", "busca detalhada", "avalie"}:
                continue

            image_urls = extract_image_urls(value_cell)
            unique_key = (current_group, field_name, field_value)
            if unique_key in seen:
                continue
            seen.add(unique_key)

            rows.append(
                TechnicalRow(
                    codigo_ficha=codigo_ficha,
                    ficha_url=ficha_url,
                    page_title=page_title,
                    group_name=current_group,
                    field_name=field_name,
                    field_value=field_value,
                    image_urls=" | ".join(image_urls),
                    source_row_text=row_text,
                )
            )

    return rows


def save_raw_html(codigo_ficha: str, html: str, raw_html_dir: str) -> str:
    os.makedirs(raw_html_dir, exist_ok=True)
    file_path = os.path.join(raw_html_dir, f"{codigo_ficha or 'sem_codigo'}.html")
    with open(file_path, "w", encoding="utf-8", errors="ignore") as html_file:
        html_file.write(html)
    return file_path


def save_table_rows(rows: List[TechnicalRow], output_csv: str) -> None:
    if not output_csv or not rows:
        return

    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fieldnames = list(asdict(rows[0]).keys())
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    print(f"[OUTPUT] table_csv={output_csv}")


def run_check(
    session: requests.Session,
    target: str,
    timeout: int,
    delay_min: float,
    delay_max: float,
):
    requested_url, codigo = resolve_target(target)

    print(f"[CHECK] target={target}")
    print(f"[CHECK] url={requested_url}")

    checked_at = time.strftime("%Y-%m-%d %H:%M:%S")

    response_html = ""

    try:
        response = session.get(requested_url, timeout=timeout)
        response_html = response.text
        status, reason, title = classify_response(response)

        result = AccessResult(
            input_value=target,
            codigo_ficha=codigo,
            requested_url=requested_url,
            final_url=response.url,
            http_status=response.status_code,
            html_size=len(response.text),
            status=status,
            reason=reason,
            page_title=title,
            checked_at=checked_at,
        )
    except requests.RequestException as exc:
        result = AccessResult(
            input_value=target,
            codigo_ficha=codigo,
            requested_url=requested_url,
            final_url="",
            http_status=0,
            html_size=0,
            status="exception",
            reason=str(exc),
            page_title="",
            checked_at=checked_at,
        )

    print(
        "[RESULT] "
        f"http_status={result.http_status} "
        f"status={result.status} "
        f"reason={result.reason or '-'} "
        f"final_url={result.final_url or '-'} "
        f"html_size={result.html_size}"
    )

    time.sleep(uniform(delay_min, delay_max))
    return result, response_html


def save_results(results: List[AccessResult], output_csv: str) -> None:
    if not output_csv:
        return

    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fieldnames = list(asdict(results[0]).keys()) if results else list(AccessResult.__annotations__.keys())
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            writer.writerow(asdict(item))

    print(f"[OUTPUT] csv={output_csv}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnostica acesso a poucas fichas do Carros na Web sem extrair dados "
            "nem tentar contornar validacao/captcha."
        )
    )
    parser.add_argument(
        "--codes",
        nargs="+",
        help="Lista de codigos de ficha, por exemplo: --codes 44763 22547",
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="Lista de URLs completas de ficha.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout de cada request em segundos.",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=2.0,
        help="Delay minimo apos cada request.",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=5.0,
        help="Delay maximo apos cada request.",
    )
    parser.add_argument(
        "--output-csv",
        default=DEFAULT_OUTPUT_CSV,
        help="CSV de saida com o resumo do diagnostico.",
    )
    parser.add_argument(
        "--stop-on-validation",
        action="store_true",
        help="Interrompe ao detectar validation_required.",
    )
    parser.add_argument(
        "--extract-table",
        action="store_true",
        help="Extrai as linhas tecnicas da ficha quando o acesso retornar success.",
    )
    parser.add_argument(
        "--output-table-csv",
        default=DEFAULT_OUTPUT_TABLE_CSV,
        help="CSV de saida para as linhas extraidas da tabela tecnica.",
    )
    parser.add_argument(
        "--raw-html-dir",
        default=DEFAULT_RAW_HTML_DIR,
        help="Pasta para salvar HTML bruto das fichas com success.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print(sys.executable)
    print(sys.version)

    targets = list(iter_targets(args))
    if not targets:
        print("[ERROR] Nenhum alvo informado.")
        return 1

    session = create_session()
    warm_up_session(session)

    results: List[AccessResult] = []
    extracted_rows: List[TechnicalRow] = []
    for target in targets:
        result, response_html = run_check(
            session=session,
            target=target,
            timeout=args.timeout,
            delay_min=args.delay_min,
            delay_max=args.delay_max,
        )
        results.append(result)

        if args.extract_table and result.status == "success" and response_html:
            raw_html_path = save_raw_html(
                codigo_ficha=result.codigo_ficha,
                html=response_html,
                raw_html_dir=args.raw_html_dir,
            )
            parsed_rows = parse_ficha_tables(
                html=response_html,
                ficha_url=result.final_url or result.requested_url,
                codigo_ficha=result.codigo_ficha,
                page_title=result.page_title,
            )
            print(
                f"[PARSE] codigo={result.codigo_ficha or '-'} "
                f"rows={len(parsed_rows)} raw_html={raw_html_path}"
            )
            extracted_rows.extend(parsed_rows)

        if args.stop_on_validation and result.status == "validation_required":
            print("[STOP] validation_required detectado; encerrando.")
            break

    save_results(results, args.output_csv)
    if args.extract_table:
        save_table_rows(extracted_rows, args.output_table_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
