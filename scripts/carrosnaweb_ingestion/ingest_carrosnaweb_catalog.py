import argparse
import ast
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "discovery"
SOURCE_NAME = "Carros na Web"
SOURCE_PAGE_URL = "https://www.carrosnaweb.com.br"
SOURCE_TYPE = "catalogo_automotivo"
DATA_ROLE = "catalogo_veiculos"
ACCESS_TYPE = "publico_site_csv"
EXTRACTION_METHOD = "csv_catalog_snapshot"
DEFAULT_REFERENCE_PERIOD = "2026-07-01"

CSV_FILES = {
    "manufacturers": DATA_DIR / "fabricantes.csv",
    "models": DATA_DIR / "modelos.csv",
    "model_years": DATA_DIR / "anos_modelo.csv",
}

EXPECTED_HEADERS = {
    "manufacturers": ["fabricante", "value", "url"],
    "models": [
        "fabricante",
        "modelo",
        "codigo_modelo",
        "url_modelo",
        "href_original",
        "texto_link",
        "params",
    ],
    "model_years": [
        "fabricante",
        "modelo",
        "ano",
        "url_ano",
        "url_modelo_origem",
        "href_original",
        "texto_link",
        "params",
    ],
}


def load_local_env():
    for env_path in [
        BASE_DIR / ".env",
        BASE_DIR.parent / "fenabrave_ingestion" / ".env",
        BASE_DIR.parent.parent / ".env",
    ]:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def require_env(name):
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")

    return value


def normalize_supabase_url(url):
    normalized = url.rstrip("/")

    if normalized.endswith("/rest/v1"):
        normalized = normalized[: -len("/rest/v1")]

    return normalized


def build_headers(supabase_key, prefer=None):
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }

    if prefer:
        headers["Prefer"] = prefer

    return headers


def rest_url(base_url, table):
    return f"{base_url}/rest/v1/{table}"


def request_json(method, url, headers, **kwargs):
    try:
        import requests
    except ImportError:
        return request_json_urllib(method, url, headers, **kwargs)

    response = requests.request(method, url, headers=headers, timeout=60, **kwargs)

    if not response.ok:
        raise RuntimeError(
            f"Supabase request falhou: {method} {url} "
            f"status={response.status_code} body={response.text[:500]}"
        )

    if not response.text:
        return None

    return response.json()


def request_json_urllib(method, url, headers, **kwargs):
    params = kwargs.get("params")
    payload = kwargs.get("json")

    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(params)}"

    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=60) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else None
    except HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Supabase request falhou: {method} {url} "
            f"status={exc.code} body={error_text[:500]}"
        ) from exc


def strip_accents(value):
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_text(value):
    value = "" if value is None else str(value)
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_key(value):
    value = strip_accents(normalize_text(value)).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def read_csv_dicts(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return reader.fieldnames or [], rows


def parse_params(raw_value, issues, row_label):
    raw_value = normalize_text(raw_value)

    if not raw_value:
        return {}

    try:
        parsed = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError) as exc:
        issues.append(f"{row_label}: params invalido ({exc})")
        return {"_raw": raw_value}

    if not isinstance(parsed, dict):
        issues.append(f"{row_label}: params nao e dict")
        return {"_raw": raw_value}

    return parsed


def param_first(params, key):
    value = params.get(key)

    if isinstance(value, list):
        return normalize_text(value[0]) if value else None

    return normalize_text(value) if value is not None else None


def parse_int(value):
    text = normalize_text(value)

    if not text:
        return None

    try:
        return int(text)
    except ValueError:
        return None


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def validate_headers(kind, headers, issues):
    expected = EXPECTED_HEADERS[kind]

    if headers != expected:
        issues.append(
            f"{kind}: schema inesperado. esperado={expected} recebido={headers}"
        )


def load_manufacturers(path, source_file_id=None):
    issues = []
    headers, rows = read_csv_dicts(path)
    validate_headers("manufacturers", headers, issues)
    payload = []
    keys = Counter()

    for idx, row in enumerate(rows, start=2):
        manufacturer_name = normalize_text(row.get("fabricante"))
        manufacturer_param = manufacturer_name
        manufacturer_key = normalize_key(manufacturer_param or manufacturer_name)
        keys[(manufacturer_key,)] += 1

        if not manufacturer_name:
            issues.append(f"fabricantes.csv:{idx}: fabricante obrigatorio")

        payload.append(
            {
                "source_file_id": source_file_id,
                "manufacturer_name": manufacturer_name,
                "manufacturer_param": manufacturer_param,
                "manufacturer_key": manufacturer_key,
                "source_value": normalize_text(row.get("value")),
                "manufacturer_url": normalize_text(row.get("url")),
                "params": {},
            }
        )

    issues.extend(
        f"fabricantes.csv: fabricante duplicado key={key[0]}"
        for key, count in keys.items()
        if count > 1
    )
    return payload, issues


