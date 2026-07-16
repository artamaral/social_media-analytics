import datetime
import os
import re
import time
import traceback

import requests

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 3))
CURSOR_KEY = "youtube_cursor"
MAX_ERROR_SUMMARY_LENGTH = 500

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def utc_now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()


def truncate_text(value, limit=MAX_ERROR_SUMMARY_LENGTH):
    if value is None:
        return None

    text = str(value).strip()
    if len(text) <= limit:
        return text

    return text[: limit - 3].rstrip() + "..."


def append_error_summary(current_summary, message):
    message = truncate_text(message, 160)
    if not message:
        return current_summary

    if not current_summary:
        return message

    entries = [item.strip() for item in current_summary.split(" | ") if item.strip()]
    if message in entries:
        return current_summary

    return truncate_text(current_summary + " | " + message)


def get_cursor():
    url = f"{SUPABASE_URL}/rest/v1/pipeline_state"
    params = {"select": "*", "id": f"eq.{CURSOR_KEY}"}

    res = requests.get(url, headers=HEADERS, params=params)
    print("Cursor status:", res.status_code)

    data = res.json()
    if data:
        return int(data[0]["value"])

    return 0


def save_cursor(value):
    url = f"{SUPABASE_URL}/rest/v1/pipeline_state"
    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates"

    payload = {"id": CURSOR_KEY, "value": str(value)}
    res = requests.post(url, headers=headers, json=payload)

    print("Save cursor:", res.status_code)
    if res.status_code >= 300:
        raise RuntimeError(f"save cursor failed: {res.status_code} {res.text}")


def create_heartbeat(payload):
    url = f"{SUPABASE_URL}/rest/v1/youtube_discovery_heartbeats"
    headers = HEADERS.copy()
    headers["Prefer"] = "return=representation"

    res = requests.post(url, headers=headers, json=payload)
    print("Heartbeat create:", res.status_code)

    if res.status_code >= 300:
        raise RuntimeError(f"heartbeat create failed: {res.status_code} {res.text}")

    data = res.json()
    if not data:
        raise RuntimeError("heartbeat create returned empty payload")

    return data[0]


def update_heartbeat(heartbeat_id, payload):
    if not heartbeat_id:
        return None

    url = f"{SUPABASE_URL}/rest/v1/youtube_discovery_heartbeats?id=eq.{heartbeat_id}"
    headers = HEADERS.copy()
    headers["Prefer"] = "return=representation"

    res = requests.patch(url, headers=headers, json=payload)
    print("Heartbeat update:", res.status_code)

    if res.status_code >= 300:
        raise RuntimeError(f"heartbeat update failed: {res.status_code} {res.text}")

    data = res.json()
    if not data:
        raise RuntimeError("heartbeat update returned empty payload")

    return data[0]


def fetch_creators():
    url = f"{SUPABASE_URL}/rest/v1/creators"
    params = {"select": "*", "platform": "eq.youtube"}

    res = requests.get(url, headers=HEADERS, params=params)
    print("Creators status:", res.status_code)

    if res.status_code != 200:
        print("Erro creators:", res.text)
        return []

    data = res.json()
    print(f"Creators total: {len(data)}")
    return data


def parse_duration(duration):
    try:
        pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
        match = pattern.match(duration)
        if not match:
            return 0

        h, m, s = match.groups()
        return int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0)
    except Exception:
        return 0


def get_channel_profile(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "snippet,contentDetails", "id": channel_id, "key": YOUTUBE_API_KEY}

    res = requests.get(url, params=params).json()
    items = res.get("items", [])
    if not items:
        return None

    item = items[0]
    thumbnails = item.get("snippet", {}).get("thumbnails", {})
    avatar_url = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
    )

    return {
        "playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
        "avatar_url": avatar_url,
    }


