import yt_dlp
import csv
import math
import time

channel_url = "https://www.youtube.com/playlist?list=UUtOcDBKgyr-f50SgbMErFkQ"
chunk_size = 100  # Max rows per file

ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'force_generic_extractor': False,
    'skip_download': True,
    'no_warnings': True,   # 👈 ADD THIS
}

video_urls = []

print(f"📡 Fetching video URLs from: {channel_url}")

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(channel_url, download=False)
    entries = info.get('entries', [])
    print(f"🎞 Found {len(entries)} videos.\n")

    for entry in entries:
        video_id = entry.get('id')
        url = f"https://www.youtube.com/watch?v={video_id}"
        video_urls.append(url)

# Split into chunks
num_chunks = math.ceil(len(video_urls) / chunk_size)
chunks = [video_urls[i * chunk_size:(i + 1) * chunk_size] for i in range(num_chunks)]

# yt-dlp options for metadata extraction
ydl_opts_meta = {
    'quiet': True,
    'skip_download': True,
    'no_warnings': True,   # 👈 ADD THIS
}

for i, chunk in enumerate(chunks):
    input_label = f"Video URL {i + 1}.csv"
    output_file = f"video metadata {i + 1}.csv"

    print(f"\n🔄 Processing chunk {i + 1}/{num_chunks} → {output_file}")

    video_data = []
    start_time = time.time()
    total = len(chunk)

    with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
        for j, url in enumerate(chunk, start=1):
            try:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "N/A")
                upload_date = info.get("upload_date", "")
                views = info.get("view_count", 0)

                if upload_date and len(upload_date) == 8:
                    upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

                video_data.append({
                    "Video Title": title,
                    "Video Post Date": upload_date,
                    "Video URL": url,
                    "Video Play Count": views
                })

                # ETA estimate
                elapsed = time.time() - start_time
                avg_time = elapsed / j
                eta = avg_time * (total - j)
                eta_m, eta_s = divmod(int(eta), 60)
                eta_str = f"{eta_m}m {eta_s}s" if eta_m else f"{eta_s}s"
                print(f"[{j}/{total}] ✅ {title} — ETA: {eta_str}")

            except Exception as e:
                print(f"[{j}/{total}] ❌ Error for {url}: {e}")

    with open(output_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Video Title", "Video Post Date", "Video URL", "Video Play Count"])
        writer.writeheader()
        writer.writerows(video_data)

    print(f"📄 Done: {output_file} ({len(video_data)} videos)")

print(f"\n📁 All done! Total metadata files created: {num_chunks}")