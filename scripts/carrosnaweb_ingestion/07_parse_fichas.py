import argparse
import csv
import os

from src.parser import parse_ficha_tables, technical_rows_to_dicts


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RAW_DIR = os.path.join(SCRIPT_DIR, "data", "debug_html", "raw_html")
DEFAULT_OUTPUT_CSV = os.path.join(SCRIPT_DIR, "data", "processed", "ficha_tecnica.csv")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Parseia HTML bruto de fichas do Carros na Web em formato longo."
    )
    parser.add_argument(
        "--raw-dir",
        default=DEFAULT_RAW_DIR,
        help="Pasta com arquivos HTML salvos localmente.",
    )
    parser.add_argument(
        "--output-csv",
        default=DEFAULT_OUTPUT_CSV,
        help="CSV de saida com os campos tecnicos extraidos.",
    )
    return parser.parse_args()


def parse_html_files(raw_dir):
    all_rows = []

    for file_name in sorted(os.listdir(raw_dir)):
        if not file_name.lower().endswith(".html"):
            continue

        codigo_ficha = file_name[:-5]
        raw_html_path = os.path.join(raw_dir, file_name)
        ficha_url = f"https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo={codigo_ficha}"

        with open(raw_html_path, "r", encoding="utf-8", errors="ignore") as html_file:
            html = html_file.read()

        rows = parse_ficha_tables(
            html=html,
            ficha_url=ficha_url,
            codigo_ficha=codigo_ficha,
            collection_status="success",
            raw_html_path=raw_html_path,
        )
        print(f"[PARSE] codigo={codigo_ficha} rows={len(rows)}")
        all_rows.extend(rows)

    return all_rows


def save_csv(rows, output_csv):
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    dict_rows = technical_rows_to_dicts(rows)
    if not dict_rows:
        print("[OUTPUT] Nenhuma linha extraida.")
        return

    fieldnames = list(dict_rows[0].keys())
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in dict_rows:
            writer.writerow(row)

    print(f"[OUTPUT] csv={output_csv}")


def main():
    args = parse_args()
    rows = parse_html_files(args.raw_dir)
    save_csv(rows, args.output_csv)


if __name__ == "__main__":
    main()
