import requests
import csv
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────
API_KEY = "AIzaSyByis4jQwOwMZ692Jk9YCoWzXUEcAfJmQo"
CHANNEL_ID = "UCtOcDBKgyr-f50SgbMErFkQ"
CHUNK_SIZE = 100
# ──────────────────────────────────────────────────────────────────────────────


def fetch_all_video_ids(api_key, channel_id):
    """Use YouTube Data API v3 to paginate through all uploads."""
    uploads_playlist_id = "UU" + channel_id[2:]  # UC... → UU...
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": 50,
        "key": api_key,
    }

    video_ids = []
    page = 1

    print("📡 Fetching video IDs via Data API v3...")
    while True:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(f"API error: {data['error']['message']}")

        items = data.get("items", [])
        for item in items:
            vid_id = item["contentDetails"]["videoId"]
            video_ids.append(vid_id)

        print(f"  Page {page}: fetched {len(items)} IDs (total so far: {len(video_ids)})")
        page += 1

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

        params["pageToken"] = next_page_token

    print(f"🎞  Total videos found: {len(video_ids)}\n")
    return video_ids


def fetch_metadata(api_key, video_ids):
    """Fetch title, publish date and view count directly from YouTube Data API v3."""
    url = "https://www.googleapis.com/youtube/v3/videos"
    video_data = []
    total = len(video_ids)
    start_time = time.time()

    # videos.list accepts up to 50 video IDs per request
    for batch_start in range(0, total, 50):
        batch = video_ids[batch_start:batch_start + 50]
        params = {
            "part": "snippet,statistics",
            "id": ",".join(batch),
            "key": api_key,
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(f"API error: {data['error']['message']}")

        returned = {item["id"]: item for item in data.get("items", [])}

        for offset, vid_id in enumerate(batch, start=1):
            j = batch_start + offset
            item = returned.get(vid_id)
            video_url = f"https://www.youtube.com/watch?v={vid_id}"

            if not item:
                print(f"[{j}/{total}] ❌ Skipped {video_url}: unavailable/private/deleted")
                continue

            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})

            title = snippet.get("title", "N/A")
            published_at = snippet.get("publishedAt", "")
            upload_date = published_at[:10] if published_at else ""
            views = int(statistics.get("viewCount", 0))

            video_data.append({
                "Video Title": title,
                "Video Post Date": upload_date,
                "Video URL": video_url,
                "Video Play Count": views,
            })

            elapsed = time.time() - start_time
            avg_time = elapsed / j
            eta = avg_time * (total - j)
            eta_m, eta_s = divmod(int(eta), 60)
            eta_str = f"{eta_m}m {eta_s}s" if eta_m else f"{eta_s}s"
            print(f"[{j}/{total}] ✅ {title} — ETA: {eta_str}")

        batch_no = batch_start // 50 + 1
        print(f"    API batch {batch_no} complete ({min(batch_start + 50, total)}/{total} IDs processed)")

    return video_data


def write_chunks(video_data, chunk_size):
    chunks = [video_data[i:i + chunk_size] for i in range(0, len(video_data), chunk_size)]

    for i, chunk in enumerate(chunks, start=1):
        output_file = f"video metadata {i}.csv"
        with open(output_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["Video Title", "Video Post Date", "Video URL", "Video Play Count"],
            )
            writer.writeheader()
            writer.writerows(chunk)
        print(f"📄 Written: {output_file} ({len(chunk)} videos)")

    print(f"\n📁 Done. {len(chunks)} file(s), {len(video_data)} total videos.")


if __name__ == "__main__":
    video_ids = fetch_all_video_ids(API_KEY, CHANNEL_ID)
    video_data = fetch_metadata(API_KEY, video_ids)
    write_chunks(video_data, CHUNK_SIZE)
