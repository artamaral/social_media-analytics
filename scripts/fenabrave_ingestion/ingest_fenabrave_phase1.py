import argparse
import hashlib
import io
import json
import os
import re
import subprocess
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
]

FENABRAVE_ITEM1_CODE = "fenabrave_item_01_ranking_emplacamentos_mes"
FENABRAVE_ITEM1_LABEL = "Ranking dos emplacamentos mes"
FENABRAVE_ITEM1_PAGE = 6
FENABRAVE_ITEM1_PERIOD_TYPE = "monthly"
FENABRAVE_ITEM1_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM1_SALES_CHANNEL = "all"
FENABRAVE_ITEM1_EXPECTED_RANKS = 50
FENABRAVE_ITEM1_CATEGORIES = ["automoveis", "comerciais_leves"]

FENABRAVE_ITEM2_CODE = "fenabrave_item_02_ranking_emplacamentos_acumulado"
FENABRAVE_ITEM2_LABEL = "Ranking dos emplacamentos acumulado"
FENABRAVE_ITEM2_PAGE = 7
FENABRAVE_ITEM2_PERIOD_TYPE = "accumulated"
FENABRAVE_ITEM2_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM2_SALES_CHANNEL = "all"

FENABRAVE_ITEM3_CODE = "fenabrave_item_03_ranking_por_marca_mes"
FENABRAVE_ITEM3_LABEL = "Ranking por marca mes"
FENABRAVE_ITEM3_PAGE = 8
FENABRAVE_ITEM3_PERIOD_TYPE = "monthly"
FENABRAVE_ITEM3_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM3_SALES_CHANNEL = "all"
FENABRAVE_ITEM3_EXPECTED_RANKS = 21

FENABRAVE_ITEM4_CODE = "fenabrave_item_04_ranking_por_marca_acumulado"
FENABRAVE_ITEM4_LABEL = "Ranking por marca acumulado"
FENABRAVE_ITEM4_PAGE = 9
FENABRAVE_ITEM4_PERIOD_TYPE = "accumulated"
FENABRAVE_ITEM4_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM4_SALES_CHANNEL = "all"

FENABRAVE_ITEM5_CODE = "fenabrave_item_05_emplacamentos_por_subsegmento"
FENABRAVE_ITEM5_LABEL = "Emplacamentos por sub segmento"
FENABRAVE_ITEM5_PAGE = 17
FENABRAVE_ITEM5_PERIOD_TYPE = "mixed"
FENABRAVE_ITEM5_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM5_SALES_CHANNEL = "all"
FENABRAVE_ITEM5_EXPECTED_ROWS = 13

FENABRAVE_ITEM6_CODE = "fenabrave_item_06_mercado_eletrificados_mes"
FENABRAVE_ITEM6_LABEL = "Mercado de eletrificados mes"
FENABRAVE_ITEM6_PAGE = 20
FENABRAVE_ITEM6_PERIOD_TYPE = "monthly"
FENABRAVE_ITEM6_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM6_SALES_CHANNEL = "all"

FENABRAVE_ITEM7_CODE = "fenabrave_item_07_total_marca_hibrido_mes"
FENABRAVE_ITEM7_LABEL = "Total por marca hibrido mes"
FENABRAVE_ITEM7_PAGE = 20
FENABRAVE_ITEM7_PERIOD_TYPE = "monthly"
FENABRAVE_ITEM7_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM7_SALES_CHANNEL = "all"

FENABRAVE_ITEM8_CODE = "fenabrave_item_08_total_marca_eletrico_mes"
FENABRAVE_ITEM8_LABEL = "Total por marca eletrico mes"
FENABRAVE_ITEM8_PAGE = 20
FENABRAVE_ITEM8_PERIOD_TYPE = "monthly"
FENABRAVE_ITEM8_MARKET_SCOPE = "Brasil"
FENABRAVE_ITEM8_SALES_CHANNEL = "all"

FENABRAVE_ELECTRIFIED_PAGE_MAP = {
    20: "automoveis",
    21: "comerciais_leves",
}
FENABRAVE_ELECTRIFIED_MARKET_LABELS = {
    "a hibridos": "hybrid",
    "b eletricos": "electric",
    "tot eletrificados": "total_electrified",
}

FENABRAVE_MODEL_RANKING_ITEMS = {
    FENABRAVE_ITEM1_CODE: {
        "code": FENABRAVE_ITEM1_CODE,
        "label": FENABRAVE_ITEM1_LABEL,
        "page": FENABRAVE_ITEM1_PAGE,
        "published_period_type": FENABRAVE_ITEM1_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM1_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM1_SALES_CHANNEL,
    },
    FENABRAVE_ITEM2_CODE: {
        "code": FENABRAVE_ITEM2_CODE,
        "label": FENABRAVE_ITEM2_LABEL,
        "page": FENABRAVE_ITEM2_PAGE,
        "published_period_type": FENABRAVE_ITEM2_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM2_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM2_SALES_CHANNEL,
    },
}

FENABRAVE_BRAND_RANKING_ITEMS = {
    FENABRAVE_ITEM3_CODE: {
        "code": FENABRAVE_ITEM3_CODE,
        "label": FENABRAVE_ITEM3_LABEL,
        "page": FENABRAVE_ITEM3_PAGE,
        "published_period_type": FENABRAVE_ITEM3_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM3_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM3_SALES_CHANNEL,
    },
    FENABRAVE_ITEM4_CODE: {
        "code": FENABRAVE_ITEM4_CODE,
        "label": FENABRAVE_ITEM4_LABEL,
        "page": FENABRAVE_ITEM4_PAGE,
        "published_period_type": FENABRAVE_ITEM4_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM4_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM4_SALES_CHANNEL,
    },
}

FENABRAVE_SUBSEGMENT_ITEMS = {
    FENABRAVE_ITEM5_CODE: {
        "code": FENABRAVE_ITEM5_CODE,
        "label": FENABRAVE_ITEM5_LABEL,
        "page": FENABRAVE_ITEM5_PAGE,
        "published_period_type": FENABRAVE_ITEM5_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM5_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM5_SALES_CHANNEL,
    },
}

FENABRAVE_ELECTRIFIED_ITEMS = {
    FENABRAVE_ITEM6_CODE: {
        "code": FENABRAVE_ITEM6_CODE,
        "label": FENABRAVE_ITEM6_LABEL,
        "page": FENABRAVE_ITEM6_PAGE,
        "published_period_type": FENABRAVE_ITEM6_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM6_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM6_SALES_CHANNEL,
    },
    FENABRAVE_ITEM7_CODE: {
        "code": FENABRAVE_ITEM7_CODE,
        "label": FENABRAVE_ITEM7_LABEL,
        "page": FENABRAVE_ITEM7_PAGE,
        "published_period_type": FENABRAVE_ITEM7_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM7_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM7_SALES_CHANNEL,
    },
    FENABRAVE_ITEM8_CODE: {
        "code": FENABRAVE_ITEM8_CODE,
        "label": FENABRAVE_ITEM8_LABEL,
        "page": FENABRAVE_ITEM8_PAGE,
        "published_period_type": FENABRAVE_ITEM8_PERIOD_TYPE,
        "market_scope": FENABRAVE_ITEM8_MARKET_SCOPE,
        "sales_channel": FENABRAVE_ITEM8_SALES_CHANNEL,
    },
}

FENABRAVE_ITEM_DEFINITIONS = {}
FENABRAVE_ITEM_DEFINITIONS.update(FENABRAVE_MODEL_RANKING_ITEMS)
FENABRAVE_ITEM_DEFINITIONS.update(FENABRAVE_BRAND_RANKING_ITEMS)
FENABRAVE_ITEM_DEFINITIONS.update(FENABRAVE_SUBSEGMENT_ITEMS)
FENABRAVE_ITEM_DEFINITIONS.update(FENABRAVE_ELECTRIFIED_ITEMS)


def infer_reference_period_from_path(storage_path):
    """
    Infere o periodo de referencia a partir do nome/caminho do PDF.

    Resultado esperado:
    - `fenabrave/2026/04/2026_04_02.pdf` vira `2026-04-01`.
    - usa os dois primeiros grupos numericos do nome do arquivo como ano/mes.
    """
    filename = Path(storage_path).name
    match = re.search(r"(20\d{2})[_-](\d{2})", filename)

    if not match:
        match = re.search(r"(20\d{2})[^\d]+(\d{2})", storage_path)

    if not match:
        raise RuntimeError(
            "Nao foi possivel inferir o periodo pelo nome do arquivo. "
            "Use um nome como 2026_04_02.pdf ou informe --reference-period."
        )

    year = int(match.group(1))
    month = int(match.group(2))

    if month < 1 or month > 12:
        raise RuntimeError(f"Mes invalido inferido do arquivo: {month}")

    return f"{year:04d}-{month:02d}-01"


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


def select_current_month_raw(numbers):
    """
    Seleciona a coluna `mes_atual` entre os numeros extraidos da linha.

    Resultado esperado:
    - ignora percentuais como `-9,23`, que podem aparecer antes dos volumes
      por causa da ordem extraida pelo PDF.
    - retorna o primeiro volume inteiro nao negativo, como `187.313`.
    """
    for value in numbers:
        text = normalize_text(value)

        if "," in text or text.startswith("-"):
            continue

        return text

    return None


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


def normalize_subsegment_name(value):
    """
    Normaliza subsegmentos removendo prefixos tecnicos do PDF.

    Resultado esperado:
    - `AU - SUVs` vira `SUVs`.
    """
    text = normalize_text(value)
    text = re.sub(r"^AU\s*-\s*", "", text, flags=re.IGNORECASE)
    return normalize_text(text)


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
    - retorna linhas raw com segmento identificado e, para a carga analitica,
      usa apenas o primeiro valor numerico da linha: `mes_atual`.
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
            current_month_raw = select_current_month_raw(numbers)

            if current_month_raw is None:
                numbers = extract_numbers_from_cells(cells)
                current_month_raw = select_current_month_raw(numbers)

                if current_month_raw is None:
                    continue

            values = [current_month_raw]
            row = {
                "page_number": 1,
                "table_number": table_number,
                "row_number": row_number,
                "segment_label_raw": cells[0] or segment["name"],
                "segment_code": segment["code"],
                "segment_name": segment["name"],
            }

            for field_name, value in zip(RAW_FIELD_NAMES, values):
                row[field_name] = value

            for field_name in RAW_FIELD_NAMES:
                row.setdefault(field_name, None)

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


