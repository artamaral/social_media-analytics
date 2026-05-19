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