def load_models(path, source_file_id=None):
    issues = []
    headers, rows = read_csv_dicts(path)
    validate_headers("models", headers, issues)
    payload = []
    keys = Counter()

    for idx, row in enumerate(rows, start=2):
        params = parse_params(row.get("params"), issues, f"modelos.csv:{idx}")
        manufacturer_name = normalize_text(row.get("fabricante"))
        model_name = normalize_text(row.get("modelo"))
        manufacturer_param = param_first(params, "fabricante")
        model_param = param_first(params, "modelo")
        manufacturer_key = normalize_key(manufacturer_param or manufacturer_name)
        model_key = normalize_key(model_param or model_name)
        keys[(manufacturer_key, model_key)] += 1

        if not manufacturer_name:
            issues.append(f"modelos.csv:{idx}: fabricante obrigatorio")
        if not model_name:
            issues.append(f"modelos.csv:{idx}: modelo obrigatorio")

        payload.append(
            {
                "source_file_id": source_file_id,
                "manufacturer_name": manufacturer_name,
                "manufacturer_param": manufacturer_param,
                "manufacturer_key": manufacturer_key,
                "model_name": model_name,
                "model_param": model_param,
                "model_key": model_key,
                "model_code": normalize_text(row.get("codigo_modelo")),
                "model_url": normalize_text(row.get("url_modelo")),
                "href_original": normalize_text(row.get("href_original")),
                "link_text": normalize_text(row.get("texto_link")),
                "params": params,
            }
        )

    issues.extend(
        f"modelos.csv: modelo duplicado manufacturer_key={key[0]} model_key={key[1]}"
        for key, count in keys.items()
        if count > 1
    )
    return payload, issues


def load_model_years(path, source_file_id=None):
    issues = []
    headers, rows = read_csv_dicts(path)
    validate_headers("model_years", headers, issues)
    payload = []
    keys = Counter()

    for idx, row in enumerate(rows, start=2):
        params = parse_params(row.get("params"), issues, f"anos_modelo.csv:{idx}")
        manufacturer_name = normalize_text(row.get("fabricante"))
        model_name = normalize_text(row.get("modelo"))
        model_year = parse_int(row.get("ano"))
        manufacturer_param = param_first(params, "fabricante")
        model_param = param_first(params, "varnome")
        param_year_start = parse_int(param_first(params, "anoini"))
        param_year_end = parse_int(param_first(params, "anofim"))
        manufacturer_key = normalize_key(manufacturer_param or manufacturer_name)
        model_key = normalize_key(model_param or model_name)

        keys[(manufacturer_key, model_key, model_year)] += 1

        if not manufacturer_name:
            issues.append(f"anos_modelo.csv:{idx}: fabricante obrigatorio")
        if not model_name:
            issues.append(f"anos_modelo.csv:{idx}: modelo obrigatorio")
        if model_year is None:
            issues.append(f"anos_modelo.csv:{idx}: ano obrigatorio/numerico")

        payload.append(
            {
                "source_file_id": source_file_id,
                "manufacturer_name": manufacturer_name,
                "manufacturer_param": manufacturer_param,
                "manufacturer_key": manufacturer_key,
                "model_name": model_name,
                "model_param": model_param,
                "model_key": model_key,
                "model_year": model_year,
                "param_year_start": param_year_start,
                "param_year_end": param_year_end,
                "year_url": normalize_text(row.get("url_ano")),
                "source_model_url": normalize_text(row.get("url_modelo_origem")),
                "href_original": normalize_text(row.get("href_original")),
                "link_text": normalize_text(row.get("texto_link")),
                "params": params,
            }
        )

    issues.extend(
        "anos_modelo.csv: ano/modelo duplicado "
        f"manufacturer_key={key[0]} model_key={key[1]} model_year={key[2]}"
        for key, count in keys.items()
        if count > 1
    )
    return payload, issues