def update_creator_avatar(creator_id, avatar_url):
    if not creator_id or not avatar_url:
        return

    url = f"{SUPABASE_URL}/rest/v1/creators?id=eq.{creator_id}"
    headers = HEADERS.copy()
    headers["Prefer"] = "return=minimal"

    payload = {"avatar_url": avatar_url}
    res = requests.patch(url, headers=headers, json=payload)

    print("Avatar update:", res.status_code)
    if res.status_code >= 300:
        print("Avatar update error:", res.text)


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
            "key": YOUTUBE_API_KEY,
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
        batch_ids = video_ids[i : i + 50]
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch_ids),
            "key": YOUTUBE_API_KEY,
        }

        res = requests.get(url, params=params).json()

        for item in res.get("items", []):
            duration_raw = item["contentDetails"].get("duration", "PT0S")
            duration_sec = parse_duration(duration_raw)
            title = item["snippet"]["title"].lower()
            is_short = duration_sec <= 270 or "#shorts" in title

            all_data.append(
                {
                    "post_id": item["id"],
                    "title": item["snippet"]["title"],
                    "post_date": item["snippet"]["publishedAt"],
                    "views": int(item["statistics"].get("viewCount", 0)),
                    "likes": int(item["statistics"].get("likeCount", 0)),
                    "comments": int(item["statistics"].get("commentCount", 0)),
                    "duration": duration_sec,
                    "video_type": "short" if is_short else "long",
                }
            )

    return all_data


def upsert_posts(posts, creator_id):
    if not posts:
        return 0

    for post in posts:
        post["creator_id"] = creator_id

    url = f"{SUPABASE_URL}/rest/v1/posts?on_conflict=post_id"
    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"

    res = requests.post(url, headers=headers, json=posts)
    print("Upsert:", res.status_code)

    if res.status_code >= 300:
        raise RuntimeError(f"post upsert failed: {res.status_code} {res.text}")

    data = res.json()
    return len(data)


