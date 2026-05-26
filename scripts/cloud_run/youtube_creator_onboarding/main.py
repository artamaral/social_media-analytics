import os
import re

import requests


# ==============================
# CONFIG
# ==============================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
ONBOARDING_WORKER_TOKEN = os.environ.get("ONBOARDING_WORKER_TOKEN")


def parse_max_uploads():
    try:
        value = int(os.environ.get("MAX_UPLOADS", "50"))
    except ValueError:
        return 50

    return max(1, min(value, 50))


MAX_UPLOADS = parse_max_uploads()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


# ==============================
# RESPONSE HELPERS
# ==============================

def make_response(payload, status_code=200):
    return payload, status_code


def validate_config():
    missing = []

    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")

    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")

    if not YOUTUBE_API_KEY:
        missing.append("YOUTUBE_API_KEY")

    if not ONBOARDING_WORKER_TOKEN:
        missing.append("ONBOARDING_WORKER_TOKEN")

    return missing


def validate_token(request):
    token = request.headers.get("x-worker-token")
    return token and token == ONBOARDING_WORKER_TOKEN


def parse_creator_id(request):
    creator_id = request.args.get("creator_id")

    if not creator_id:
        payload = request.get_json(silent=True) or {}
        creator_id = payload.get("creator_id")

    try:
        creator_id = int(creator_id)
    except (TypeError, ValueError):
        return None

    if creator_id <= 0:
        return None

    return creator_id


# ==============================
# SUPABASE
# ==============================

def fetch_creator(creator_id):
    url = f"{SUPABASE_URL}/rest/v1/creators"
    params = {
        "select": "id,username,platform,channel_id,is_active",
        "id": f"eq.{creator_id}",
        "limit": "1",
    }

    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    print("Creator fetch status:", response.status_code)

    if response.status_code != 200:
        raise RuntimeError(
            "Erro ao buscar creator: "
            f"{response.status_code} - {response.text}"
        )

    data = response.json()

    if not data:
        return None

    return data[0]


def creator_has_posts(creator_id):
    url = f"{SUPABASE_URL}/rest/v1/posts"
    params = {
        "select": "post_id",
        "creator_id": f"eq.{creator_id}",
        "limit": "1",
    }

    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    print("Existing posts check status:", response.status_code)

    if response.status_code != 200:
        raise RuntimeError(
            "Erro ao checar posts existentes: "
            f"{response.status_code} - {response.text}"
        )

    return bool(response.json())


def upsert_posts(posts, creator_id):
    if not posts:
        return 0

    payload = []

    for post in posts:
        row = dict(post)
        row["creator_id"] = creator_id
        payload.append(row)

    url = f"{SUPABASE_URL}/rest/v1/posts?on_conflict=post_id"

    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates"

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    print("Posts upsert status:", response.status_code)

    if response.status_code >= 300:
        raise RuntimeError(
            "Erro ao fazer upsert de posts: "
            f"{response.status_code} - {response.text}"
        )

    return len(payload)


# ==============================
# YOUTUBE
# ==============================

def parse_duration(duration):
    try:
        pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
        match = pattern.match(duration)

        if not match:
            return 0

        hours, minutes, seconds = match.groups()

        return (
            int(hours or 0) * 3600
            + int(minutes or 0) * 60
            + int(seconds or 0)
        )
    except (TypeError, ValueError):
        return 0


