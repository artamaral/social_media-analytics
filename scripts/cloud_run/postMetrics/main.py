import os
from datetime import datetime, timezone

import requests

# ==============================
# CONFIG
# ==============================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


# ==============================
# STEP 1 - BUSCAR FILA
# ==============================

def fetch_queue():
    print("Buscando itens na fila...")

    url = f"{SUPABASE_URL}/rest/v1/v_post_update_queue_batch"
    print("Fonte da fila: v_post_update_queue_batch")

    params = {
        "select": "post_id",
    }

    response = requests.get(url, headers=HEADERS, params=params)

    print("Queue status:", response.status_code)

    if response.status_code != 200:
        print("Erro ao buscar queue:", response.text)
        return []

    data = response.json()
    print(f"Itens encontrados: {len(data)}")

    return data


# ==============================
# STEP 2 - IDS
# ==============================

def extract_ids(rows):
    return [r["post_id"] for r in rows]


# ==============================
# STEP 3 - YOUTUBE API
# ==============================

def fetch_youtube_stats(video_ids):
    print("Chamando YouTube API...")

    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(url, params=params)

    print("YouTube status:", response.status_code)

    if response.status_code != 200:
        print("Erro YouTube:", response.text)
        return None

    return response.json().get("items", [])


# ==============================
# STEP 4 - SEGREGAR IDS AUSENTES
# ==============================

def extract_returned_ids(items):
    return [video["id"] for video in items if video.get("id")]


def find_missing_video_ids(requested_ids, returned_ids):
    returned_set = set(returned_ids)
    seen_missing = set()
    missing_ids = []

    for video_id in requested_ids:
        if video_id in returned_set or video_id in seen_missing:
            continue

        seen_missing.add(video_id)
        missing_ids.append(video_id)

    return missing_ids


def register_post_collection_result(requested_ids, returned_ids):
    print("Registrando resultado da coleta no banco...")

    url = f"{SUPABASE_URL}/rest/v1/rpc/register_post_collection_result"
    payload = {
        "p_requested_ids": requested_ids,
        "p_returned_ids": returned_ids,
    }

    response = requests.post(url, headers=HEADERS, json=payload)

    print("Collection result:", response.status_code)

    if response.status_code >= 300:
        print("Response:", response.text)
        return []

    actions = response.json()
    missing_ids = [
        row["post_id"]
        for row in actions
        if row.get("action_taken") == "missing"
    ]

    if missing_ids:
        print(f"IDs nao retornados pela YouTube API: {missing_ids}")

    return actions


# ==============================
# STEP 5 - NORMALIZAR
# ==============================

def normalize(items):
    results = []

    for video in items:
        stats = video.get("statistics", {})

        results.append({
            "post_id": video["id"],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })

    return results


# ==============================
# STEP 6 - HISTORY
# ==============================

def insert_history(records):
    print("Inserindo historico batch...")

    url = f"{SUPABASE_URL}/rest/v1/post_metrics_history"

    response = requests.post(url, headers=HEADERS, json=records)

    print("History batch:", response.status_code)

    if response.status_code >= 300:
        print("Response:", response.text)


# ==============================
# PIPELINE
# ==============================

def run_pipeline():
    queue = fetch_queue()

    if not queue:
        print("Nada na fila")
        return

    ids = extract_ids(queue)

    yt_data = fetch_youtube_stats(ids)

    if yt_data is None:
        print("Falha global na YouTube API; nenhum ID sera segregado")
        return

    returned_ids = extract_returned_ids(yt_data)
    missing_ids = find_missing_video_ids(ids, returned_ids)

    register_post_collection_result(ids, returned_ids)

    if not yt_data:
        print("Sem dados do YouTube")
        return

    records = normalize(yt_data)

    # Regras de negocio ficam no banco:
    # - insert em post_metrics_history dispara sync_post_latest()
    # - insert em post_metrics_history dispara refresh_post_queue_on_metrics()
    # - register_post_collection_result() segrega IDs ausentes da YouTube API
    insert_history(records)

    print(f"Processados: {len(records)}")

    if missing_ids:
        print(f"Segregados para revisao: {len(missing_ids)}")


# ==============================
# CLOUD RUN ENTRYPOINT
# ==============================

def run(request):
    print("Cloud Run job iniciado")

    try:
        run_pipeline()
        return {"status": "success"}
    except Exception as e:
        print("ERRO:", str(e))
        return {"status": "error", "message": str(e)}