def run_pipeline():
    print("DISCOVERY PIPELINE INICIADO")

    heartbeat = create_heartbeat(
        {
            "status": "running",
            "batch_size": BATCH_SIZE,
            "processed_creators": 0,
            "attempted_creators": 0,
            "inserted_or_updated_posts": 0,
            "errors": 0,
        }
    )
    heartbeat_id = heartbeat["id"]
    heartbeat_update = {
        "batch_size": BATCH_SIZE,
        "processed_creators": 0,
        "attempted_creators": 0,
        "inserted_or_updated_posts": 0,
        "errors": 0,
        "error_summary": None,
    }
    final_status = "success"

    try:
        cursor = get_cursor()
        heartbeat_update["cursor_start"] = cursor
        print(f"Cursor atual: {cursor}")

        creators = fetch_creators()
        if not creators:
            print("Nenhum creator encontrado")
            final_status = "no_creators"
            heartbeat_update["total_creators"] = 0
            heartbeat_update["cursor_end"] = cursor
            return {"status": "no_creators"}

        total = len(creators)
        batch = creators[cursor : cursor + BATCH_SIZE]
        heartbeat_update["total_creators"] = total

        print(f"Total creators: {total}")
        print(f"Batch size: {BATCH_SIZE}")
        print(f"Creators no batch: {len(batch)}")

        if not batch:
            print("Fim da lista atingido, resetando cursor")
            save_cursor(0)
            heartbeat_update["cursor_end"] = 0
            return {"status": "completed", "processed": 0}

        processed = 0
        errors = 0
        inserted_or_updated_posts = 0

        for creator in batch:
            heartbeat_update["attempted_creators"] += 1
            creator_label = creator.get("username") or str(creator.get("id"))
            channel_id = creator.get("channel_id")

            if not channel_id:
                print("Creator sem channel_id, pulando...")
                errors += 1
                heartbeat_update["errors"] = errors
                final_status = "partial_error"
                heartbeat_update["error_summary"] = append_error_summary(
                    heartbeat_update.get("error_summary"),
                    f"{creator_label}: creator sem channel_id",
                )
                continue

            try:
                print("\n==================================================")
                print(f"Creator: {creator.get('username')}")
                print(f"Channel ID: {channel_id}")
                print(f"Creator ID (DB): {creator.get('id')}")
                print("==================================================")

                channel_profile = get_channel_profile(channel_id)
                playlist_id = channel_profile.get("playlist_id") if channel_profile else None
                avatar_url = channel_profile.get("avatar_url") if channel_profile else None

                if avatar_url:
                    update_creator_avatar(creator["id"], avatar_url)
                print(f"Playlist ID: {playlist_id}")

                if not playlist_id:
                    print("Playlist nao encontrada, pulando...")
                    errors += 1
                    heartbeat_update["errors"] = errors
                    final_status = "partial_error"
                    heartbeat_update["error_summary"] = append_error_summary(
                        heartbeat_update.get("error_summary"),
                        f"{creator_label}: playlist nao encontrada",
                    )
                    continue

                video_ids = get_videos_from_playlist(playlist_id)
                print(f"Videos encontrados: {len(video_ids)}")

                if not video_ids:
                    print("Nenhum video encontrado")
                    processed += 1
                    heartbeat_update["processed_creators"] = processed
                    continue

                videos_data = get_video_details(video_ids)
                print(f"Dados coletados: {len(videos_data)}")

                if not videos_data:
                    print("Nenhum detalhe retornado")
                    processed += 1
                    heartbeat_update["processed_creators"] = processed
                    continue

                touched_posts = upsert_posts(videos_data, creator["id"])
                inserted_or_updated_posts += touched_posts
                heartbeat_update["inserted_or_updated_posts"] = inserted_or_updated_posts

                print(f"Finalizado creator: {creator.get('username')}")

                processed += 1
                heartbeat_update["processed_creators"] = processed
                time.sleep(0.5)
            except Exception as exc:
                print("\nERRO NO CREATOR")
                print(f"Creator: {creator.get('username')}")
                print(f"Detalhe: {str(exc)}")
                traceback.print_exc()

                errors += 1
                heartbeat_update["errors"] = errors
                final_status = "partial_error"
                heartbeat_update["error_summary"] = append_error_summary(
                    heartbeat_update.get("error_summary"),
                    f"{creator_label}: {str(exc)}",
                )

        next_cursor = cursor + BATCH_SIZE
        if next_cursor >= total:
            next_cursor = 0

        save_cursor(next_cursor)
        heartbeat_update["cursor_end"] = next_cursor

        print("\n====================================")
        print(f"Processados: {processed}")
        print(f"Erros: {errors}")
        print(f"Proximo cursor: {next_cursor}")
        print("====================================")

        return {
            "processed": processed,
            "errors": errors,
            "cursor": cursor,
            "next_cursor": next_cursor,
            "total_creators": total,
            "inserted_or_updated_posts": inserted_or_updated_posts,
            "heartbeat_id": heartbeat_id,
        }
    except Exception as exc:
        final_status = "failed"
        heartbeat_update["error_summary"] = append_error_summary(
            heartbeat_update.get("error_summary"),
            f"fatal: {str(exc)}",
        )
        print("ERRO FATAL:", str(exc))
        traceback.print_exc()
        raise
    finally:
        try:
            if final_status == "success" and heartbeat_update.get("errors", 0) > 0:
                final_status = "partial_error"

            payload = heartbeat_update.copy()
            payload["status"] = final_status
            payload["finished_at"] = utc_now_iso()
            payload["error_summary"] = truncate_text(payload.get("error_summary"))
            update_heartbeat(heartbeat_id, payload)
        except Exception as heartbeat_error:
            print("ERRO AO FINALIZAR HEARTBEAT:", str(heartbeat_error))


def run(request):
    print("Cloud Run DISCOVERY iniciado")

    try:
        result = run_pipeline()
        return result
    except Exception as exc:
        print("ERRO:", str(exc))
        return {"error": str(exc)}
