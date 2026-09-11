import requests
import yt_dlp
import csv
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────
API_KEY = "AIzaSyByis4jQwOwMZ692Jk9YCoWzXUEcAfJmQo"
CHANNEL_ID = "UCtOcDBKgyr-f50SgbMErFkQ"
CHUNK_SIZE = 100
# ──────────────────────────────────────────────────────────────────────────────


def fetch_all_video_ids(api_key, channel_id):
    """Use Data API v3 to reliably paginate through all uploads."""
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

    print(f"📡 Fetching video IDs via Data API v3...")
    while True:
        response = requests.get(url, params=params)
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


def fetch_metadata(video_ids):
    """Use yt-dlp to fetch metadata for each video ID."""
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'cookiesfrombrowser': ('firefox',),
    }

    video_data = []
    total = len(video_ids)
    start_time = time.time()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for j, vid_id in enumerate(video_ids, start=1):
            url = f"https://www.youtube.com/watch?v={vid_id}"
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise ValueError("Empty response")

                title = info.get("title", "N/A")
                upload_date = info.get("upload_date", "")
                views = info.get("view_count", 0)

                if upload_date and len(upload_date) == 8:
                    upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

                video_data.append({
                    "Video Title": title,
                    "Video Post Date": upload_date,
                    "Video URL": url,
                    "Video Play Count": views,
                })

                elapsed = time.time() - start_time
                avg_time = elapsed / j
                eta = avg_time * (total - j)
                eta_m, eta_s = divmod(int(eta), 60)
                eta_str = f"{eta_m}m {eta_s}s" if eta_m else f"{eta_s}s"
                print(f"[{j}/{total}] ✅ {title} — ETA: {eta_str}")

            except Exception as e:
                print(f"[{j}/{total}] ❌ Skipped {url}: {e}")

    return video_data


def write_chunks(video_data, chunk_size):
    chunks = [video_data[i:i + chunk_size] for i in range(0, len(video_data), chunk_size)]

    for i, chunk in enumerate(chunks, start=1):
        output_file = f"video metadata {i}.csv"
        with open(output_file, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["Video Title", "Video Post Date", "Video URL", "Video Play Count"]
            )
            writer.writeheader()
            writer.writerows(chunk)
        print(f"📄 Written: {output_file} ({len(chunk)} videos)")

    print(f"\n📁 Done. {len(chunks)} file(s), {len(video_data)} total videos.")


if __name__ == "__main__":
    video_ids = fetch_all_video_ids(API_KEY, CHANNEL_ID)
    video_data = fetch_metadata(video_ids)
    write_chunks(video_data, CHUNK_SIZE)