def split_fenabrave_ranked_entries(line):
    """
    Separa entradas de ranking em uma linha da pagina 6.

    Resultado esperado:
    - `1o VW/T CROSS 11.753 1o FIAT/STRADA 14.303` vira duas entradas.
    - o ultimo numero de cada entrada e tratado como volume mensal, preservando
      numeros que fazem parte do modelo, como `DAILY 30-130`.
    """
    text = normalize_text(line)
    matches = list(re.finditer(r"(\d+)(?:\u00ba|o)\s+", text, flags=re.IGNORECASE))
    entries = []

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = normalize_text(text[start:end])

        if not body:
            continue

        value_match = re.search(r"(\d{1,3}(?:\.\d{3})*|\d+)\s*$", body)

        if not value_match:
            continue

        model_label_raw = normalize_text(body[: value_match.start()])
        monthly_units_raw = value_match.group(1)

        if not model_label_raw:
            continue

        brand_name_raw = None
        model_name_raw = None

        if "/" in model_label_raw:
            brand_name_raw, model_name_raw = [
                normalize_text(part) or None
                for part in model_label_raw.split("/", 1)
            ]

        entries.append(
            {
                "rank_position": int(match.group(1)),
                "model_label_raw": model_label_raw,
                "brand_name_raw": brand_name_raw,
                "model_name_raw": model_name_raw,
                "monthly_units_raw": monthly_units_raw,
                "monthly_units": parse_int_br(monthly_units_raw),
                "raw_entry": body,
            }
        )

    return entries


def split_fenabrave_brand_ranked_entries(line):
    """
    Separa entradas de ranking por marca em uma linha da pagina 8.

    Resultado esperado:
    - `1o VW 42.425 19,93% 1o FIAT 21.848 45,93%` vira duas entradas.
    - captura rank, marca, unidades e participacao em cada coluna.
    """
    text = normalize_text(line)
    matches = list(re.finditer(r"(\d+)(?:\u00ba|o)\s+", text, flags=re.IGNORECASE))
    entries = []

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = normalize_text(text[start:end])

        if not body:
            continue

        value_match = re.search(
            r"(.+?)\s+(\d{1,3}(?:\.\d{3})*|\d+)\s+(\d{1,3},\d+)%\s*$",
            body,
        )

        if not value_match:
            continue

        brand_name_raw = normalize_text(value_match.group(1))
        units_raw = value_match.group(2)
        share_raw = value_match.group(3)

        if not brand_name_raw:
            continue

        entries.append(
            {
                "rank_position": int(match.group(1)),
                "brand_name_raw": brand_name_raw,
                "units_raw": units_raw,
                "units": parse_int_br(units_raw),
                "market_share_pct_raw": share_raw,
                "market_share_pct": parse_decimal_br(share_raw),
                "raw_entry": body,
            }
        )

    return entries


def split_fenabrave_subsegment_share_entry(line):
    """
    Extrai uma linha da pagina 17 com shares por subsegmento.

    Resultado esperado:
    - `AU - SUVs 59,08% 57,70% 57,95% 53,35%` vira um dicionario com
      subsegmento, mes corrente, mes anterior e acumulados n/n-1.
    """
    text = normalize_text(line)
    match = re.search(
        r"(.+?)\s+"
        r"(\d{1,3},\d+)%\s+"
        r"(\d{1,3},\d+)%\s+"
        r"(?:=\s+)?(\d{1,3},\d+)%\s+"
        r"(\d{1,3},\d+)%\s*(?:=\s*)?$",
        text,
    )

    if not match:
        return None

    raw_label = normalize_text(match.group(1))
    subsegment_name = normalize_subsegment_name(raw_label)

    if not subsegment_name:
        return None

    return {
        "raw_label": raw_label,
        "subsegment_name": subsegment_name,
        "current_month_share_pct_raw": match.group(2),
        "current_month_share_pct": parse_decimal_br(match.group(2)),
        "previous_month_share_pct_raw": match.group(3),
        "previous_month_share_pct": parse_decimal_br(match.group(3)),
        "prior_year_accum_share_pct_raw": match.group(4),
        "prior_year_accum_share_pct": parse_decimal_br(match.group(4)),
        "current_year_accum_share_pct_raw": match.group(5),
        "current_year_accum_share_pct": parse_decimal_br(match.group(5)),
    }


def split_fenabrave_electrified_market_entry(line):
    """
    Extrai uma linha de mercado de eletrificados das paginas 20 e 21.

    Resultado esperado:
    - `A) Hibridos 32.563 ...` vira uma linha com o volume mensal e o tipo de
      propulsao correspondente.
    - somente a primeira coluna mensal entra no escopo inicial.
    """
    text = normalize_text(line)
    line_key = normalize_key(text)

    if line_key.startswith("a hibridos"):
        raw_label = "A) Hibridos"
        powertrain_type = "hybrid"
    elif line_key.startswith("b eletricos"):
        raw_label = "B) Eletricos"
        powertrain_type = "electric"
    elif line_key.startswith("tot eletrificados"):
        raw_label = "Tot.Eletrificados"
        powertrain_type = "total_electrified"
    else:
        return None

    numbers = re.findall(r"\d{1,3}(?:\.\d{3})*|\d+", text)

    if not numbers:
        return None

    units_raw = normalize_text(numbers[0])
    monthly_units = parse_int_br(units_raw)

    if monthly_units is None:
        return None

    return {
        "raw_label": raw_label,
        "powertrain_type": powertrain_type,
        "monthly_units_raw": units_raw,
        "monthly_units": monthly_units,
    }


def extract_electrified_pages(pdf_bytes):
    """
    Extrai os blocos mensais de eletrificados das paginas 20 e 21.

    Resultado esperado:
    - item 6: mercado mensal por categoria veicular e propulsao.
    - item 7: ranking mensal por marca de hibridos.
    - item 8: ranking mensal por marca de eletricos.
    """
    try:
        import pdfplumber
    except ImportError as error:
        raise RuntimeError(
            "Dependencia ausente: pdfplumber. Execute `pip install -r requirements.txt` "
            "em scripts/fenabrave_ingestion."
        ) from error

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_number in FENABRAVE_ELECTRIFIED_PAGE_MAP:
            if len(pdf.pages) < page_number:
                raise RuntimeError(
                    f"PDF sem pagina {page_number} para os itens 6, 7 e 8 da Fenabrave."
                )

        page_text_map = {
            page_number: pdf.pages[page_number - 1].extract_text(
                x_tolerance=1,
                y_tolerance=3,
            )
            or ""
            for page_number in FENABRAVE_ELECTRIFIED_PAGE_MAP
        }

    market_rows = []
    hybrid_brand_rows = []
    electric_brand_rows = []

    for page_number, vehicle_category in FENABRAVE_ELECTRIFIED_PAGE_MAP.items():
        text = page_text_map[page_number]
        monthly_brand_section = False
        market_row_number = 0
        brand_row_number = 0

        for raw_line in text.splitlines():
            line = normalize_text(raw_line)
            line_key = normalize_key(line)

            if not line:
                continue
            if (
                line_key.startswith("ed ")
                or line_key == "informativo emplacamentos"
                or line_key.startswith("sao paulo ")
                or line_key == "mercado de eletrificados autos"
                or line_key == "mercado de eletrificados comerciais leves"
                or line_key == "variacao"
                or line_key == "a b a d c e"
                or line_key.startswith("www fenabrave org br")
            ):
                continue

            market_entry = split_fenabrave_electrified_market_entry(line)
            if market_entry:
                market_row_number += 1
                market_rows.append(
                    {
                        "page_number": page_number,
                        "row_number": market_row_number,
                        "vehicle_category": vehicle_category,
                        **market_entry,
                    }
                )
                continue

            if line_key == "hibridos mes eletricos mes":
                monthly_brand_section = True
                continue

            if line_key == "hibridos acumulado eletricos acumulado":
                break

            if not monthly_brand_section:
                continue

            entries = split_fenabrave_brand_ranked_entries(line)

            if not entries:
                continue

            brand_row_number += 1

            if len(entries) >= 1:
                hybrid_brand_rows.append(
                    {
                        "page_number": page_number,
                        "row_number": brand_row_number,
                        "vehicle_category": vehicle_category,
                        "powertrain_type": "hybrid",
                        **entries[0],
                    }
                )

            if len(entries) >= 2:
                electric_brand_rows.append(
                    {
                        "page_number": page_number,
                        "row_number": brand_row_number,
                        "vehicle_category": vehicle_category,
                        "powertrain_type": "electric",
                        **entries[1],
                    }
                )

    return market_rows, hybrid_brand_rows, electric_brand_rows


def extract_model_rankings_from_page(pdf_bytes, item_definition):
    """
    Extrai ranking Fenabrave de uma pagina com layout em duas colunas.

    Resultado esperado:
    - retorna ate 100 linhas: 50 automoveis e 50 comerciais leves.
    - pagina de origem varia conforme o item de extracao.
    """
    try:
        import pdfplumber
    except ImportError as error:
        raise RuntimeError(
            "Dependencia ausente: pdfplumber. Execute `pip install -r requirements.txt` "
            "em scripts/fenabrave_ingestion."
        ) from error

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_number = item_definition["page"]

        if len(pdf.pages) < page_number:
            raise RuntimeError(
                f"PDF sem pagina {page_number} para {item_definition['code']}."
            )

        page = pdf.pages[page_number - 1]
        text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""

    rows = []
    row_number = 0

    for line in text.splitlines():
        entries = split_fenabrave_ranked_entries(line)

        if not entries:
            continue

        row_number += 1

        for entry_index, entry in enumerate(entries[:2]):
            vehicle_category = (
                "automoveis" if entry_index == 0 else "comerciais_leves"
            )
            rows.append(
                {
                    "page_number": page_number,
                    "row_number": row_number,
                    "entry_index": entry_index + 1,
                    "vehicle_category": vehicle_category,
                    **entry,
                }
            )

    return rows


def extract_item1_model_rankings(pdf_bytes):
    """
    Extrai o item 1 da fase 2: ranking mensal da pagina 6.
    """
    return extract_model_rankings_from_page(
        pdf_bytes,
        FENABRAVE_MODEL_RANKING_ITEMS[FENABRAVE_ITEM1_CODE],
    )


def extract_item2_model_rankings(pdf_bytes):
    """
    Extrai o item 2 da fase 2: ranking acumulado da pagina 7.
    """
    return extract_model_rankings_from_page(
        pdf_bytes,
        FENABRAVE_MODEL_RANKING_ITEMS[FENABRAVE_ITEM2_CODE],
    )