def file_metadata(path, reference_period):
    return {
        "reference_period": reference_period,
        "source_url": f"git:4ace350:scripts/carrosnaweb_ingestion/data/discovery/{path.name}",
        "source_page_url": SOURCE_PAGE_URL,
        "file_type": "csv",
        "storage_bucket": None,
        "storage_path": None,
        "original_filename": path.name,
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "extraction_status": "validated",
        "extraction_method": EXTRACTION_METHOD,
        "extraction_notes": (
            "Snapshot historico usado como catalogo operacional de fabricantes, "
            "modelos e anos/modelo; fichas tecnicas permanecem fora do escopo."
        ),
    }


def load_all(reference_period):
    missing = [str(path) for path in CSV_FILES.values() if not path.exists()]

    if missing:
        raise RuntimeError(f"CSVs obrigatorios ausentes: {missing}")

    manufacturers, manufacturer_issues = load_manufacturers(CSV_FILES["manufacturers"])
    models, model_issues = load_models(CSV_FILES["models"])
    model_years, year_issues = load_model_years(CSV_FILES["model_years"])
    metadata = {
        kind: file_metadata(path, reference_period)
        for kind, path in CSV_FILES.items()
    }
    issues = manufacturer_issues + model_issues + year_issues

    return {
        "manufacturers": manufacturers,
        "models": models,
        "model_years": model_years,
        "metadata": metadata,
        "issues": issues,
    }


def print_sample_matches(model_years):
    probes = [
        ("BYD", "Dolphin"),
        ("Renault", "Kwid"),
        ("Changan", "Uni T"),
        ("Hyundai", "HB20"),
    ]

    print("\nBuscas de validacao local:")

    for brand, model in probes:
        brand_key = normalize_key(brand)
        model_key = normalize_key(model)
        matches = [
            row
            for row in model_years
            if row["manufacturer_key"] == brand_key and model_key in row["model_key"]
        ]
        status = "found" if matches else "not_found"
        years = sorted({row["model_year"] for row in matches if row["model_year"]})
        years_preview = ",".join(str(year) for year in years[:5])
        if len(years) > 5:
            years_preview += ",..."
        print(f"- {brand} {model}: {status} count={len(matches)} years={years_preview}")


def get_or_create_source(base_url, headers):
    params = {"select": "id,source_name", "source_name": f"eq.{SOURCE_NAME}"}
    rows = request_json(
        "GET",
        rest_url(base_url, "market_data_sources"),
        headers,
        params=params,
    )

    if rows:
        return rows[0]["id"]

    payload = {
        "source_name": SOURCE_NAME,
        "source_type": SOURCE_TYPE,
        "data_role": DATA_ROLE,
        "structured_ingestion": True,
        "priority": 3,
        "access_type": ACCESS_TYPE,
        "official_url": SOURCE_PAGE_URL,
        "notes": (
            "Catalogo de fabricantes, modelos e anos/modelo por CSV; usado para "
            "homogeneizacao de entidades extraidas de videos."
        ),
    }
    inserted = request_json(
        "POST",
        rest_url(base_url, "market_data_sources"),
        build_headers(headers["apikey"], prefer="return=representation"),
        json=payload,
    )
    return inserted[0]["id"]


def get_or_create_source_file(base_url, headers, source_id, metadata):
    params = {
        "select": "id",
        "source_id": f"eq.{source_id}",
        "reference_period": f"eq.{metadata['reference_period']}",
        "source_url": f"eq.{metadata['source_url']}",
    }
    rows = request_json(
        "GET",
        rest_url(base_url, "market_source_files"),
        headers,
        params=params,
    )

    if rows:
        source_file_id = rows[0]["id"]
        patch_payload = {
            key: value
            for key, value in metadata.items()
            if key not in {"reference_period", "source_url"}
        }
        request_json(
            "PATCH",
            rest_url(base_url, "market_source_files"),
            build_headers(headers["apikey"], prefer="return=minimal"),
            params={"id": f"eq.{source_file_id}"},
            json=patch_payload,
        )
        return source_file_id

    payload = {"source_id": source_id, **metadata}
    inserted = request_json(
        "POST",
        rest_url(base_url, "market_source_files"),
        build_headers(headers["apikey"], prefer="return=representation"),
        json=payload,
    )
    return inserted[0]["id"]


def post_batches(base_url, headers, table, rows, conflict_columns, batch_size):
    url = rest_url(base_url, table)
    params = {"on_conflict": ",".join(conflict_columns)}
    write_headers = build_headers(
        headers["apikey"],
        prefer="resolution=merge-duplicates,return=minimal",
    )

    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        request_json("POST", url, write_headers, params=params, json=batch)
        print(f"- {table}: enviados {min(start + batch_size, len(rows))}/{len(rows)}")