def get_upload_playlist_id(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(url, params=params, timeout=30)
    print("YouTube channel status:", response.status_code)

    if response.status_code != 200:
        raise RuntimeError(
            "Erro ao buscar canal no YouTube: "
            f"{response.status_code} - {response.text}"
        )

    items = response.json().get("items", [])

    if not items:
        return None

    return (
        items[0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )


def get_videos_from_playlist(playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"

    video_ids = []
    next_page = None

    while True:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": min(MAX_UPLOADS, 50),
            "pageToken": next_page,
            "key": YOUTUBE_API_KEY,
        }

        response = requests.get(url, params=params, timeout=30)
        print("YouTube playlist status:", response.status_code)

        if response.status_code != 200:
            raise RuntimeError(
                "Erro ao buscar uploads do canal: "
                f"{response.status_code} - {response.text}"
            )

        data = response.json()

        for item in data.get("items", []):
            video_id = (
                item.get("snippet", {})
                .get("resourceId", {})
                .get("videoId")
            )

            if video_id:
                video_ids.append(video_id)

            if len(video_ids) >= MAX_UPLOADS:
                return video_ids[:MAX_UPLOADS]

        next_page = data.get("nextPageToken")

        if not next_page:
            break

    return video_ids[:MAX_UPLOADS]


def get_video_details(video_ids):
    if not video_ids:
        return []

    url = "https://www.googleapis.com/youtube/v3/videos"
    posts = []

    for index in range(0, len(video_ids), 50):
        batch_ids = video_ids[index:index + 50]
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch_ids),
            "key": YOUTUBE_API_KEY,
        }

        response = requests.get(url, params=params, timeout=30)
        print("YouTube videos status:", response.status_code)

        if response.status_code != 200:
            raise RuntimeError(
                "Erro ao buscar detalhes dos videos: "
                f"{response.status_code} - {response.text}"
            )

        for item in response.json().get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            duration_sec = parse_duration(content_details.get("duration", "PT0S"))
            title = snippet.get("title", "")
            is_short = duration_sec <= 270 or "#shorts" in title.lower()

            posts.append({
                "post_id": item.get("id"),
                "title": title,
                "post_date": snippet.get("publishedAt"),
                "views": int(statistics.get("viewCount", 0)),
                "likes": int(statistics.get("likeCount", 0)),
                "comments": int(statistics.get("commentCount", 0)),
                "duration": duration_sec,
                "video_type": "short" if is_short else "long",
            })

    return [post for post in posts if post.get("post_id")]


# ==============================
# ONBOARDING FLOW
# ==============================

def validate_creator_for_onboarding(creator):
    if not creator:
        return "creator_not_found"

    if creator.get("platform") != "youtube":
        return "creator_not_youtube"

    if creator.get("is_active") is False:
        return "creator_inactive"

    if not creator.get("channel_id"):
        return "missing_channel_id"

    return None


def run_onboarding(creator_id):
    print("Starting creator onboarding discovery")
    print("Creator ID:", creator_id)

    creator = fetch_creator(creator_id)
    validation_error = validate_creator_for_onboarding(creator)

    if validation_error:
        return {
            "status": "error",
            "creator_id": creator_id,
            "error": validation_error,
            "processed_posts": 0,
            "skipped": False,
            "error_details": [{
                "creator_id": creator_id,
                "error": validation_error,
            }],
        }, 400

    if creator_has_posts(creator_id):
        return {
            "status": "skipped",
            "creator_id": creator_id,
            "username": creator.get("username"),
            "processed_posts": 0,
            "skipped": True,
            "reason": "creator_already_has_posts",
            "error_details": [],
        }, 200

    playlist_id = get_upload_playlist_id(creator["channel_id"])

    if not playlist_id:
        return {
            "status": "error",
            "creator_id": creator_id,
            "username": creator.get("username"),
            "processed_posts": 0,
            "skipped": False,
            "error": "upload_playlist_not_found",
            "error_details": [{
                "creator_id": creator_id,
                "channel_id": creator.get("channel_id"),
                "error": "upload_playlist_not_found",
            }],
        }, 404

    video_ids = get_videos_from_playlist(playlist_id)
    posts = get_video_details(video_ids)
    processed_posts = upsert_posts(posts, creator_id)

    return {
        "status": "processed",
        "creator_id": creator_id,
        "username": creator.get("username"),
        "processed_posts": processed_posts,
        "discovered_video_ids": len(video_ids),
        "skipped": False,
        "error_details": [],
    }, 200


# ==============================
# ENTRYPOINT
# ==============================

def run(request):
    print("Cloud Run creator onboarding discovery started")

    missing_config = validate_config()

    if missing_config:
        return make_response({
            "status": "error",
            "error": "missing_config",
            "missing": missing_config,
        }, 500)

    if not validate_token(request):
        return make_response({
            "status": "error",
            "error": "unauthorized",
        }, 401)

    creator_id = parse_creator_id(request)

    if not creator_id:
        return make_response({
            "status": "error",
            "error": "invalid_creator_id",
        }, 400)

    try:
        payload, status_code = run_onboarding(creator_id)
        return make_response(payload, status_code)
    except Exception as exc:
        print("Unhandled onboarding error:", str(exc))

        return make_response({
            "status": "error",
            "creator_id": creator_id,
            "error": str(exc),
            "processed_posts": 0,
            "skipped": False,
            "error_details": [{
                "creator_id": creator_id,
                "error": str(exc),
            }],
        }, 500)