def extract_brand_rankings_from_page(pdf_bytes, item_definition):
    """
    Extrai ranking por marca Fenabrave em layout de duas colunas.
    """
    try:
        import pdfplumber
    except ImportError as error:
        raise RuntimeError(
            "Dependencia ausente: pdfplumber. Execute `pip install -r requirements.txt` "
            "em scripts/fenabrave_ingestion."
        ) from error

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_number = item_definition["page"]

        if len(pdf.pages) < page_number:
            raise RuntimeError(
                f"PDF sem pagina {page_number} para {item_definition['code']}."
            )

        page = pdf.pages[page_number - 1]
        text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""

    rows = []
    row_number = 0

    for raw_line in text.splitlines():
        line = normalize_text(raw_line)
        line_key = normalize_key(line)

        if not line:
            continue
        if "automoveis + comerciais leves" in line_key:
            break
        if (
            line_key.startswith("ed ")
            or line_key == "informativo emplacamentos"
            or line_key.startswith("sao paulo ")
            or line_key.startswith("ranking por marca ")
            or line_key == "automoveis comerciais leves"
            or line_key == "fabricante quant part fabricante quant part"
            or line_key.startswith("www fenabrave org br")
        ):
            continue

        entries = split_fenabrave_brand_ranked_entries(line)

        if not entries:
            continue

        row_number += 1

        for entry_index, entry in enumerate(entries[:2]):
            vehicle_category = (
                "automoveis" if entry_index == 0 else "comerciais_leves"
            )
            rows.append(
                {
                    "page_number": page_number,
                    "row_number": row_number,
                    "entry_index": entry_index + 1,
                    "vehicle_category": vehicle_category,
                    **entry,
                }
            )

    return rows


def extract_item3_brand_rankings(pdf_bytes):
    """
    Extrai o item 3 da fase 2: ranking por marca mensal da pagina 8.
    """
    return extract_brand_rankings_from_page(
        pdf_bytes,
        FENABRAVE_BRAND_RANKING_ITEMS[FENABRAVE_ITEM3_CODE],
    )


def extract_item4_brand_rankings(pdf_bytes):
    """
    Extrai o item 4 da fase 2: ranking por marca acumulado da pagina 9.
    """
    return extract_brand_rankings_from_page(
        pdf_bytes,
        FENABRAVE_BRAND_RANKING_ITEMS[FENABRAVE_ITEM4_CODE],
    )


def extract_item5_subsegment_shares(pdf_bytes):
    """
    Extrai o item 5 da fase 2: shares por subsegmento da pagina 17.
    """
    try:
        import pdfplumber
    except ImportError as error:
        raise RuntimeError(
            "Dependencia ausente: pdfplumber. Execute `pip install -r requirements.txt` "
            "em scripts/fenabrave_ingestion."
        ) from error

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        if len(pdf.pages) < FENABRAVE_ITEM5_PAGE:
            raise RuntimeError(
                f"PDF sem pagina {FENABRAVE_ITEM5_PAGE} para {FENABRAVE_ITEM5_CODE}."
            )

        page = pdf.pages[FENABRAVE_ITEM5_PAGE - 1]
        text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""

    rows = []

    for raw_line in text.splitlines():
        line = normalize_text(raw_line)
        line_key = normalize_key(line)

        if not line:
            continue
        if (
            line_key.startswith("ed ")
            or line_key == "informativo emplacamentos"
            or line_key.startswith("sao paulo ")
            or line_key.startswith("modelos mais emplacados ")
            or line_key.startswith("www fenabrave org br")
        ):
            continue

        entry = split_fenabrave_subsegment_share_entry(line)

        if not entry:
            continue

        rows.append(
            {
                "page_number": FENABRAVE_ITEM5_PAGE,
                "row_number": len(rows) + 1,
                "vehicle_category": "automoveis",
                **entry,
            }
        )

    return rows


def extract_item6_electrified_market(pdf_bytes):
    """
    Extrai o item 6 da fase 2: mercado mensal de eletrificados das paginas 20 e 21.
    """
    market_rows, _, _ = extract_electrified_pages(pdf_bytes)
    return market_rows


def extract_item7_electrified_hybrid_brands(pdf_bytes):
    """
    Extrai o item 7 da fase 2: marcas mensais de hibridos das paginas 20 e 21.
    """
    _, hybrid_brand_rows, _ = extract_electrified_pages(pdf_bytes)
    return hybrid_brand_rows


def extract_item8_electrified_electric_brands(pdf_bytes):
    """
    Extrai o item 8 da fase 2: marcas mensais de eletricos das paginas 20 e 21.
    """
    _, _, electric_brand_rows = extract_electrified_pages(pdf_bytes)
    return electric_brand_rows


def normalize_model_ranking_rows(raw_rows, source_file_id, reference_period, item_code):
    """
    Normaliza linhas de ranking Fenabrave para `market_vehicle_model_rankings`.

    Resultado esperado:
    - payloads prontos para gravacao e reprocessamento por item.
    """
    item_definition = FENABRAVE_ITEM_DEFINITIONS[item_code]
    normalized = []

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "item_code": item_definition["code"],
                "published_period_type": item_definition["published_period_type"],
                "market_scope": item_definition["market_scope"],
                "vehicle_category": row["vehicle_category"],
                "sales_channel": item_definition["sales_channel"],
                "rank_position": row["rank_position"],
                "brand_name_raw": row.get("brand_name_raw"),
                "model_name_raw": row.get("model_name_raw"),
                "model_label_raw": row["model_label_raw"],
                "monthly_units": row["monthly_units"],
                "market_share_pct": None,
            }
        )

    return normalized


def normalize_item1_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 1 para `market_vehicle_model_rankings`.
    """
    return normalize_model_ranking_rows(
        raw_rows,
        source_file_id,
        reference_period,
        FENABRAVE_ITEM1_CODE,
    )


def normalize_item2_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 2 para `market_vehicle_model_rankings`.
    """
    return normalize_model_ranking_rows(
        raw_rows,
        source_file_id,
        reference_period,
        FENABRAVE_ITEM2_CODE,
    )


def normalize_item3_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 3 para `market_vehicle_brand_rankings`.
    """
    normalized = []
    item_definition = FENABRAVE_BRAND_RANKING_ITEMS[FENABRAVE_ITEM3_CODE]

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "item_code": item_definition["code"],
                "published_period_type": item_definition["published_period_type"],
                "market_scope": item_definition["market_scope"],
                "vehicle_category": row["vehicle_category"],
                "sales_channel": item_definition["sales_channel"],
                "rank_position": row["rank_position"],
                "brand_name_raw": row["brand_name_raw"],
                "units": row["units"],
                "market_share_pct": row["market_share_pct"],
                "raw_label": row["brand_name_raw"],
            }
        )

    return normalized


def normalize_item4_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 4 para `market_vehicle_brand_rankings`.
    """
    normalized = []
    item_definition = FENABRAVE_BRAND_RANKING_ITEMS[FENABRAVE_ITEM4_CODE]

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "item_code": item_definition["code"],
                "published_period_type": item_definition["published_period_type"],
                "market_scope": item_definition["market_scope"],
                "vehicle_category": row["vehicle_category"],
                "sales_channel": item_definition["sales_channel"],
                "rank_position": row["rank_position"],
                "brand_name_raw": row["brand_name_raw"],
                "units": row["units"],
                "market_share_pct": row["market_share_pct"],
                "raw_label": row["brand_name_raw"],
            }
        )

    return normalized


def normalize_item5_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 5 para `market_vehicle_subsegment_shares`.
    """
    normalized = []
    item_definition = FENABRAVE_SUBSEGMENT_ITEMS[FENABRAVE_ITEM5_CODE]

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "item_code": item_definition["code"],
                "published_period_type": item_definition["published_period_type"],
                "market_scope": item_definition["market_scope"],
                "vehicle_category": row["vehicle_category"],
                "sales_channel": item_definition["sales_channel"],
                "subsegment_name": row["subsegment_name"],
                "current_month_share_pct": row["current_month_share_pct"],
                "current_year_accum_share_pct": row["current_year_accum_share_pct"],
                "prior_year_accum_share_pct": row["prior_year_accum_share_pct"],
                "raw_label": row["raw_label"],
            }
        )

    return normalized


def normalize_item6_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 6 para `market_vehicle_electrified_registrations`.
    """
    normalized = []
    item_definition = FENABRAVE_ELECTRIFIED_ITEMS[FENABRAVE_ITEM6_CODE]

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "item_code": item_definition["code"],
                "published_period_type": item_definition["published_period_type"],
                "market_scope": item_definition["market_scope"],
                "aggregation_level": "market",
                "powertrain_type": row["powertrain_type"],
                "vehicle_category": row["vehicle_category"],
                "rank_position": None,
                "brand_name_raw": None,
                "model_name_raw": None,
                "units": row["monthly_units"],
                "market_share_pct": None,
                "raw_label": row["raw_label"],
            }
        )

    return normalized


