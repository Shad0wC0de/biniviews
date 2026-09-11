import yt_dlp
import csv
import math
import time

CHANNEL_URL = "https://www.youtube.com/channel/UCtOcDBKgyr-f50SgbMErFkQ/videos"
CHUNK_SIZE = 100

def fetch_video_urls(channel_url):
    ydl_opts = {
        'quiet': False,
        'extract_flat': True,
        'skip_download': True,
        'ignoreerrors': True,
        'playlistend': 99999,
        'cookiesfrombrowser': ('firefox',),
        'extractor_args': {
            'youtube': {
                'skip': ['authcheck'],
            }
        },
    }

    print(f"📡 Fetching video list from: {channel_url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    if not info:
        raise RuntimeError("❌ yt-dlp returned nothing. Check your URL or cookies.")

    entries = info.get('entries', [])
    if not entries:
        raise RuntimeError("❌ No entries found. Channel may be private or URL is wrong.")

    urls = []
    for entry in entries:
        if entry and entry.get('id'):
            urls.append(f"https://www.youtube.com/watch?v={entry['id']}")

    print(f"🎞  Found {len(urls)} videos.\n")
    return urls


def fetch_metadata(urls):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'cookiesfrombrowser': ('firefox',),
        'sleep_interval_requests': 1,
    }

    video_data = []
    total = len(urls)
    start_time = time.time()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for j, url in enumerate(urls, start=1):
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
    num_chunks = len(chunks)

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

    print(f"\n📁 Done. {num_chunks} file(s) created, {len(video_data)} total videos.")


if __name__ == "__main__":
    urls = fetch_video_urls(CHANNEL_URL)
    video_data = fetch_metadata(urls)
    write_chunks(video_data, CHUNK_SIZE)