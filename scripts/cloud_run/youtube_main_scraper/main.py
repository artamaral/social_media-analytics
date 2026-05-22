import os
import requests
import time
import re

# ==============================
# 🔧 CONFIG
# ==============================

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 3))

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

CURSOR_KEY = "youtube_cursor"

# ==============================
# 🔄 CURSOR
# ==============================

def get_cursor():
    url = f"{SUPABASE_URL}/rest/v1/pipeline_state"

    params = {
        "select": "*",
        "id": f"eq.{CURSOR_KEY}"
    }

    res = requests.get(url, headers=HEADERS, params=params)

    print("📡 Cursor status:", res.status_code)

    data = res.json()

    if data:
        return int(data[0]["value"])

    return 0


def save_cursor(value):
    url = f"{SUPABASE_URL}/rest/v1/pipeline_state"

    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates"

    payload = {
        "id": CURSOR_KEY,
        "value": str(value)
    }

    res = requests.post(url, headers=headers, json=payload)

    print("📡 Save cursor:", res.status_code)


# ==============================
# 👥 CREATORS
# ==============================

def fetch_creators():
    url = f"{SUPABASE_URL}/rest/v1/creators"

    params = {
        "select": "*",
        "platform": "eq.youtube"
    }

    res = requests.get(url, headers=HEADERS, params=params)

    print("📡 Creators status:", res.status_code)

    if res.status_code != 200:
        print("❌ Erro creators:", res.text)
        return []

    data = res.json()

    print(f"📦 Creators total: {len(data)}")

    return data


# ==============================
# 🎥 YOUTUBE
# ==============================

def parse_duration(duration):
    try:
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration)
        if not match:
            return 0
        h, m, s = match.groups()
        return int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0)
    except:
        return 0


def parse_int(value):
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_channel_details(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"

    params = {
        "part": "contentDetails,statistics",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    print("📡 Channel details status:", response.status_code)

    if response.status_code != 200:
        print("❌ Erro channel details:", response.text)
        return None

    res = response.json()

    items = res.get("items", [])

    if not items:
        return None

    item = items[0]
    statistics = item.get("statistics", {})

    return {
        "upload_playlist_id": (
            item.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        ),
        "followers": parse_int(statistics.get("subscriberCount")),
        "channel_view_count": parse_int(statistics.get("viewCount")),
        "channel_video_count": parse_int(statistics.get("videoCount")),
        "hidden_subscriber_count": statistics.get("hiddenSubscriberCount"),
    }


def get_videos_from_playlist(playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"

    videos = []
    next_page = None

    while True:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "pageToken": next_page,
            "key": YOUTUBE_API_KEY
        }

        res = requests.get(url, params=params).json()

        for item in res.get("items", []):
            videos.append(item["snippet"]["resourceId"]["videoId"])

        next_page = res.get("nextPageToken")
        if not next_page:
            break

    return videos[:50]


def get_video_details(video_ids):
    url = "https://www.googleapis.com/youtube/v3/videos"

    all_data = []

    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]

        params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch_ids),
            "key": YOUTUBE_API_KEY
        }

        res = requests.get(url, params=params).json()

        for item in res.get("items", []):
            duration_raw = item["contentDetails"].get("duration", "PT0S")
            duration_sec = parse_duration(duration_raw)
            title = item["snippet"]["title"].lower()

            is_short = duration_sec <= 270 or "#shorts" in title

            all_data.append({
                "post_id": item["id"],
                "title": item["snippet"]["title"],
                "post_date": item["snippet"]["publishedAt"],
                "views": int(item["statistics"].get("viewCount", 0)),
                "likes": int(item["statistics"].get("likeCount", 0)),
                "comments": int(item["statistics"].get("commentCount", 0)),
                "duration": duration_sec,
                "video_type": "short" if is_short else "long"
            })

    return all_data


# ==============================
# 💾 UPSERT POSTS
# ==============================

def upsert_posts(posts, creator_id):
    if not posts:
        return

    for post in posts:
        post["creator_id"] = creator_id

    url = f"{SUPABASE_URL}/rest/v1/posts?on_conflict=post_id"

    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates"

    res = requests.post(url, headers=headers, json=posts)

    print("📡 Upsert:", res.status_code)

    if res.status_code >= 300:
        print("❌ Response:", res.text)