def normalize_item7_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 7 para `market_vehicle_electrified_registrations`.
    """
    normalized = []
    item_definition = FENABRAVE_ELECTRIFIED_ITEMS[FENABRAVE_ITEM7_CODE]

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "item_code": item_definition["code"],
                "published_period_type": item_definition["published_period_type"],
                "market_scope": item_definition["market_scope"],
                "aggregation_level": "brand",
                "powertrain_type": "hybrid",
                "vehicle_category": row["vehicle_category"],
                "rank_position": row["rank_position"],
                "brand_name_raw": row["brand_name_raw"],
                "model_name_raw": None,
                "units": row["units"],
                "market_share_pct": row["market_share_pct"],
                "raw_label": row["brand_name_raw"],
            }
        )

    return normalized


def normalize_item8_rows(raw_rows, source_file_id, reference_period):
    """
    Normaliza linhas do item 8 para `market_vehicle_electrified_registrations`.
    """
    normalized = []
    item_definition = FENABRAVE_ELECTRIFIED_ITEMS[FENABRAVE_ITEM8_CODE]

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "item_code": item_definition["code"],
                "published_period_type": item_definition["published_period_type"],
                "market_scope": item_definition["market_scope"],
                "aggregation_level": "brand",
                "powertrain_type": "electric",
                "vehicle_category": row["vehicle_category"],
                "rank_position": row["rank_position"],
                "brand_name_raw": row["brand_name_raw"],
                "model_name_raw": None,
                "units": row["units"],
                "market_share_pct": row["market_share_pct"],
                "raw_label": row["brand_name_raw"],
            }
        )

    return normalized


def normalize_rows(raw_rows, source_file_id, reference_period):
    """
    Converte linhas raw em registros analiticos normalizados.

    Resultado esperado:
    - retorna payloads compativeis com `market_vehicle_registrations_segment`,
      contendo os campos da extracao: `segment_code`, `segmento` e `mes_atual`.
    """
    normalized = []

    for row in raw_rows:
        normalized.append(
            {
                "source_file_id": source_file_id,
                "reference_period": reference_period,
                "segment_code": row["segment_code"],
                "segmento": row["segment_name"],
                "mes_atual": parse_int_br(row["current_month_raw"]),
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
        return None if row is None else row["mes_atual"]

    checks = []

    check_specs = [
        {
            "check_name": "autos_plus_comerciais_leves",
            "inputs": ["autos", "comerciais_leves"],
            "expected_code": "autos_comerciais_leves",
            "missing_expected_severity": "error",
        },
        {
            "check_name": "caminhoes_plus_onibus",
            "inputs": ["caminhoes", "onibus"],
            "expected_code": "caminhoes_onibus",
            "missing_expected_severity": "error",
        },
        {
            "check_name": "subtotal_plus_outros",
            "inputs": ["subtotal", "motos", "implementos_rodoviarios", "outros"],
            "expected_code": "total",
            "missing_expected_severity": "warning",
        },
    ]

    for check_spec in check_specs:
        check_name = check_spec["check_name"]
        inputs = check_spec["inputs"]
        expected_code = check_spec["expected_code"]
        input_values = [value(code) for code in inputs]
        expected_value = value(expected_code)
        severity = "error"
        notes = None

        if any(item is None for item in input_values):
            calculated_value = None
            passed = False
            difference = None
        elif expected_value is None:
            calculated_value = sum(input_values)
            passed = False
            difference = None
            severity = check_spec["missing_expected_severity"]
            notes = (
                f"Linha esperada `{expected_code}` nao extraida; "
                "soma calculada mantida para revisao."
            )
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
                "severity": severity,
                "notes": notes if notes else None if passed else "Falha em validacao local.",
            }
        )

    return checks


def validate_model_ranking_rows(
    ranking_rows,
    *,
    segment_rows=None,
    compare_rows=None,
    expected_period_type="monthly",
):
    """
    Valida ranking Fenabrave por modelo.

    Resultado esperado:
    - 50 posicoes por categoria, ranks sem duplicidade, volumes positivos e
      checks adicionais conforme o tipo publicado.
    """
    rows_by_category = {
        category: [
            row for row in ranking_rows if row.get("vehicle_category") == category
        ]
        for category in FENABRAVE_ITEM1_CATEGORIES
    }
    checks = []

    for category, rows in rows_by_category.items():
        ranks = [row.get("rank_position") for row in rows]
        units = [row.get("monthly_units") for row in rows]
        labels = [row.get("model_label_raw") for row in rows]
        brands = [row.get("brand_name_raw") for row in rows]
        models = [row.get("model_name_raw") for row in rows]

        row_count = len(rows)
        distinct_ranks = len(set(ranks))
        expected_ranks = set(range(1, FENABRAVE_ITEM1_EXPECTED_RANKS + 1))
        found_ranks = set(rank for rank in ranks if rank is not None)
        missing_ranks = sorted(expected_ranks - found_ranks)
        invalid_units = sum(1 for value in units if value is None or value <= 0)
        missing_labels = sum(1 for value in labels if not normalize_text(value))
        split_count = sum(
            1
            for brand, model in zip(brands, models)
            if normalize_text(brand) and normalize_text(model)
        )
        split_ratio = split_count / row_count if row_count else 0
        sorted_rows = sorted(rows, key=lambda row: row.get("rank_position") or 999)
        order_violations = sum(
            1
            for previous, current in zip(sorted_rows, sorted_rows[1:])
            if (previous.get("monthly_units") or 0) < (current.get("monthly_units") or 0)
        )

        checks.extend(
            [
                {
                    "check_name": f"{category}_row_count",
                    "calculated_value": row_count,
                    "expected_value": FENABRAVE_ITEM1_EXPECTED_RANKS,
                    "difference": row_count - FENABRAVE_ITEM1_EXPECTED_RANKS,
                    "passed": row_count == FENABRAVE_ITEM1_EXPECTED_RANKS,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_distinct_ranks",
                    "calculated_value": distinct_ranks,
                    "expected_value": FENABRAVE_ITEM1_EXPECTED_RANKS,
                    "difference": distinct_ranks - FENABRAVE_ITEM1_EXPECTED_RANKS,
                    "passed": distinct_ranks == FENABRAVE_ITEM1_EXPECTED_RANKS
                    and not missing_ranks,
                    "severity": "error",
                    "notes": (
                        "Ranks ausentes: " + ", ".join(str(rank) for rank in missing_ranks)
                        if missing_ranks
                        else None
                    ),
                },
                {
                    "check_name": f"{category}_positive_units",
                    "calculated_value": invalid_units,
                    "expected_value": 0,
                    "difference": invalid_units,
                    "passed": invalid_units == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_model_labels",
                    "calculated_value": missing_labels,
                    "expected_value": 0,
                    "difference": missing_labels,
                    "passed": missing_labels == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_brand_model_split",
                    "calculated_value": round(split_ratio * 100, 2),
                    "expected_value": 95,
                    "difference": round((split_ratio * 100) - 95, 2),
                    "passed": split_ratio >= 0.95,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_descending_units",
                    "calculated_value": order_violations,
                    "expected_value": 0,
                    "difference": order_violations,
                    "passed": order_violations == 0,
                    "severity": "error",
                    "notes": None,
                },
            ]
        )

    if segment_rows:
        segment_totals = {
            "automoveis": next(
                (
                    row["mes_atual"]
                    for row in segment_rows
                    if row.get("segment_code") == "autos"
                ),
                None,
            ),
            "comerciais_leves": next(
                (
                    row["mes_atual"]
                    for row in segment_rows
                    if row.get("segment_code") == "comerciais_leves"
                ),
                None,
            ),
        }

        for category, rows in rows_by_category.items():
            top_50_total = sum(row.get("monthly_units") or 0 for row in rows)
            segment_total = segment_totals.get(category)
            passed = segment_total is None or top_50_total <= segment_total
            checks.append(
                {
                    "check_name": f"{category}_top50_lte_segment_total",
                    "calculated_value": top_50_total,
                    "expected_value": segment_total,
                    "difference": None
                    if segment_total is None
                    else top_50_total - segment_total,
                    "passed": passed,
                    "severity": "warning" if segment_total is None else "error",
                    "notes": (
                        "Total do segmento indisponivel para comparacao."
                        if segment_total is None
                        else None
                    ),
                }
            )

    if compare_rows:
        compare_totals = {
            category: sum(
                row.get("monthly_units") or 0
                for row in compare_rows
                if row.get("vehicle_category") == category
            )
            for category in FENABRAVE_ITEM1_CATEGORIES
        }

        for category, rows in rows_by_category.items():
            ranking_total = sum(row.get("monthly_units") or 0 for row in rows)
            compare_total = compare_totals.get(category)
            notes = None
            passed = True

            if compare_total is not None:
                passed = ranking_total >= compare_total
                if (
                    passed
                    and expected_period_type == "accumulated"
                    and normalize_text(rows[0].get("reference_period") if rows else "").endswith("-01-01")
                ):
                    notes = "Janeiro deve ser revisado visualmente se acumulado divergir do mensal."

            checks.append(
                {
                    "check_name": f"{category}_ranking_total_gte_compare_total",
                    "calculated_value": ranking_total,
                    "expected_value": compare_total,
                    "difference": None
                    if compare_total is None
                    else ranking_total - compare_total,
                    "passed": passed,
                    "severity": "warning" if compare_total is None else "error",
                    "notes": (
                        "Ranking de comparacao indisponivel."
                        if compare_total is None
                        else notes
                    ),
                }
            )

    return checks


def validate_item1_rows(item1_rows, segment_rows=None):
    """
    Valida o ranking mensal de modelos da pagina 6.
    """
    return validate_model_ranking_rows(
        item1_rows,
        segment_rows=segment_rows,
        expected_period_type="monthly",
    )


def validate_item2_rows(item2_rows, item1_rows=None):
    """
    Valida o ranking acumulado de modelos da pagina 7.
    """
    return validate_model_ranking_rows(
        item2_rows,
        compare_rows=item1_rows,
        expected_period_type="accumulated",
    )


def validate_item3_rows(item3_rows):
    """
    Valida o ranking por marca mensal da pagina 8.
    """
    rows_by_category = {
        category: [
            row for row in item3_rows if row.get("vehicle_category") == category
        ]
        for category in FENABRAVE_ITEM1_CATEGORIES
    }
    checks = []

    for category, rows in rows_by_category.items():
        ranks = [row.get("rank_position") for row in rows]
        units = [row.get("units") for row in rows]
        brands = [row.get("brand_name_raw") for row in rows]
        shares = [row.get("market_share_pct") for row in rows]
        row_count = len(rows)
        distinct_ranks = len(set(ranks))
        expected_ranks = set(range(1, row_count + 1))
        found_ranks = set(rank for rank in ranks if rank is not None)
        missing_ranks = sorted(expected_ranks - found_ranks)
        invalid_units = sum(1 for value in units if value is None or value <= 0)
        missing_brands = sum(1 for value in brands if not normalize_text(value))
        invalid_shares = sum(
            1 for value in shares if value is None or value < 0 or value > 100
        )
        sorted_rows = sorted(rows, key=lambda row: row.get("rank_position") or 999)
        order_violations = sum(
            1
            for previous, current in zip(sorted_rows, sorted_rows[1:])
            if (previous.get("units") or 0) < (current.get("units") or 0)
        )
        share_total = round(sum(value or 0 for value in shares), 4)

        checks.extend(
            [
                {
                    "check_name": f"{category}_row_count",
                    "calculated_value": row_count,
                    "expected_value": FENABRAVE_ITEM3_EXPECTED_RANKS,
                    "difference": row_count - FENABRAVE_ITEM3_EXPECTED_RANKS,
                    "passed": row_count == FENABRAVE_ITEM3_EXPECTED_RANKS,
                    "severity": "warning",
                    "notes": "Quantidade de marcas publicadas pode mudar se o layout da Fenabrave mudar.",
                },
                {
                    "check_name": f"{category}_distinct_ranks",
                    "calculated_value": distinct_ranks,
                    "expected_value": row_count,
                    "difference": distinct_ranks - row_count,
                    "passed": distinct_ranks == row_count and not missing_ranks,
                    "severity": "error",
                    "notes": (
                        "Ranks ausentes: " + ", ".join(str(rank) for rank in missing_ranks)
                        if missing_ranks
                        else None
                    ),
                },
                {
                    "check_name": f"{category}_positive_units",
                    "calculated_value": invalid_units,
                    "expected_value": 0,
                    "difference": invalid_units,
                    "passed": invalid_units == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_brand_names",
                    "calculated_value": missing_brands,
                    "expected_value": 0,
                    "difference": missing_brands,
                    "passed": missing_brands == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_share_range",
                    "calculated_value": invalid_shares,
                    "expected_value": 0,
                    "difference": invalid_shares,
                    "passed": invalid_shares == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_descending_units",
                    "calculated_value": order_violations,
                    "expected_value": 0,
                    "difference": order_violations,
                    "passed": order_violations == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_share_total_lte_100",
                    "calculated_value": share_total,
                    "expected_value": 100,
                    "difference": round(share_total - 100, 4),
                    "passed": share_total <= 100.5,
                    "severity": "warning",
                    "notes": "Top N por marca pode nao somar 100% se houver marcas fora do ranking publicado.",
                },
            ]
        )

    return checks


def validate_item4_rows(item4_rows, item3_rows=None):
    """
    Valida o ranking por marca acumulado da pagina 9.
    """
    checks = validate_item3_rows(item4_rows)

    if item3_rows:
        compare_totals = {
            category: sum(
                row.get("units") or 0
                for row in item3_rows
                if row.get("vehicle_category") == category
            )
            for category in FENABRAVE_ITEM1_CATEGORIES
        }

        for category in FENABRAVE_ITEM1_CATEGORIES:
            ranking_total = sum(
                row.get("units") or 0
                for row in item4_rows
                if row.get("vehicle_category") == category
            )
            compare_total = compare_totals.get(category)
            notes = None

            if compare_total is None:
                passed = True
            else:
                passed = ranking_total >= compare_total
                if passed and any(
                    normalize_text(row.get("reference_period", "")).endswith("-01-01")
                    for row in item4_rows
                    if row.get("vehicle_category") == category
                ):
                    notes = (
                        "Janeiro deve ser revisado visualmente se o acumulado "
                        "divergir do mensal."
                    )

            checks.append(
                {
                    "check_name": f"{category}_ranking_total_gte_compare_total",
                    "calculated_value": ranking_total,
                    "expected_value": compare_total,
                    "difference": None
                    if compare_total is None
                    else ranking_total - compare_total,
                    "passed": passed,
                    "severity": "warning" if compare_total is None else "error",
                    "notes": (
                        "Ranking de comparacao indisponivel."
                        if compare_total is None
                        else notes
                    ),
                }
            )

    return checks


def validate_item5_rows(item5_rows, item5_raw_rows=None):
    """
    Valida shares por subsegmento da pagina 17.
    """
    raw_rows = item5_raw_rows or []
    subsegments = [row.get("subsegment_name") for row in item5_rows]
    row_count = len(item5_rows)
    distinct_count = len(
        {
            normalize_key(value)
            for value in subsegments
            if normalize_text(value)
        }
    )
    missing_names = sum(1 for value in subsegments if not normalize_text(value))

    current_month_invalid = sum(
        1
        for row in item5_rows
        if row.get("current_month_share_pct") is None
        or row.get("current_month_share_pct") < 0
        or row.get("current_month_share_pct") > 100
    )
    current_year_invalid = sum(
        1
        for row in item5_rows
        if row.get("current_year_accum_share_pct") is None
        or row.get("current_year_accum_share_pct") < 0
        or row.get("current_year_accum_share_pct") > 100
    )
    prior_year_invalid = sum(
        1
        for row in item5_rows
        if row.get("prior_year_accum_share_pct") is None
        or row.get("prior_year_accum_share_pct") < 0
        or row.get("prior_year_accum_share_pct") > 100
    )

    previous_month_invalid = sum(
        1
        for row in raw_rows
        if row.get("previous_month_share_pct") is None
        or row.get("previous_month_share_pct") < 0
        or row.get("previous_month_share_pct") > 100
    )

    current_month_total = round(
        sum(row.get("current_month_share_pct") or 0 for row in item5_rows), 4
    )
    previous_month_total = round(
        sum(row.get("previous_month_share_pct") or 0 for row in raw_rows), 4
    )
    current_year_total = round(
        sum(row.get("current_year_accum_share_pct") or 0 for row in item5_rows), 4
    )
    prior_year_total = round(
        sum(row.get("prior_year_accum_share_pct") or 0 for row in item5_rows), 4
    )

    return [
        {
            "check_name": "subsegment_row_count",
            "calculated_value": row_count,
            "expected_value": FENABRAVE_ITEM5_EXPECTED_ROWS,
            "difference": row_count - FENABRAVE_ITEM5_EXPECTED_ROWS,
            "passed": row_count == FENABRAVE_ITEM5_EXPECTED_ROWS,
            "severity": "warning",
            "notes": "Quantidade de subsegmentos pode variar se a Fenabrave alterar a composicao publicada.",
        },
        {
            "check_name": "subsegment_distinct_names",
            "calculated_value": distinct_count,
            "expected_value": row_count,
            "difference": distinct_count - row_count,
            "passed": distinct_count == row_count and missing_names == 0,
            "severity": "error",
            "notes": None,
        },
        {
            "check_name": "subsegment_current_month_share_range",
            "calculated_value": current_month_invalid,
            "expected_value": 0,
            "difference": current_month_invalid,
            "passed": current_month_invalid == 0,
            "severity": "error",
            "notes": None,
        },
        {
            "check_name": "subsegment_previous_month_share_range",
            "calculated_value": previous_month_invalid,
            "expected_value": 0,
            "difference": previous_month_invalid,
            "passed": previous_month_invalid == 0,
            "severity": "error",
            "notes": "Coluna lida apenas para auditoria local; nao entra na persistencia inicial.",
        },
        {
            "check_name": "subsegment_current_year_share_range",
            "calculated_value": current_year_invalid,
            "expected_value": 0,
            "difference": current_year_invalid,
            "passed": current_year_invalid == 0,
            "severity": "error",
            "notes": None,
        },
        {
            "check_name": "subsegment_prior_year_share_range",
            "calculated_value": prior_year_invalid,
            "expected_value": 0,
            "difference": prior_year_invalid,
            "passed": prior_year_invalid == 0,
            "severity": "error",
            "notes": None,
        },
        {
            "check_name": "subsegment_current_month_total_close_100",
            "calculated_value": current_month_total,
            "expected_value": 100,
            "difference": round(current_month_total - 100, 4),
            "passed": 99 <= current_month_total <= 101,
            "severity": "warning",
            "notes": "Tabela publicada em percentuais pode variar ligeiramente por arredondamento.",
        },
        {
            "check_name": "subsegment_previous_month_total_close_100",
            "calculated_value": previous_month_total,
            "expected_value": 100,
            "difference": round(previous_month_total - 100, 4),
            "passed": 99 <= previous_month_total <= 101,
            "severity": "warning",
            "notes": "Coluna lida apenas para auditoria local.",
        },
        {
            "check_name": "subsegment_current_year_total_close_100",
            "calculated_value": current_year_total,
            "expected_value": 100,
            "difference": round(current_year_total - 100, 4),
            "passed": 99 <= current_year_total <= 101,
            "severity": "warning",
            "notes": None,
        },
        {
            "check_name": "subsegment_prior_year_total_close_100",
            "calculated_value": prior_year_total,
            "expected_value": 100,
            "difference": round(prior_year_total - 100, 4),
            "passed": 99 <= prior_year_total <= 101,
            "severity": "warning",
            "notes": "Campo precisa permanecer separado do acumulado corrente para suportar n-1.",
        },
    ]


def validate_item6_rows(item6_rows):
    """
    Valida mercado mensal de eletrificados das paginas 20 e 21.
    """
    checks = []

    for category in FENABRAVE_ELECTRIFIED_PAGE_MAP.values():
        rows = [row for row in item6_rows if row.get("vehicle_category") == category]
        row_count = len(rows)
        powertrains = {row.get("powertrain_type") for row in rows}
        invalid_units = sum(1 for row in rows if (row.get("units") or 0) <= 0)
        values = {row.get("powertrain_type"): row.get("units") for row in rows}
        hybrid_units = values.get("hybrid")
        electric_units = values.get("electric")
        total_units = values.get("total_electrified")
        total_match = (
            hybrid_units is not None
            and electric_units is not None
            and total_units is not None
            and (hybrid_units + electric_units) == total_units
        )

        checks.extend(
            [
                {
                    "check_name": f"{category}_market_row_count",
                    "calculated_value": row_count,
                    "expected_value": 3,
                    "difference": row_count - 3,
                    "passed": row_count == 3,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_market_powertrain_labels",
                    "calculated_value": len(powertrains),
                    "expected_value": 3,
                    "difference": len(powertrains) - 3,
                    "passed": powertrains == {"hybrid", "electric", "total_electrified"},
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_market_positive_units",
                    "calculated_value": invalid_units,
                    "expected_value": 0,
                    "difference": invalid_units,
                    "passed": invalid_units == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_market_total_match",
                    "calculated_value": None
                    if hybrid_units is None or electric_units is None
                    else hybrid_units + electric_units,
                    "expected_value": total_units,
                    "difference": None
                    if hybrid_units is None or electric_units is None or total_units is None
                    else (hybrid_units + electric_units) - total_units,
                    "passed": total_match,
                    "severity": "warning",
                    "notes": "O total consolidado deve bater com hibridos + eletricos no bloco mensal.",
                },
            ]
        )

    return checks


def validate_item7_rows(item7_rows, item6_rows=None):
    """
    Valida ranking mensal por marca de hibridos das paginas 20 e 21.
    """
    return validate_electrified_brand_rows(
        item7_rows,
        item6_rows=item6_rows,
        powertrain_type="hybrid",
    )


def validate_item8_rows(item8_rows, item6_rows=None):
    """
    Valida ranking mensal por marca de eletricos das paginas 20 e 21.
    """
    return validate_electrified_brand_rows(
        item8_rows,
        item6_rows=item6_rows,
        powertrain_type="electric",
    )


def validate_electrified_brand_rows(item_rows, item6_rows=None, powertrain_type="hybrid"):
    """
    Valida rankings por marca de eletrificados.
    """
    checks = []

    for category in FENABRAVE_ELECTRIFIED_PAGE_MAP.values():
        rows = [row for row in item_rows if row.get("vehicle_category") == category]
        ranks = [row.get("rank_position") for row in rows]
        units = [row.get("units") for row in rows]
        brands = [row.get("brand_name_raw") for row in rows]
        shares = [row.get("market_share_pct") for row in rows]
        distinct_ranks = len({rank for rank in ranks if rank is not None})
        invalid_units = sum(1 for value in units if value is None or value <= 0)
        missing_brands = sum(1 for value in brands if not normalize_text(value))
        invalid_shares = sum(
            1 for value in shares if value is None or value < 0 or value > 100
        )
        sorted_rows = sorted(rows, key=lambda row: row.get("rank_position") or 999)
        order_violations = sum(
            1
            for previous, current in zip(sorted_rows, sorted_rows[1:])
            if (previous.get("units") or 0) < (current.get("units") or 0)
        )
        share_total = round(sum(value or 0 for value in shares), 4)
        ranking_total = sum(row.get("units") or 0 for row in rows)
        compare_total = None

        if item6_rows:
            compare_total = next(
                (
                    row.get("units")
                    for row in item6_rows
                    if row.get("vehicle_category") == category
                    and row.get("powertrain_type") == powertrain_type
                ),
                None,
            )

        checks.extend(
            [
                {
                    "check_name": f"{category}_{powertrain_type}_row_count",
                    "calculated_value": len(rows),
                    "expected_value": None,
                    "difference": None,
                    "passed": len(rows) > 0,
                    "severity": "error",
                    "notes": "A quantidade de marcas publicadas pode variar por mes.",
                },
                {
                    "check_name": f"{category}_{powertrain_type}_distinct_ranks",
                    "calculated_value": distinct_ranks,
                    "expected_value": len(rows),
                    "difference": distinct_ranks - len(rows),
                    "passed": distinct_ranks == len(rows),
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_{powertrain_type}_positive_units",
                    "calculated_value": invalid_units,
                    "expected_value": 0,
                    "difference": invalid_units,
                    "passed": invalid_units == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_{powertrain_type}_brand_names",
                    "calculated_value": missing_brands,
                    "expected_value": 0,
                    "difference": missing_brands,
                    "passed": missing_brands == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_{powertrain_type}_share_range",
                    "calculated_value": invalid_shares,
                    "expected_value": 0,
                    "difference": invalid_shares,
                    "passed": invalid_shares == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_{powertrain_type}_descending_units",
                    "calculated_value": order_violations,
                    "expected_value": 0,
                    "difference": order_violations,
                    "passed": order_violations == 0,
                    "severity": "error",
                    "notes": None,
                },
                {
                    "check_name": f"{category}_{powertrain_type}_share_total_lte_100",
                    "calculated_value": share_total,
                    "expected_value": 100,
                    "difference": round(share_total - 100, 4),
                    "passed": share_total <= 100.5,
                    "severity": "warning",
                    "notes": "Top N por marca pode nao somar 100% se houver marcas fora do ranking publicado.",
                },
                {
                    "check_name": f"{category}_{powertrain_type}_ranking_total_lte_market_total",
                    "calculated_value": ranking_total,
                    "expected_value": compare_total,
                    "difference": None if compare_total is None else ranking_total - compare_total,
                    "passed": compare_total is None or ranking_total <= compare_total,
                    "severity": "warning" if compare_total is None else "error",
                    "notes": "Comparacao usa o bloco mensal consolidado do item 6.",
                },
            ]
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
    print(f"{'segment_code':28} {'segmento':28} {'mes_atual':>10}")
    print("-" * 96)

    for row in normalized_rows:
        print(
            f"{row['segment_code'][:28]:28} "
            f"{row['segmento'][:28]:28} "
            f"{row['mes_atual']:>10}"
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
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':32} notes={check['notes']}")

    print("")


def print_model_ranking_preview(ranking_rows, ranking_checks, item_code):
    """
    Imprime preview de ranking Fenabrave por modelo.

    Resultado esperado:
    - operador consegue conferir top 10 de cada categoria e checks do item.
    """
    item_definition = FENABRAVE_ITEM_DEFINITIONS[item_code]
    print(
        f"{item_definition['label']} (pagina {item_definition['page']}, "
        f"{item_definition['published_period_type']})"
    )
    print("-" * 96)
    print(f"{'categoria':20} {'rank':>4} {'modelo':38} {'unidades':>10}")
    print("-" * 96)

    for category in FENABRAVE_ITEM1_CATEGORIES:
        category_rows = sorted(
            [row for row in ranking_rows if row["vehicle_category"] == category],
            key=lambda row: row["rank_position"],
        )[:10]

        for row in category_rows:
            print(
                f"{category[:20]:20} "
                f"{row['rank_position']:>4} "
                f"{row['model_label_raw'][:38]:38} "
                f"{row['monthly_units']:>10}"
            )

    print("")
    print(f"Validacoes locais de {item_definition['code']}")
    print("-" * 96)

    for check in ranking_checks:
        print(
            f"{check['check_name']:42} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':42} notes={check['notes']}")

    print("")


def print_item1_preview(item1_rows, item1_checks):
    """
    Imprime preview do ranking mensal da pagina 6.
    """
    print_model_ranking_preview(
        item1_rows,
        item1_checks,
        FENABRAVE_ITEM1_CODE,
    )


def print_item2_preview(item2_rows, item2_checks):
    """
    Imprime preview do ranking acumulado da pagina 7.
    """
    print_model_ranking_preview(
        item2_rows,
        item2_checks,
        FENABRAVE_ITEM2_CODE,
    )


def print_item3_preview(item3_rows, item3_checks):
    """
    Imprime preview do ranking por marca mensal da pagina 8.
    """
    print("Ranking por marca mes (pagina 8, monthly)")
    print("-" * 96)
    print(f"{'categoria':20} {'rank':>4} {'marca':28} {'unidades':>10} {'share':>10}")
    print("-" * 96)

    for category in FENABRAVE_ITEM1_CATEGORIES:
        category_rows = sorted(
            [row for row in item3_rows if row["vehicle_category"] == category],
            key=lambda row: row["rank_position"],
        )[:10]

        for row in category_rows:
            print(
                f"{category[:20]:20} "
                f"{row['rank_position']:>4} "
                f"{row['brand_name_raw'][:28]:28} "
                f"{row['units']:>10} "
                f"{row['market_share_pct']:>9.2f}%"
            )

    print("")
    print(f"Validacoes locais de {FENABRAVE_ITEM3_CODE}")
    print("-" * 96)

    for check in item3_checks:
        print(
            f"{check['check_name']:42} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':42} notes={check['notes']}")

    print("")


def print_item4_preview(item4_rows, item4_checks):
    """
    Imprime preview do ranking por marca acumulado da pagina 9.
    """
    print("Ranking por marca acumulado (pagina 9, accumulated)")
    print("-" * 96)
    print(f"{'categoria':20} {'rank':>4} {'marca':28} {'unidades':>10} {'share':>10}")
    print("-" * 96)

    for category in FENABRAVE_ITEM1_CATEGORIES:
        category_rows = sorted(
            [row for row in item4_rows if row["vehicle_category"] == category],
            key=lambda row: row["rank_position"],
        )[:10]

        for row in category_rows:
            print(
                f"{category[:20]:20} "
                f"{row['rank_position']:>4} "
                f"{row['brand_name_raw'][:28]:28} "
                f"{row['units']:>10} "
                f"{row['market_share_pct']:>9.2f}%"
            )

    print("")
    print(f"Validacoes locais de {FENABRAVE_ITEM4_CODE}")
    print("-" * 96)

    for check in item4_checks:
        print(
            f"{check['check_name']:42} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':42} notes={check['notes']}")

    print("")


def print_item5_preview(item5_rows, item5_checks):
    """
    Imprime preview do item 5 na pagina 17.
    """
    print("Emplacamentos por sub segmento (pagina 17, mixed)")
    print("-" * 120)
    print(
        f"{'subsegmento':28} {'mes':>8} {'acum_n':>10} {'acum_n_1':>12}"
    )
    print("-" * 120)

    for row in item5_rows:
        print(
            f"{row['subsegment_name'][:28]:28} "
            f"{row['current_month_share_pct']:>7.2f}% "
            f"{row['current_year_accum_share_pct']:>9.2f}% "
            f"{row['prior_year_accum_share_pct']:>11.2f}%"
        )

    print("")
    print(f"Validacoes locais de {FENABRAVE_ITEM5_CODE}")
    print("-" * 120)

    for check in item5_checks:
        print(
            f"{check['check_name']:42} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':42} notes={check['notes']}")

    print("")


def print_item6_preview(item6_rows, item6_checks):
    """
    Imprime preview do mercado mensal de eletrificados.
    """
    item_definition = FENABRAVE_ELECTRIFIED_ITEMS[FENABRAVE_ITEM6_CODE]
    print(
        f"{item_definition['label']} (paginas 20-21, "
        f"{item_definition['published_period_type']})"
    )
    print("-" * 96)
    print(f"{'categoria':20} {'propulsao':22} {'unidades':>12}")
    print("-" * 96)

    for row in item6_rows:
        print(
            f"{row['vehicle_category'][:20]:20} "
            f"{str(row['powertrain_type'])[:22]:22} "
            f"{row['units']:>12}"
        )

    print("")
    print(f"Validacoes locais de {item_definition['code']}")
    print("-" * 96)

    for check in item6_checks:
        print(
            f"{check['check_name']:42} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':42} notes={check['notes']}")

    print("")


def print_item7_preview(item7_rows, item7_checks):
    """
    Imprime preview do ranking mensal por marca de hibridos.
    """
    item_definition = FENABRAVE_ELECTRIFIED_ITEMS[FENABRAVE_ITEM7_CODE]
    print(
        f"{item_definition['label']} (paginas 20-21, "
        f"{item_definition['published_period_type']})"
    )
    print("-" * 96)
    print(f"{'categoria':20} {'rank':>4} {'marca':34} {'unidades':>10} {'share':>8}")
    print("-" * 96)

    for category in FENABRAVE_ELECTRIFIED_PAGE_MAP.values():
        category_rows = sorted(
            [row for row in item7_rows if row["vehicle_category"] == category],
            key=lambda row: row["rank_position"],
        )[:10]

        for row in category_rows:
            print(
                f"{category[:20]:20} "
                f"{row['rank_position']:>4} "
                f"{row['brand_name_raw'][:34]:34} "
                f"{row['units']:>10} "
                f"{row['market_share_pct']:>7.2f}%"
            )

    print("")
    print(f"Validacoes locais de {item_definition['code']}")
    print("-" * 96)

    for check in item7_checks:
        print(
            f"{check['check_name']:42} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':42} notes={check['notes']}")

    print("")


def print_item8_preview(item8_rows, item8_checks):
    """
    Imprime preview do ranking mensal por marca de eletricos.
    """
    item_definition = FENABRAVE_ELECTRIFIED_ITEMS[FENABRAVE_ITEM8_CODE]
    print(
        f"{item_definition['label']} (paginas 20-21, "
        f"{item_definition['published_period_type']})"
    )
    print("-" * 96)
    print(f"{'categoria':20} {'rank':>4} {'marca':34} {'unidades':>10} {'share':>8}")
    print("-" * 96)

    for category in FENABRAVE_ELECTRIFIED_PAGE_MAP.values():
        category_rows = sorted(
            [row for row in item8_rows if row["vehicle_category"] == category],
            key=lambda row: row["rank_position"],
        )[:10]

        for row in category_rows:
            print(
                f"{category[:20]:20} "
                f"{row['rank_position']:>4} "
                f"{row['brand_name_raw'][:34]:34} "
                f"{row['units']:>10} "
                f"{row['market_share_pct']:>7.2f}%"
            )

    print("")
    print(f"Validacoes locais de {item_definition['code']}")
    print("-" * 96)

    for check in item8_checks:
        print(
            f"{check['check_name']:42} "
            f"calc={check['calculated_value']} "
            f"expected={check['expected_value']} "
            f"diff={check['difference']} "
            f"passed={check['passed']} "
            f"severity={check['severity']}"
        )

        if check["notes"]:
            print(f"{'':42} notes={check['notes']}")

    print("")


def delete_existing_rows(base_url, headers, source_file_id):
    """
    Remove cargas anteriores do mesmo arquivo de origem.

    Resultado esperado:
    - usado por `--replace` para reprocessar um PDF sem duplicar linhas.
    """
    for table in [
        "market_vehicle_registrations_segment",
    ]:
        url = rest_url(base_url, table)
        params = {"source_file_id": f"eq.{source_file_id}"}
        response = requests.delete(url, headers=headers, params=params, timeout=60)

        if response.status_code not in {200, 204}:
            raise RuntimeError(
                f"Falha ao limpar {table}: status={response.status_code} "
                f"body={response.text[:500]}"
            )


def delete_model_ranking_rows(base_url, headers, source_file_id, item_code):
    """
    Remove apenas linhas de um item de ranking para um arquivo.

    Resultado esperado:
    - permite reprocessar o item sem afetar outros rankings futuros.
    """
    params = {
        "source_file_id": f"eq.{source_file_id}",
        "item_code": f"eq.{item_code}",
    }
    response = requests.delete(
        rest_url(base_url, "market_vehicle_model_rankings"),
        headers=headers,
        params=params,
        timeout=60,
    )

    if response.status_code not in {200, 204}:
        raise RuntimeError(
            "Falha ao limpar market_vehicle_model_rankings: "
            f"status={response.status_code} body={response.text[:500]}"
        )


def delete_brand_ranking_rows(base_url, headers, source_file_id, item_code):
    """
    Remove linhas de ranking por marca para um arquivo/item.
    """
    params = {
        "source_file_id": f"eq.{source_file_id}",
        "item_code": f"eq.{item_code}",
    }
    response = requests.delete(
        rest_url(base_url, "market_vehicle_brand_rankings"),
        headers=headers,
        params=params,
        timeout=60,
    )

    if response.status_code not in {200, 204}:
        raise RuntimeError(
            "Falha ao limpar market_vehicle_brand_rankings: "
            f"status={response.status_code} body={response.text[:500]}"
        )


def delete_subsegment_share_rows(base_url, headers, source_file_id, item_code):
    """
    Remove apenas linhas de shares por subsegmento para um arquivo.
    """
    params = {
        "source_file_id": f"eq.{source_file_id}",
        "item_code": f"eq.{item_code}",
    }
    response = requests.delete(
        rest_url(base_url, "market_vehicle_subsegment_shares"),
        headers=headers,
        params=params,
        timeout=60,
    )

    if response.status_code not in {200, 204}:
        raise RuntimeError(
            "Falha ao limpar market_vehicle_subsegment_shares: "
            f"status={response.status_code} body={response.text[:500]}"
        )


def insert_rows(base_url, headers, table, rows):
    """
    Insere uma lista de registros em uma tabela Supabase.

    Resultado esperado:
    - grava payloads normalizados; se a tabela nao existir ou houver conflito,
      retorna erro claro.
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


