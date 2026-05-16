import argparse
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


EXPECTED_SEGMENTS = [
    {
        "code": "autos",
        "name": "Autos",
        "aliases": ["A) Autos", "Autos"],
    },
    {
        "code": "comerciais_leves",
        "name": "Comerciais Leves",
        "aliases": ["B) Com. Leves", "Com. Leves", "Comerciais Leves"],
    },
    {
        "code": "autos_comerciais_leves",
        "name": "Autos + Comerciais Leves",
        "aliases": ["A + B", "A+B"],
    },
    {
        "code": "caminhoes",
        "name": "Caminhoes",
        "aliases": ["C) Caminhoes", "C) Caminhões", "Caminhoes", "Caminhões"],
    },
    {
        "code": "onibus",
        "name": "Onibus",
        "aliases": ["D) Onibus", "D) Ônibus", "Onibus", "Ônibus"],
    },
    {
        "code": "caminhoes_onibus",
        "name": "Caminhoes + Onibus",
        "aliases": ["C + D", "C+D"],
    },
    {
        "code": "subtotal",
        "name": "Subtotal",
        "aliases": ["Subtotal"],
    },
    {
        "code": "motos",
        "name": "Motos",
        "aliases": ["E) Motos", "Motos"],
    },
    {
        "code": "implementos_rodoviarios",
        "name": "Implementos Rodoviarios",
        "aliases": ["F) Impl. Rod.", "Impl. Rod.", "Implementos Rodoviarios"],
    },
    {
        "code": "outros",
        "name": "Outros",
        "aliases": ["Outros"],
    },
    {
        "code": "total",
        "name": "Total",
        "aliases": ["Total"],
    },
]

RAW_FIELD_NAMES = [
    "current_month_raw",
    "previous_month_raw",
    "current_year_accumulated_raw",
    "previous_year_month_raw",
    "previous_year_accumulated_raw",
    "month_over_month_raw",
    "year_over_year_raw",
    "accumulated_year_over_year_raw",
]


def load_local_env():
    """
    Carrega variaveis do `.env` local sem sobrescrever o ambiente.

    Resultado esperado:
    - credenciais e configuracoes fixas, como SUPABASE_URL e bucket padrao,
      ficam disponiveis para a execucao manual do script.
    """
    env_path = Path(__file__).with_name(".env")

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def normalize_supabase_url(url):
    """
    Remove sufixos de API da URL do Supabase.

    Resultado esperado:
    - `https://project.supabase.co/rest/v1` vira `https://project.supabase.co`.
    """
    if not url:
        return url

    normalized = url.rstrip("/")

    if normalized.endswith("/rest/v1"):
        normalized = normalized[: -len("/rest/v1")]

    return normalized


def require_env(name):
    """
    Busca uma variavel obrigatoria no ambiente.

    Resultado esperado:
    - retorna o valor configurado ou interrompe a execucao com erro claro.
    """
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")

    return value


