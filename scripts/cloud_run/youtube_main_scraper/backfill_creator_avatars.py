import os
import time
import requests


YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 20))
CURSOR_KEY = os.environ.get("AVATAR_CURSOR_KEY", "youtube_avatar_cursor")
REFRESH_ALL = os.environ.get("REFRESH_ALL_AVATARS", "false").strip().lower() == "true"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def get_cursor():
    url = f"{SUPABASE_URL}/rest/v1/pipeline_state"
    params = {
        "select": "*",
        "id": f"eq.{CURSOR_KEY}",
    }

    res = requests.get(url, headers=HEADERS, params=params)
    print("Cursor status:", res.status_code)

    if res.status_code != 200:
        print("Cursor read error:", res.text)
        return 0

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
        "value": str(value),
    }

    res = requests.post(url, headers=headers, json=payload)
    print("Save cursor:", res.status_code)
    if res.status_code >= 300:
        print("Save cursor error:", res.text)


def fetch_creators():
    url = f"{SUPABASE_URL}/rest/v1/creators"
    params = {
        "select": "id,username,channel_id,avatar_url",
        "platform": "eq.youtube",
        "order": "id.asc",
    }

    if not REFRESH_ALL:
        params["avatar_url"] = "is.null"

    res = requests.get(url, headers=HEADERS, params=params)
    print("Creators status:", res.status_code)

    if res.status_code != 200:
        print("Creators fetch error:", res.text)
        return []

    data = res.json()
    print(f"Creators loaded: {len(data)}")
    return data


def get_channel_avatar(channel_id):
    if not channel_id:
        return None

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet",
        "id": channel_id,
        "key": YOUTUBE_API_KEY,
    }

    res = requests.get(url, params=params)
    if res.status_code != 200:
        print(f"Channel API error for {channel_id}: {res.status_code} {res.text}")
        return None

    data = res.json()
    items = data.get("items", [])
    if not items:
        return None

    thumbnails = items[0].get("snippet", {}).get("thumbnails", {})
    return (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
    )


def update_creator_avatar(creator_id, avatar_url):
    if not creator_id or not avatar_url:
        return False

    url = f"{SUPABASE_URL}/rest/v1/creators?id=eq.{creator_id}"
    headers = HEADERS.copy()
    headers["Prefer"] = "return=minimal"
    payload = {
        "avatar_url": avatar_url,
    }

    res = requests.patch(url, headers=headers, json=payload)
    print(f"Avatar update creator={creator_id}: {res.status_code}")

    if res.status_code >= 300:
        print("Avatar update error:", res.text)
        return False

    return True


def run_avatar_backfill():
    print("Avatar backfill started")

    cursor = get_cursor()
    print(f"Current cursor: {cursor}")

    creators = fetch_creators()
    if not creators:
        print("No creators found for avatar backfill")
        return {
            "status": "no_creators",
            "processed": 0,
            "updated": 0,
            "errors": 0,
        }

    total = len(creators)
    batch = creators[cursor:cursor + BATCH_SIZE]

    print(f"Total creators: {total}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Creators in batch: {len(batch)}")

    if not batch:
        print("End of list reached, resetting cursor")
        save_cursor(0)
        return {
            "status": "completed",
            "processed": 0,
            "updated": 0,
            "errors": 0,
            "next_cursor": 0,
        }

    processed = 0
    updated = 0
    errors = 0

    for creator in batch:
        try:
            creator_id = creator.get("id")
            username = creator.get("username")
            channel_id = creator.get("channel_id")

            print("\n====================================")
            print(f"Creator: {username}")
            print(f"Creator ID: {creator_id}")
            print(f"Channel ID: {channel_id}")
            print("====================================")

            if not channel_id:
                print("Creator without channel_id, skipping")
                continue

            avatar_url = get_channel_avatar(channel_id)
            if not avatar_url:
                print("Avatar not found in YouTube API")
                processed += 1
                time.sleep(0.2)
                continue

            if update_creator_avatar(creator_id, avatar_url):
                updated += 1

            processed += 1
            time.sleep(0.2)

        except Exception as exc:
            print("Avatar backfill error:", str(exc))
            errors += 1

    next_cursor = cursor + BATCH_SIZE
    if next_cursor >= total:
        next_cursor = 0

    save_cursor(next_cursor)

    print("\n====================================")
    print(f"Processed: {processed}")
    print(f"Updated: {updated}")
    print(f"Errors: {errors}")
    print(f"Next cursor: {next_cursor}")
    print("====================================")

    return {
        "processed": processed,
        "updated": updated,
        "errors": errors,
        "cursor": cursor,
        "next_cursor": next_cursor,
        "total_creators": total,
        "refresh_all": REFRESH_ALL,
    }


def run(request):
    print("Cloud Run avatar backfill started")
    try:
        return run_avatar_backfill()
    except Exception as exc:
        print("Avatar backfill fatal error:", str(exc))
        return {"error": str(exc)}


if __name__ == "__main__":
    result = run_avatar_backfill()
    print(result)