def upsert_fenabrave_item_status(
    base_url,
    headers,
    source_file_id,
    reference_period,
    item_code,
    status,
    row_count,
    validation_status,
    validation_notes,
):
    """
    Cria ou atualiza o status do item 1 para um PDF.

    Resultado esperado:
    - `market_fenabrave_extraction_items` reflete a situacao mensal do item.
    """
    item_definition = FENABRAVE_ITEM_DEFINITIONS[item_code]
    params = {
        "select": "id",
        "source_file_id": f"eq.{source_file_id}",
        "item_code": f"eq.{item_code}",
        "limit": "1",
    }
    rows = request_json(
        "GET",
        rest_url(base_url, "market_fenabrave_extraction_items"),
        headers,
        params=params,
    )
    payload = {
        "source_file_id": source_file_id,
        "reference_period": reference_period,
        "item_code": item_definition["code"],
        "item_label": item_definition["label"],
        "pdf_page": item_definition["page"],
        "published_period_type": item_definition["published_period_type"],
        "market_scope": item_definition["market_scope"],
        "status": status,
        "row_count": row_count,
        "validation_status": validation_status,
        "validation_notes": validation_notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_headers = dict(headers)
    write_headers["Prefer"] = "return=minimal"

    if rows:
        response = requests.patch(
            rest_url(base_url, "market_fenabrave_extraction_items"),
            headers=write_headers,
            params={"id": f"eq.{rows[0]['id']}"},
            data=json.dumps(payload),
            timeout=60,
        )
    else:
        response = requests.post(
            rest_url(base_url, "market_fenabrave_extraction_items"),
            headers=write_headers,
            data=json.dumps(payload),
            timeout=60,
        )

    if not response.ok:
        raise RuntimeError(
            "Falha ao atualizar market_fenabrave_extraction_items: "
            f"status={response.status_code} body={response.text[:500]}"
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


def write_results(
    base_url,
    headers,
    source_file_id,
    normalized_rows,
    checks,
    replace,
    item1_rows=None,
    item1_checks=None,
    item2_rows=None,
    item2_checks=None,
    item3_rows=None,
    item3_checks=None,
    item4_rows=None,
    item4_checks=None,
    item5_rows=None,
    item5_checks=None,
):
    """
    Persiste normalizado e status no Supabase.

    Resultado esperado:
    - em `--write`, grava os dados normalizados; com `--replace`,
      limpa cargas antigas do mesmo arquivo antes de inserir novamente.
    """
    if replace:
        delete_existing_rows(base_url, headers, source_file_id)

    insert_rows(
        base_url,
        headers,
        "market_vehicle_registrations_segment",
        normalized_rows,
    )

    if item1_rows is not None:
        if replace:
            delete_model_ranking_rows(
                base_url,
                headers,
                source_file_id,
                FENABRAVE_ITEM1_CODE,
            )

        item1_has_error = any(
            not check["passed"] and check["severity"] == "error"
            for check in (item1_checks or [])
        )

        if item1_has_error:
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM1_CODE,
                "failed",
                len(item1_rows),
                "failed",
                "Item 1 Fenabrave falhou em validacoes locais.",
            )
        else:
            insert_rows(
                base_url,
                headers,
                "market_vehicle_model_rankings",
                item1_rows,
            )
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM1_CODE,
                "validated",
                len(item1_rows),
                "passed",
                "Item 1 Fenabrave validado e gravado pela rotina mensal.",
            )

    if item2_rows is not None:
        if replace:
            delete_model_ranking_rows(
                base_url,
                headers,
                source_file_id,
                FENABRAVE_ITEM2_CODE,
            )

        item2_has_error = any(
            not check["passed"] and check["severity"] == "error"
            for check in (item2_checks or [])
        )

        if item2_has_error:
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM2_CODE,
                "failed",
                len(item2_rows),
                "failed",
                "Item 2 Fenabrave falhou em validacoes locais.",
            )
        else:
            insert_rows(
                base_url,
                headers,
                "market_vehicle_model_rankings",
                item2_rows,
            )
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM2_CODE,
                "validated",
                len(item2_rows),
                "passed",
                "Item 2 Fenabrave validado e gravado pela rotina mensal.",
            )

    if item3_rows is not None:
        if replace:
            delete_brand_ranking_rows(
                base_url,
                headers,
                source_file_id,
                FENABRAVE_ITEM3_CODE,
            )

        item3_has_error = any(
            not check["passed"] and check["severity"] == "error"
            for check in (item3_checks or [])
        )

        if item3_has_error:
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM3_CODE,
                "failed",
                len(item3_rows),
                "failed",
                "Item 3 Fenabrave falhou em validacoes locais.",
            )
        else:
            insert_rows(
                base_url,
                headers,
                "market_vehicle_brand_rankings",
                item3_rows,
            )
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM3_CODE,
                "validated",
                len(item3_rows),
                "passed",
                "Item 3 Fenabrave validado e gravado pela rotina mensal.",
            )

    if item4_rows is not None:
        if replace:
            delete_brand_ranking_rows(
                base_url,
                headers,
                source_file_id,
                FENABRAVE_ITEM4_CODE,
            )

        item4_has_error = any(
            not check["passed"] and check["severity"] == "error"
            for check in (item4_checks or [])
        )

        if item4_has_error:
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM4_CODE,
                "failed",
                len(item4_rows),
                "failed",
                "Item 4 Fenabrave falhou em validacoes locais.",
            )
        else:
            insert_rows(
                base_url,
                headers,
                "market_vehicle_brand_rankings",
                item4_rows,
            )
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM4_CODE,
                "validated",
                len(item4_rows),
                "passed",
                "Item 4 Fenabrave validado e gravado pela rotina mensal.",
            )

    if item5_rows is not None:
        if replace:
            delete_subsegment_share_rows(
                base_url,
                headers,
                source_file_id,
                FENABRAVE_ITEM5_CODE,
            )

        item5_has_error = any(
            not check["passed"] and check["severity"] == "error"
            for check in (item5_checks or [])
        )

        if item5_has_error:
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM5_CODE,
                "failed",
                len(item5_rows),
                "failed",
                "Item 5 Fenabrave falhou em validacoes locais.",
            )
        else:
            insert_rows(
                base_url,
                headers,
                "market_vehicle_subsegment_shares",
                item5_rows,
            )
            upsert_fenabrave_item_status(
                base_url,
                headers,
                source_file_id,
                normalized_rows[0]["reference_period"],
                FENABRAVE_ITEM5_CODE,
                "validated",
                len(item5_rows),
                "passed",
                "Item 5 Fenabrave validado e gravado pela rotina mensal.",
            )

    has_error = any(
        not check["passed"] and check["severity"] == "error" for check in checks
    )

    if not has_error:
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