def strip_accents(value):
    """
    Remove acentos de uma string para comparacao robusta.

    Resultado esperado:
    - `Ônibus` vira `Onibus`, facilitando matching de segmentos.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_text(value):
    """
    Normaliza texto extraido do PDF.

    Resultado esperado:
    - quebras de linha e espacos duplicados viram uma string limpa.
    """
    value = "" if value is None else str(value)
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_key(value):
    """
    Cria uma chave textual simplificada para matching.

    Resultado esperado:
    - nomes com acento, pontuacao e caixa diferente passam a comparar igual.
    """
    value = strip_accents(normalize_text(value)).lower()
    value = re.sub(r"[^a-z0-9+]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def segment_lookup():
    """
    Monta a lista de aliases conhecidos dos segmentos Fenabrave.

    Resultado esperado:
    - retorna pares `(alias_normalizado, segmento)` ordenados do alias maior
      para o menor, evitando matches curtos antes dos especificos.
    """
    lookup = []

    for segment in EXPECTED_SEGMENTS:
        for alias in segment["aliases"]:
            lookup.append((normalize_key(alias), segment))

    lookup.sort(key=lambda item: len(item[0]), reverse=True)
    return lookup


SEGMENT_LOOKUP = segment_lookup()


def match_segment(row):
    """
    Identifica qual segmento Fenabrave uma linha extraida representa.

    Resultado esperado:
    - retorna o dicionario do segmento esperado ou `None` se a linha nao for
      uma linha de dado relevante.
    """
    row_text = normalize_text(" ".join(cell for cell in row if cell))
    row_key = normalize_key(row_text)
    first_cell_key = normalize_key(row[0] if row else "")

    for alias_key, segment in SEGMENT_LOOKUP:
        if first_cell_key == alias_key or first_cell_key.startswith(alias_key):
            return segment

    for alias_key, segment in SEGMENT_LOOKUP:
        if row_key.startswith(alias_key + " ") or row_key == alias_key:
            return segment

    return None


def extract_numbers_from_cells(cells):
    """
    Extrai numeros em formato brasileiro de celulas do PDF.

    Resultado esperado:
    - retorna strings como `187.313` e `-9,23` preservadas para raw.
    """
    numbers = []
    pattern = re.compile(r"-?\d{1,3}(?:\.\d{3})*(?:,\d+)?|-?\d+,\d+|-?\d+")

    for cell in cells:
        text = normalize_text(cell)

        if not text:
            continue

        numbers.extend(match.group(0) for match in pattern.finditer(text))

    return numbers


def parse_int_br(value):
    """
    Converte inteiro em formato brasileiro para `int`.

    Resultado esperado:
    - `187.313` vira `187313`.
    """
    if value is None:
        return None

    text = normalize_text(value)

    if not text or text in {"-", "--"}:
        return None

    text = text.replace(".", "").replace(" ", "")

    if "," in text:
        text = text.split(",", 1)[0]

    return int(text)


def parse_decimal_br(value):
    """
    Converte percentual/decimal brasileiro para `float`.

    Resultado esperado:
    - `-9,23` vira `-9.23`.
    """
    if value is None:
        return None

    text = normalize_text(value)

    if not text or text in {"-", "--"}:
        return None

    text = text.replace("%", "").replace(".", "").replace(",", ".")
    return float(text)


def build_headers(supabase_key):
    """
    Cria headers padrao para chamadas REST ao Supabase.

    Resultado esperado:
    - headers com `apikey`, `Authorization` e `Content-Type`.
    """
    return {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }


def rest_url(base_url, table):
    """
    Monta endpoint REST de uma tabela Supabase.

    Resultado esperado:
    - `base_url` + `/rest/v1/<table>`.
    """
    return f"{base_url}/rest/v1/{table}"


def storage_object_url(base_url, bucket, storage_path):
    """
    Monta endpoint de download de objeto privado no Supabase Storage.

    Resultado esperado:
    - URL correta mesmo quando `storage_path` possui barras ou caracteres
      que precisam de encoding.
    """
    safe_path = quote(storage_path, safe="/")
    return f"{base_url}/storage/v1/object/{bucket}/{safe_path}"


def request_json(method, url, headers, **kwargs):
    """
    Executa uma chamada HTTP ao Supabase e retorna JSON.

    Resultado esperado:
    - retorna JSON decodificado quando a chamada e bem-sucedida.
    - levanta erro com status/body quando a chamada falha.
    """
    response = requests.request(method, url, headers=headers, timeout=60, **kwargs)

    if not response.ok:
        raise RuntimeError(
            f"Supabase request falhou: {method} {url} "
            f"status={response.status_code} body={response.text[:500]}"
        )

    if not response.text:
        return None

    return response.json()


def download_pdf_from_storage(base_url, supabase_key, bucket, storage_path):
    """
    Baixa o PDF ja salvo no bucket privado do Supabase Storage.

    Resultado esperado:
    - retorna os bytes do PDF que serao enviados ao pdfplumber.
    """
    url = storage_object_url(base_url, bucket, storage_path)
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }
    response = requests.get(url, headers=headers, timeout=120)

    if not response.ok:
        raise RuntimeError(
            f"Falha ao baixar PDF do Storage: status={response.status_code} "
            f"body={response.text[:500]}"
        )

    return response.content


def find_source_id(base_url, headers, source_name):
    """
    Busca o ID da fonte em `public.market_data_sources`.

    Resultado esperado:
    - retorna o `id` da Fenabrave ou falha se a fonte ainda nao foi cadastrada.
    """
    params = {
        "select": "id,source_name",
        "source_name": f"eq.{source_name}",
        "limit": "1",
    }
    rows = request_json("GET", rest_url(base_url, "market_data_sources"), headers, params=params)

    if not rows:
        raise RuntimeError(
            f"Fonte '{source_name}' nao encontrada em public.market_data_sources."
        )

    return rows[0]["id"]


def get_or_create_source_file(
    base_url,
    headers,
    source_id,
    reference_period,
    source_url,
    storage_bucket,
    storage_path,
    file_bytes,
    write,
):
    """
    Localiza ou cria o registro do PDF em `market_source_files`.

    Resultado esperado:
    - em dry-run, retorna o ID se o registro ja existe ou `None`.
    - em modo write, cria o registro se ainda nao existir e retorna seu ID.
    """
    params = {
        "select": "id,extraction_status,storage_path",
        "source_id": f"eq.{source_id}",
        "reference_period": f"eq.{reference_period}",
        "source_url": f"eq.{source_url}",
        "limit": "1",
    }
    rows = request_json("GET", rest_url(base_url, "market_source_files"), headers, params=params)

    if rows:
        return rows[0]["id"]

    if not write:
        return None

    filename = storage_path.rstrip("/").split("/")[-1]
    payload = {
        "source_id": source_id,
        "reference_period": reference_period,
        "source_url": source_url,
        "file_type": "pdf",
        "storage_bucket": storage_bucket,
        "storage_path": storage_path,
        "original_filename": filename,
        "file_size_bytes": len(file_bytes),
        "sha256": hashlib.sha256(file_bytes).hexdigest(),
        "extraction_status": "stored",
        "extraction_method": "pdf_table_extraction",
        "extraction_notes": "Registro criado pelo script Fenabrave fase 1.",
    }
    write_headers = dict(headers)
    write_headers["Prefer"] = "return=representation"
    inserted = request_json(
        "POST",
        rest_url(base_url, "market_source_files"),
        write_headers,
        data=json.dumps(payload),
    )

    return inserted[0]["id"]


def extract_first_page_table(pdf_bytes):
    """
    Extrai a primeira tabela util da pagina 1 do PDF Fenabrave.

    Resultado esperado:
    - retorna linhas raw com segmento identificado e oito valores brutos:
      mes atual, mes anterior, acumulados e variacoes.
    """
    try:
        import pdfplumber
    except ImportError as error:
        raise RuntimeError(
            "Dependencia ausente: pdfplumber. Execute `pip install -r requirements.txt` "
            "em scripts/fenabrave_ingestion."
        ) from error

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        if not pdf.pages:
            raise RuntimeError("PDF sem paginas.")

        page = pdf.pages[0]
        tables = page.extract_tables()

    if not tables:
        raise RuntimeError("Nenhuma tabela encontrada na pagina 1 do PDF.")

    parsed_rows = []

    for table_number, table in enumerate(tables, start=1):
        for row_number, raw_row in enumerate(table, start=1):
            cells = [normalize_text(cell) for cell in raw_row]
            segment = match_segment(cells)

            if not segment:
                continue

            numbers = extract_numbers_from_cells(cells[1:])

            if len(numbers) < 8:
                numbers = extract_numbers_from_cells(cells)

            if len(numbers) < 8:
                continue

            values = numbers[:8]
            row = {
                "page_number": 1,
                "table_number": table_number,
                "row_number": row_number,
                "segment_label_raw": cells[0] or segment["name"],
                "segment_code": segment["code"],
                "segment_name": segment["name"],
            }
            row.update(dict(zip(RAW_FIELD_NAMES, values)))
            parsed_rows.append(row)

    by_code = {}

    for row in parsed_rows:
        by_code.setdefault(row["segment_code"], row)

    ordered_rows = []

    for segment in EXPECTED_SEGMENTS:
        row = by_code.get(segment["code"])

        if row:
            ordered_rows.append(row)

    if not ordered_rows:
        raise RuntimeError("Nenhuma linha esperada da Fenabrave foi extraida.")

    missing = [s["code"] for s in EXPECTED_SEGMENTS if s["code"] not in by_code]

    if missing:
        print(
            "Aviso: segmentos esperados nao extraidos: "
            + ", ".join(missing),
            file=sys.stderr,
        )

    return ordered_rows


def normalize_rows(raw_rows, source_file_id, reference_period):
    """
    Converte linhas raw em registros analiticos normalizados.

    Resultado esperado:
    - retorna payloads compativeis com `market_vehicle_registrations_segment`.
    """
    normalized = []

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "market_scope": "Brasil",
                "metric_name": "emplacamentos",
                "segment_code": row["segment_code"],
                "segment_name": row["segment_name"],
                "current_month_units": parse_int_br(row["current_month_raw"]),
                "previous_month_units": parse_int_br(row["previous_month_raw"]),
                "current_year_accumulated_units": parse_int_br(
                    row["current_year_accumulated_raw"]
                ),
                "previous_year_month_units": parse_int_br(row["previous_year_month_raw"]),
                "previous_year_accumulated_units": parse_int_br(
                    row["previous_year_accumulated_raw"]
                ),
                "month_over_month_pct": parse_decimal_br(row["month_over_month_raw"]),
                "year_over_year_pct": parse_decimal_br(row["year_over_year_raw"]),
                "accumulated_year_over_year_pct": parse_decimal_br(
                    row["accumulated_year_over_year_raw"]
                ),
            }
        )

    return normalized


def validate_normalized_rows(normalized_rows):
    """
    Valida somas estruturais da primeira tabela Fenabrave.

    Resultado esperado:
    - confirma `Autos + Com. Leves`, `Caminhoes + Onibus` e o total geral.
    """
    by_code = {row["segment_code"]: row for row in normalized_rows}

    def value(code):
        row = by_code.get(code)
        return None if row is None else row["current_month_units"]

    checks = []

    check_specs = [
        (
            "autos_plus_comerciais_leves",
            ["autos", "comerciais_leves"],
            "autos_comerciais_leves",
        ),
        (
            "caminhoes_plus_onibus",
            ["caminhoes", "onibus"],
            "caminhoes_onibus",
        ),
        (
            "subtotal_plus_outros",
            ["subtotal", "motos", "implementos_rodoviarios", "outros"],
            "total",
        ),
    ]

    for check_name, inputs, expected_code in check_specs:
        input_values = [value(code) for code in inputs]
        expected_value = value(expected_code)

        if any(item is None for item in input_values) or expected_value is None:
            calculated_value = None
            passed = False
            difference = None
        else:
            calculated_value = sum(input_values)
            difference = calculated_value - expected_value
            passed = difference == 0

        checks.append(
            {
                "check_name": check_name,
                "calculated_value": calculated_value,
                "expected_value": expected_value,
                "difference": difference,
                "passed": passed,
            }
        )

    return checks


def print_preview(raw_rows, normalized_rows, checks, pdf_bytes):
    """
    Imprime uma pre-visualizacao da extracao no terminal.

    Resultado esperado:
    - operador consegue revisar segmentos, valores normalizados e checks antes
      de gravar dados no Supabase.
    """
    print("")
    print("PDF")
    print(f"- bytes: {len(pdf_bytes)}")
    print(f"- sha256: {hashlib.sha256(pdf_bytes).hexdigest()}")
    print("")
    print("Linhas extraidas")
    print("-" * 96)
    print(
        f"{'segment_code':28} {'segmento':28} {'mes_atual':>10} "
        f"{'mes_ant':>10} {'acum_ano':>10}"
    )
    print("-" * 96)

    for row in normalized_rows:
        print(
            f"{row['segment_code'][:28]:28} "
            f"{row['segment_name'][:28]:28} "
            f"{row['current_month_units']:>10} "
            f"{row['previous_month_units']:>10} "
            f"{row['current_year_accumulated_units']:>10}"
        )

    print("")
    print("Validacoes locais")
    print("-" * 96)

    for check in checks:
        print(
            f"{check['check_name']:32} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']}"
        )

    print("")


def raw_payloads(raw_rows, source_file_id):
    """
    Prepara payloads para `raw_fenabrave_segment_summary`.

    Resultado esperado:
    - retorna linhas raw com valores preservados como texto e vinculadas ao
      `source_file_id`.
    """
    payloads = []

    for row in raw_rows:
        payloads.append(
            {
                "source_file_id": source_file_id,
                "page_number": row["page_number"],
                "table_number": row["table_number"],
                "row_number": row["row_number"],
                "segment_label_raw": row["segment_label_raw"],
                "current_month_raw": row["current_month_raw"],
                "previous_month_raw": row["previous_month_raw"],
                "current_year_accumulated_raw": row["current_year_accumulated_raw"],
                "previous_year_month_raw": row["previous_year_month_raw"],
                "previous_year_accumulated_raw": row["previous_year_accumulated_raw"],
                "month_over_month_raw": row["month_over_month_raw"],
                "year_over_year_raw": row["year_over_year_raw"],
                "accumulated_year_over_year_raw": row[
                    "accumulated_year_over_year_raw"
                ],
                "extraction_confidence": 0.95,
            }
        )

    return payloads


def delete_existing_rows(base_url, headers, source_file_id):
    """
    Remove cargas anteriores do mesmo arquivo de origem.

    Resultado esperado:
    - usado por `--replace` para reprocessar um PDF sem duplicar linhas.
    """
    for table in [
        "raw_fenabrave_segment_summary",
        "market_vehicle_registrations_segment",
        "market_ingestion_validation_results",
    ]:
        url = rest_url(base_url, table)
        params = {"source_file_id": f"eq.{source_file_id}"}
        response = requests.delete(url, headers=headers, params=params, timeout=60)

        if response.status_code not in {200, 204}:
            raise RuntimeError(
                f"Falha ao limpar {table}: status={response.status_code} "
                f"body={response.text[:500]}"
            )


def insert_rows(base_url, headers, table, rows):
    """
    Insere uma lista de registros em uma tabela Supabase.

    Resultado esperado:
    - grava payloads raw, normalizados ou de validacao; se a tabela nao existir
      ou houver conflito, retorna erro claro.
    """
    if not rows:
        return

    write_headers = dict(headers)
    write_headers["Prefer"] = "return=minimal"
    response = requests.post(
        rest_url(base_url, table),
        headers=write_headers,
        data=json.dumps(rows),
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"Falha ao inserir em {table}: status={response.status_code} "
            f"body={response.text[:500]}"
        )


def update_source_file_status(base_url, headers, source_file_id, status, notes):
    """
    Atualiza status operacional do arquivo processado.

    Resultado esperado:
    - marca o PDF como `validated` quando checks passam ou `failed` quando
      alguma validacao falha.
    """
    write_headers = dict(headers)
    write_headers["Prefer"] = "return=minimal"
    payload = {
        "extraction_status": status,
        "extraction_notes": notes,
    }
    response = requests.patch(
        rest_url(base_url, "market_source_files"),
        headers=write_headers,
        params={"id": f"eq.{source_file_id}"},
        data=json.dumps(payload),
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"Falha ao atualizar market_source_files: status={response.status_code} "
            f"body={response.text[:500]}"
        )


def validation_payloads(checks, source_file_id):
    """
    Converte checks locais em registros de validacao.

    Resultado esperado:
    - gera payloads para `market_ingestion_validation_results`.
    """
    payloads = []

    for check in checks:
        payloads.append(
            {
                "source_file_id": source_file_id,
                "check_name": check["check_name"],
                "calculated_value": check["calculated_value"],
                "expected_value": check["expected_value"],
                "difference": check["difference"],
                "passed": check["passed"],
                "severity": "error",
                "notes": None if check["passed"] else "Falha em validacao local.",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return payloads


def write_results(
    base_url,
    headers,
    source_file_id,
    raw_rows,
    normalized_rows,
    checks,
    replace,
):
    """
    Persiste raw, normalizado, validacoes e status no Supabase.

    Resultado esperado:
    - em `--write`, grava os resultados da extracao; com `--replace`, limpa
      cargas antigas do mesmo arquivo antes de inserir novamente.
    """
    if replace:
        delete_existing_rows(base_url, headers, source_file_id)

    insert_rows(
        base_url,
        headers,
        "raw_fenabrave_segment_summary",
        raw_payloads(raw_rows, source_file_id),
    )
    insert_rows(
        base_url,
        headers,
        "market_vehicle_registrations_segment",
        normalized_rows,
    )

    try:
        insert_rows(
            base_url,
            headers,
            "market_ingestion_validation_results",
            validation_payloads(checks, source_file_id),
        )
    except RuntimeError as error:
        print(
            "Aviso: nao foi possivel gravar market_ingestion_validation_results. "
            f"{error}",
            file=sys.stderr,
        )

    if all(check["passed"] for check in checks):
        update_source_file_status(
            base_url,
            headers,
            source_file_id,
            "validated",
            "Extracao Fenabrave fase 1 validada pelo script.",
        )
    else:
        update_source_file_status(
            base_url,
            headers,
            source_file_id,
            "failed",
            "Extracao Fenabrave fase 1 falhou em validacoes locais.",
        )


def save_temp_pdf(pdf_bytes):
    """
    Salva copia temporaria do PDF baixado para depuracao local.

    Resultado esperado:
    - cria `tmp/fenabrave_phase1_current.pdf` quando `--save-pdf` e usado.
    """
    tmp_dir = Path(__file__).parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    path = tmp_dir / "fenabrave_phase1_current.pdf"
    path.write_bytes(pdf_bytes)
    return path


def parse_args():
    """
    Define argumentos de linha de comando do script.

    Resultado esperado:
    - permite rodar em `--dry-run`, `--write` e `--replace`.
    - path, periodo e URL do PDF sao informados no comando mensal, sem editar
      `.env`.
    """
    parser = argparse.ArgumentParser(
        description="Extrai a primeira tabela da pagina 1 de PDF Fenabrave no Supabase Storage."
    )
    parser.add_argument("--dry-run", action="store_true", help="Extrai e valida sem gravar.")
    parser.add_argument("--write", action="store_true", help="Grava raw e normalizado no Supabase.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove cargas anteriores do mesmo source_file_id antes de gravar.",
    )
    parser.add_argument("--bucket", default=os.environ.get("FENABRAVE_STORAGE_BUCKET"))
    parser.add_argument(
        "--path",
        required=True,
        help="Caminho do PDF no bucket, ex: fenabrave/2026/04/2026_04_02.pdf.",
    )
    parser.add_argument(
        "--reference-period",
        required=True,
        help="Periodo de referencia no formato YYYY-MM-DD, usando o primeiro dia do mes.",
    )
    parser.add_argument(
        "--source-url",
        required=True,
        help="URL original do PDF no site da Fenabrave.",
    )
    parser.add_argument(
        "--source-name",
        default=os.environ.get("FENABRAVE_SOURCE_NAME", "Fenabrave"),
    )
    parser.add_argument(
        "--source-file-id",
        type=int,
        default=None,
        help="ID ja existente em public.market_source_files.",
    )
    parser.add_argument(
        "--save-pdf",
        action="store_true",
        help="Salva uma copia temporaria em scripts/fenabrave_ingestion/tmp.",
    )
    return parser.parse_args()


def main():
    """
    Orquestra a extracao Fenabrave fase 1.

    Resultado esperado:
    - baixa o PDF do Storage, extrai/normaliza/valida e, se solicitado com
      `--write`, grava os dados no Supabase.
    """
    load_local_env()
    args = parse_args()

    if not args.write:
        args.dry_run = True

    base_url = normalize_supabase_url(require_env("SUPABASE_URL"))
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get(
        "SUPABASE_KEY"
    )

    if not supabase_key:
        raise RuntimeError(
            "Defina SUPABASE_SERVICE_ROLE_KEY ou SUPABASE_KEY no ambiente."
        )

    bucket = args.bucket or require_env("FENABRAVE_STORAGE_BUCKET")
    storage_path = args.path
    reference_period = args.reference_period
    source_url = args.source_url
    headers = build_headers(supabase_key)

    print("Baixando PDF do Supabase Storage...")
    pdf_bytes = download_pdf_from_storage(base_url, supabase_key, bucket, storage_path)

    if args.save_pdf:
        saved_path = save_temp_pdf(pdf_bytes)
        print(f"PDF temporario salvo em: {saved_path}")

    print("Extraindo tabela da pagina 1...")
    raw_rows = extract_first_page_table(pdf_bytes)

    source_file_id = args.source_file_id

    if source_file_id is None:
        source_id = find_source_id(base_url, headers, args.source_name)
        source_file_id = get_or_create_source_file(
            base_url,
            headers,
            source_id,
            reference_period,
            source_url,
            bucket,
            storage_path,
            pdf_bytes,
            write=args.write,
        )

    if source_file_id is None:
        source_file_id_for_preview = -1
    else:
        source_file_id_for_preview = source_file_id

    normalized_rows = normalize_rows(raw_rows, source_file_id_for_preview, reference_period)
    checks = validate_normalized_rows(normalized_rows)

    print_preview(raw_rows, normalized_rows, checks, pdf_bytes)

    if args.dry_run:
        print("Dry-run concluido. Nenhum dado foi gravado.")
        return

    if source_file_id is None:
        raise RuntimeError(
            "source_file_id ausente. Informe --source-file-id ou permita criar o registro com --write."
        )

    print("Gravando resultados no Supabase...")
    write_results(
        base_url,
        headers,
        source_file_id,
        raw_rows,
        normalized_rows,
        checks,
        replace=args.replace,
    )
    print("Carga concluida.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        sys.exit(1)