def check_tables(base_url, headers):
    tables = [
        "market_carrosnaweb_manufacturers",
        "market_carrosnaweb_models",
        "market_carrosnaweb_model_years",
    ]

    for table in tables:
        request_json(
            "GET",
            rest_url(base_url, table),
            headers,
            params={"select": "id", "limit": "1"},
        )


def write_to_supabase(loaded, reference_period, batch_size):
    load_local_env()
    base_url = normalize_supabase_url(require_env("SUPABASE_URL"))
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

    if not supabase_key:
        raise RuntimeError("Configure SUPABASE_SERVICE_ROLE_KEY ou SUPABASE_KEY")

    headers = build_headers(supabase_key)
    check_tables(base_url, headers)
    source_id = get_or_create_source(base_url, headers)
    print(f"Fonte Carros na Web source_id={source_id}")

    source_file_ids = {
        kind: get_or_create_source_file(base_url, headers, source_id, metadata)
        for kind, metadata in loaded["metadata"].items()
    }

    manufacturers, _ = load_manufacturers(
        CSV_FILES["manufacturers"], source_file_ids["manufacturers"]
    )
    models, _ = load_models(CSV_FILES["models"], source_file_ids["models"])
    model_years, _ = load_model_years(
        CSV_FILES["model_years"], source_file_ids["model_years"]
    )

    post_batches(
        base_url,
        headers,
        "market_carrosnaweb_manufacturers",
        manufacturers,
        ["source_file_id", "manufacturer_key"],
        batch_size,
    )
    post_batches(
        base_url,
        headers,
        "market_carrosnaweb_models",
        models,
        ["source_file_id", "manufacturer_key", "model_key"],
        batch_size,
    )
    post_batches(
        base_url,
        headers,
        "market_carrosnaweb_model_years",
        model_years,
        ["source_file_id", "manufacturer_key", "model_key", "model_year"],
        batch_size,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Ingere CSVs de catalogo Carros na Web no Supabase para "
            "homogeneizacao de fabricantes, modelos e anos/modelo."
        )
    )
    parser.add_argument("--dry-run", action="store_true", help="Valida sem escrever no Supabase.")
    parser.add_argument("--write", action="store_true", help="Escreve no Supabase via REST.")
    parser.add_argument(
        "--reference-period",
        default=DEFAULT_REFERENCE_PERIOD,
        help="Periodo de referencia dos CSVs, no formato YYYY-MM-DD.",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    if args.dry_run == args.write:
        parser.error("Use exatamente uma opcao: --dry-run ou --write")

    try:
        loaded = load_all(args.reference_period)
    except RuntimeError as exc:
        print(f"Erro: {exc}")
        return 1

    print("Catalogo Carros na Web")
    print(f"- reference_period: {args.reference_period}")
    print(f"- fabricantes: {len(loaded['manufacturers'])}")
    print(f"- modelos: {len(loaded['models'])}")
    print(f"- anos_modelo: {len(loaded['model_years'])}")
    print("- aplicacoes_modelo_ano_test.csv: fora da carga")

    for kind, metadata in loaded["metadata"].items():
        print(
            f"- {kind}: file={metadata['original_filename']} "
            f"size={metadata['file_size_bytes']} sha256={metadata['sha256']}"
        )

    if loaded["issues"]:
        print("\nFalhas de validacao:")
        for issue in loaded["issues"][:50]:
            print(f"- {issue}")
        if len(loaded["issues"]) > 50:
            print(f"- ... mais {len(loaded['issues']) - 50} falhas")
        return 1

    print("\nValidacao local: ok")
    print_sample_matches(loaded["model_years"])

    if args.write:
        try:
            write_to_supabase(loaded, args.reference_period, args.batch_size)
        except RuntimeError as exc:
            print(f"\nCarga Supabase: bloqueada")
            print(f"Erro: {exc}")

            if "PGRST205" in str(exc) or "Could not find the table" in str(exc):
                print(
                    "Acao necessaria: aplicar antes a DDL "
                    "sql/ddl/tables/021_create_market_carrosnaweb_catalog.sql "
                    "e sql/ddl/views/022_create_v_carrosnaweb_vehicle_catalog.sql."
                )

            return 1

        print("\nCarga Supabase: concluida")
    else:
        print("\nDry-run concluido sem escrita no Supabase.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