def open_pdf_for_review(pdf_path):
    """
    Abre o PDF temporario para revisao visual, quando o ambiente permite.

    Resultado esperado:
    - no Windows, abre o PDF no visualizador padrao.
    - em outros ambientes, tenta usar `open` ou `xdg-open`.
    - retorna um handle de processo quando possivel, para fechamento best effort.
    """
    try:
        if os.name == "nt":
            os.startfile(str(pdf_path))
            return None

        opener = "open" if sys.platform == "darwin" else "xdg-open"
        return subprocess.Popen(
            [opener, str(pdf_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as error:
        print(f"Aviso: nao foi possivel abrir o PDF automaticamente: {error}")
        return None


def close_pdf_review(process):
    """
    Fecha o visualizador do PDF quando existe um processo controlado.

    Resultado esperado:
    - encerra o processo aberto por `xdg-open/open` quando houver handle.
    - no Windows com `os.startfile`, nao ha PID confiavel do visualizador
      padrao; nesse caso o fechamento e manual/best effort.
    """
    if process is None:
        return

    try:
        process.terminate()
    except Exception:
        pass


def ask_operator_approval_gui():
    """
    Exibe caixa de dialogo OK/NOK para validacao do operador.

    Resultado esperado:
    - retorna True se o operador clicar OK.
    - retorna False se clicar NOK/cancelar.
    - se GUI nao estiver disponivel, levanta excecao para fallback terminal.
    """
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    result = messagebox.askokcancel(
        title="Validacao Fenabrave",
        message=(
            "Confira o PDF aberto e o preview no terminal.\n\n"
            "Os dados extraidos estao corretos?\n\n"
            "OK = salvar/liberar continuidade\n"
            "NOK = nao salvar e retornar erro"
        ),
        parent=root,
    )
    root.destroy()
    return bool(result)


def ask_operator_approval_terminal():
    """
    Solicita validacao pelo terminal quando a GUI nao estiver disponivel.

    Resultado esperado:
    - aceita apenas `ok` ou `nok`.
    - retorna True para `ok` e False para `nok`.
    """
    while True:
        answer = input("Os dados extraidos estao corretos? Digite ok ou nok: ")
        normalized = answer.strip().lower()

        if normalized == "ok":
            return True

        if normalized == "nok":
            return False

        print("Resposta invalida. Use apenas ok ou nok.")


def operator_review(pdf_bytes, open_pdf):
    """
    Executa a revisao humana antes de gravar dados.

    Resultado esperado:
    - salva uma copia temporaria do PDF.
    - abre o PDF se `open_pdf=True`.
    - pergunta OK/NOK ao operador.
    - remove a copia temporaria quando possivel.
    """
    pdf_path = save_temp_pdf(pdf_bytes)
    process = None

    try:
        if open_pdf:
            process = open_pdf_for_review(pdf_path)

        try:
            approved = ask_operator_approval_gui()
        except Exception as error:
            print(f"Aviso: caixa grafica indisponivel ({error}). Usando terminal.")
            approved = ask_operator_approval_terminal()

        return approved
    finally:
        close_pdf_review(process)

        try:
            pdf_path.unlink()
        except Exception:
            print(
                f"Aviso: nao foi possivel remover PDF temporario: {pdf_path}. "
                "Feche o visualizador e remova manualmente se necessario."
            )


def parse_args():
    """
    Define argumentos de linha de comando do script.

    Resultado esperado:
    - permite rodar em `--dry-run`, `--write` e `--replace`.
    - path e URL do PDF sao informados no comando mensal, sem editar `.env`.
    - periodo pode ser inferido pelo nome do arquivo.
    """
    parser = argparse.ArgumentParser(
        description="Extrai a primeira tabela da pagina 1 de PDF Fenabrave no Supabase Storage."
    )
    parser.add_argument("--dry-run", action="store_true", help="Extrai e valida sem gravar.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Grava tabela normalizada e atualiza status no Supabase.",
    )
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
        default=None,
        help=(
            "Periodo de referencia YYYY-MM-DD. Opcional; se omitido, "
            "o script infere do nome do arquivo, ex: 2026_04_02.pdf -> 2026-04-01."
        ),
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
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Nao abre dialogo OK/NOK antes de gravar. Use apenas em automacao confiavel.",
    )
    parser.add_argument(
        "--no-open-pdf",
        action="store_true",
        help="Mantem a caixa OK/NOK, mas nao tenta abrir o PDF automaticamente.",
    )
    parser.add_argument(
        "--skip-phase2-item1",
        action="store_true",
        help=(
            "Nao executa o item 1 da fase 2. Use apenas para contingencia; "
            "por padrao o item 1 faz parte da inclusao mensal Fenabrave."
        ),
    )
    parser.add_argument(
        "--skip-phase2-item2",
        action="store_true",
        help=(
            "Nao executa o item 2 da fase 2. Use apenas para contingencia; "
            "por padrao o item 2 passa a fazer parte da inclusao mensal Fenabrave."
        ),
    )
    parser.add_argument(
        "--skip-phase2-item3",
        action="store_true",
        help=(
            "Nao executa o item 3 da fase 2. Use apenas para contingencia; "
            "por padrao o item 3 passa a fazer parte da inclusao mensal Fenabrave."
        ),
    )
    parser.add_argument(
        "--skip-phase2-item4",
        action="store_true",
        help=(
            "Nao executa o item 4 da fase 2. Use apenas para contingencia; "
            "por padrao o item 4 passa a fazer parte da inclusao mensal Fenabrave."
        ),
    )
    parser.add_argument(
        "--skip-phase2-item5",
        action="store_true",
        help=(
            "Nao executa o item 5 da fase 2. Use apenas para contingencia; "
            "por padrao o item 5 passa a fazer parte da inclusao mensal Fenabrave."
        ),
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
    reference_period = args.reference_period or infer_reference_period_from_path(
        storage_path
    )
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

    item1_rows = None
    item1_checks = None
    item2_rows = None
    item2_checks = None
    item3_rows = None
    item3_checks = None
    item4_rows = None
    item4_checks = None
    item5_rows = None
    item5_checks = None

    if not args.skip_phase2_item1:
        print("Extraindo item 1 da fase 2 na pagina 6...")
        item1_raw_rows = extract_item1_model_rankings(pdf_bytes)
        item1_rows = normalize_item1_rows(
            item1_raw_rows,
            source_file_id_for_preview,
            reference_period,
        )
        item1_checks = validate_item1_rows(item1_rows, normalized_rows)

    if not args.skip_phase2_item2:
        print("Extraindo item 2 da fase 2 na pagina 7...")
        item2_raw_rows = extract_item2_model_rankings(pdf_bytes)
        item2_rows = normalize_item2_rows(
            item2_raw_rows,
            source_file_id_for_preview,
            reference_period,
        )
        item2_checks = validate_item2_rows(item2_rows, item1_rows)

    if not args.skip_phase2_item3:
        print("Extraindo item 3 da fase 2 na pagina 8...")
        item3_raw_rows = extract_item3_brand_rankings(pdf_bytes)
        item3_rows = normalize_item3_rows(
            item3_raw_rows,
            source_file_id_for_preview,
            reference_period,
        )
        item3_checks = validate_item3_rows(item3_rows)

    if not args.skip_phase2_item4:
        print("Extraindo item 4 da fase 2 na pagina 9...")
        item4_raw_rows = extract_item4_brand_rankings(pdf_bytes)
        item4_rows = normalize_item4_rows(
            item4_raw_rows,
            source_file_id_for_preview,
            reference_period,
        )
        item4_checks = validate_item4_rows(item4_rows, item3_rows)

    if not args.skip_phase2_item5:
        print("Extraindo item 5 da fase 2 na pagina 17...")
        item5_raw_rows = extract_item5_subsegment_shares(pdf_bytes)
        item5_rows = normalize_item5_rows(
            item5_raw_rows,
            source_file_id_for_preview,
            reference_period,
        )
        item5_checks = validate_item5_rows(item5_rows, item5_raw_rows)

    print_preview(raw_rows, normalized_rows, checks, pdf_bytes)

    if item1_rows is not None:
        print_item1_preview(item1_rows, item1_checks)

    if item2_rows is not None:
        print_item2_preview(item2_rows, item2_checks)

    if item3_rows is not None:
        print_item3_preview(item3_rows, item3_checks)

    if item4_rows is not None:
        print_item4_preview(item4_rows, item4_checks)

    if item5_rows is not None:
        print_item5_preview(item5_rows, item5_checks)

    if args.dry_run:
        print("Dry-run concluido. Nenhum dado foi gravado.")
        return

    if source_file_id is None:
        raise RuntimeError(
            "source_file_id ausente. Informe --source-file-id ou permita criar o registro com --write."
        )

    if not args.no_review:
        approved = operator_review(pdf_bytes, open_pdf=not args.no_open_pdf)

        if not approved:
            update_source_file_status(
                base_url,
                headers,
                source_file_id,
                "failed",
                "Operador marcou dados como NOK na revisao interativa.",
            )
            raise RuntimeError(
                "Dados marcados como NOK pelo operador. Nada foi salvo na tabela normalizada."
            )

    print("Gravando resultados no Supabase...")
    write_results(
        base_url,
        headers,
        source_file_id,
        normalized_rows,
        checks,
        replace=args.replace,
        item1_rows=item1_rows,
        item1_checks=item1_checks,
        item2_rows=item2_rows,
        item2_checks=item2_checks,
        item3_rows=item3_rows,
        item3_checks=item3_checks,
        item4_rows=item4_rows,
        item4_checks=item4_checks,
        item5_rows=item5_rows,
        item5_checks=item5_checks,
    )
    print("Carga concluida.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        sys.exit(1)