def insert_creator_metrics_snapshot(creator_id, channel_details):
    if not channel_details:
        return

    payload = {
        "creator_id": creator_id,
        "followers": channel_details.get("followers"),
        "channel_view_count": channel_details.get("channel_view_count"),
        "channel_video_count": channel_details.get("channel_video_count"),
        "hidden_subscriber_count": channel_details.get("hidden_subscriber_count"),
        "source": "youtube_channels_api"
    }

    url = f"{SUPABASE_URL}/rest/v1/creator_metrics_history"

    res = requests.post(url, headers=HEADERS, json=payload)

    print("📡 Creator metrics snapshot:", res.status_code)

    if res.status_code >= 300:
        print("❌ Response:", res.text)
        raise RuntimeError(
            "Falha ao inserir snapshot em creator_metrics_history: "
            f"{res.status_code} - {res.text}"
        )


# ==============================
# 🚀 PIPELINE
# ==============================

def run_pipeline():
    print("🚀 DISCOVERY PIPELINE INICIADO")

    # ==============================
    # 🔄 CURSOR
    # ==============================
    cursor = get_cursor()
    print(f"📍 Cursor atual: {cursor}")

    # ==============================
    # 👥 BUSCAR CREATORS
    # ==============================
    creators = fetch_creators()

    if not creators:
        print("❌ Nenhum creator encontrado")
        return {"status": "no_creators"}

    total = len(creators)
    batch = creators[cursor:cursor + BATCH_SIZE]

    print(f"📊 Total creators: {total}")
    print(f"🎯 Batch size: {BATCH_SIZE}")
    print(f"📦 Creators no batch: {len(batch)}")

    # ==============================
    # 🛑 FIM DA LISTA
    # ==============================
    if not batch:
        print("⚠️ Fim da lista atingido — resetando cursor")
        save_cursor(0)

        return {
            "status": "completed",
            "processed": 0
        }

    processed = 0
    errors = 0
    error_details = []

    # ==============================
    # 🔁 LOOP PRINCIPAL
    # ==============================
    for creator in batch:
        try:
            print("\n==================================================")
            print(f"👤 Creator: {creator.get('username')}")
            print(f"🆔 Channel ID: {creator.get('channel_id')}")
            print(f"📍 Creator ID (DB): {creator.get('id')}")
            print("==================================================")

            channel_id = creator.get("channel_id")

            if not channel_id:
                print("⚠️ Creator sem channel_id, pulando...")
                continue

            # ==============================
            # 📺 CANAL
            # ==============================
            channel_details = get_channel_details(channel_id)

            if not channel_details:
                print("⚠️ Dados do canal não encontrados, pulando...")
                continue

            insert_creator_metrics_snapshot(creator["id"], channel_details)

            playlist_id = channel_details.get("upload_playlist_id")
            print(f"📺 Playlist ID: {playlist_id}")

            if not playlist_id:
                print("⚠️ Playlist não encontrada, pulando...")
                continue

            # ==============================
            # 🎬 VIDEOS
            # ==============================
            video_ids = get_videos_from_playlist(playlist_id)
            print(f"🎬 Vídeos encontrados: {len(video_ids)}")

            if not video_ids:
                print("⚠️ Nenhum vídeo encontrado")
                continue

            # ==============================
            # 📊 DETALHES
            # ==============================
            videos_data = get_video_details(video_ids)
            print(f"📊 Dados coletados: {len(videos_data)}")

            if not videos_data:
                print("⚠️ Nenhum detalhe retornado")
                continue

            # ==============================
            # 💾 UPSERT
            # ==============================
            upsert_posts(videos_data, creator["id"])

            print(f"✅ Finalizado creator: {creator.get('username')}")

            processed += 1

            # evita rate limit / throttling
            time.sleep(0.5)

        except Exception as e:
            print("\n❌ ERRO NO CREATOR")
            print(f"👤 Creator: {creator.get('username')}")
            print(f"❌ Detalhe: {str(e)}")

            error_details.append({
                "creator_id": creator.get("id"),
                "username": creator.get("username"),
                "channel_id": creator.get("channel_id"),
                "error": str(e),
            })

            import traceback
            traceback.print_exc()

            errors += 1

    # ==============================
    # 🔄 ATUALIZA CURSOR
    # ==============================
    next_cursor = cursor + BATCH_SIZE

    if next_cursor >= total:
        next_cursor = 0

    save_cursor(next_cursor)

    print("\n====================================")
    print(f"✅ Processados: {processed}")
    print(f"❌ Erros: {errors}")
    print(f"➡️ Próximo cursor: {next_cursor}")
    print("====================================")

    return {
        "processed": processed,
        "errors": errors,
        "error_details": error_details[:10],
        "cursor": cursor,
        "next_cursor": next_cursor,
        "total_creators": total
    }


# ==============================
# ☁️ ENTRYPOINT (IGUAL AO SEU FUNCIONANDO)
# ==============================

def run(request):
    print("🚀 Cloud Run DISCOVERY iniciado")

    try:
        result = run_pipeline()
        return result
    except Exception as e:
        print("❌ ERRO:", str(e))
        return {"error": str(e)}
