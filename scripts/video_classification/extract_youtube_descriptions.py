import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


REPO_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE_CSV = (
    REPO_DIR / "docs" / "external_data" / "33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv"
)
DEFAULT_OUTPUT = REPO_DIR / "tmp" / "youtube_descriptions_batch1.csv"
ENV_CANDIDATES = [
    REPO_DIR / ".env",
    REPO_DIR / "scripts" / "fenabrave_ingestion" / ".env",
]


FIELDS = [
    "post_id",
    "video_url",
    "description_status",
    "title_api",
    "channel_title",
    "published_at",
    "description",
    "description_length",
    "default_language",
    "error_message",
    "created_at",
]


def load_env_files():
    for path in ENV_CANDIDATES:
        if not path.exists():
            continue

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def require_youtube_key():
    load_env_files()
    key = os.environ.get("YOU_TUBE_API_KEY") or os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("Configure YOU_TUBE_API_KEY ou YOUTUBE_API_KEY")
    return key


def load_post_ids(sample_csv, post_ids, limit):
    selected = []
    for post_id in post_ids:
        post_id = post_id.strip()
        if post_id and post_id not in selected:
            selected.append(post_id)

    if selected:
        return selected[:limit]

    with sample_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            post_id = (row.get("post_id") or "").strip()
            if post_id and post_id not in selected:
                selected.append(post_id)
            if len(selected) >= limit:
                break

    return selected


def fetch_youtube_snippets(post_ids, api_key):
    snippets = {}
    for idx in range(0, len(post_ids), 50):
        chunk = post_ids[idx : idx + 50]
        params = urlencode(
            {
                "part": "snippet",
                "id": ",".join(chunk),
                "key": api_key,
            }
        )
        request = Request(
            f"https://www.googleapis.com/youtube/v3/videos?{params}",
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"YouTube API HTTP {exc.code}: {body[:800]}") from exc

        for item in payload.get("items", []):
            snippets[item["id"]] = item.get("snippet") or {}

    return snippets


def build_rows(post_ids, snippets):
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for post_id in post_ids:
        snippet = snippets.get(post_id)
        if snippet is None:
            rows.append(
                {
                    "post_id": post_id,
                    "video_url": f"https://www.youtube.com/watch?v={post_id}",
                    "description_status": "not_found",
                    "title_api": "",
                    "channel_title": "",
                    "published_at": "",
                    "description": "",
                    "description_length": 0,
                    "default_language": "",
                    "error_message": "video nao retornado pela YouTube Data API",
                    "created_at": created_at,
                }
            )
            continue

        description = snippet.get("description") or ""
        rows.append(
            {
                "post_id": post_id,
                "video_url": f"https://www.youtube.com/watch?v={post_id}",
                "description_status": "success",
                "title_api": snippet.get("title") or "",
                "channel_title": snippet.get("channelTitle") or "",
                "published_at": snippet.get("publishedAt") or "",
                "description": description,
                "description_length": len(description),
                "default_language": snippet.get("defaultLanguage")
                or snippet.get("defaultAudioLanguage")
                or "",
                "error_message": "",
                "created_at": created_at,
            }
        )
    return rows


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai descricoes de videos via YouTube Data API para CSV."
    )
    parser.add_argument("--sample-csv", type=Path, default=DEFAULT_SAMPLE_CSV)
    parser.add_argument("--post-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.limit < 1:
        raise RuntimeError("--limit deve ser >= 1")
    if not args.sample_csv.exists() and not args.post_id:
        raise RuntimeError(f"sample csv nao encontrado: {args.sample_csv}")

    api_key = require_youtube_key()
    post_ids = load_post_ids(args.sample_csv, args.post_id, args.limit)
    snippets = fetch_youtube_snippets(post_ids, api_key)
    rows = build_rows(post_ids, snippets)
    write_rows(args.output, rows)

    success = sum(1 for row in rows if row["description_status"] == "success")
    with_description = sum(1 for row in rows if int(row["description_length"]) > 0)
    print("Descricoes YouTube")
    print(f"- videos solicitados: {len(post_ids)}")
    print(f"- retornados pela API: {success}")
    print(f"- com descricao preenchida: {with_description}")
    print(f"- output: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        raise SystemExit(1)
