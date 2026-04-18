import requests
import os
from datetime import datetime, UTC

# ==============================
# 🔧 CONFIG
# ==============================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ==============================
# 🔍 STEP 1 — BUSCAR FILA
# ==============================

def fetch_queue():
    print("🔍 Buscando itens na fila...")

    url = f"{SUPABASE_URL}/rest/v1/v_post_update_queue_batch"

    params = {
        "select": "post_id"
    }

    response = requests.get(url, headers=HEADERS, params=params)

    print("📡 Queue status:", response.status_code)

    if response.status_code != 200:
        print("❌ Erro ao buscar queue:", response.text)
        return []

    data = response.json()
    print(f"📦 Itens encontrados: {len(data)}")

    return data


# ==============================
# 🎯 STEP 2 — IDS
# ==============================

def extract_ids(rows):
    return [r["post_id"] for r in rows]


# ==============================
# 🎥 STEP 3 — YOUTUBE API
# ==============================

def fetch_youtube_stats(video_ids):
    print("🌐 Chamando YouTube API...")

    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)

    print("📡 YouTube status:", response.status_code)

    if response.status_code != 200:
        print("❌ Erro YouTube:", response.text)
        return []

    return response.json().get("items", [])


# ==============================
# ⚙️ STEP 4 — NORMALIZAR
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
            "collected_at": datetime.now(UTC).isoformat()
        })

    return results


# ==============================
# 📝 STEP 5 — HISTORY
# ==============================

def insert_history(records):
    print("📝 Inserindo histórico batch...")

    url = f"{SUPABASE_URL}/rest/v1/post_metrics_history"

    response = requests.post(url, headers=HEADERS, json=records)

    print("📡 History batch:", response.status_code)

    if response.status_code >= 300:
        print("❌ Response:", response.text)


# ==============================
# 🚀 PIPELINE
# ==============================

def run_pipeline():
    queue = fetch_queue()

    if not queue:
        print("⚠️ Nada na fila")
        return

    ids = extract_ids(queue)

    yt_data = fetch_youtube_stats(ids)

    if not yt_data:
        print("⚠️ Sem dados do YouTube")
        return

    records = normalize(yt_data)

    # Regras de negócio ficam no banco:
    # - insert em post_metrics_history dispara sync_post_latest()
    # - insert em post_metrics_history dispara refresh_post_queue_on_metrics()
    insert_history(records)

    print(f"✅ Processados: {len(records)}")


# ==============================
# ☁️ CLOUD RUN ENTRYPOINT
# ==============================

def run(request):
    print("🚀 Cloud Run job iniciado")

    try:
        run_pipeline()
        return {"status": "success"}
    except Exception as e:
        print("❌ ERRO:", str(e))
        return {"status": "error", "message": str(e)}
