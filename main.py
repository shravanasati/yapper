import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from urllib.parse import urlparse

from download_video import download_video
from highlights import HighlightExtractor, IDHighlightSegment
from subtitles import chunk_subtitles, download_subtitles, srt_time_to_seconds
from video_gen import generate_short_clip

GAMEPLAYS_PATH = "./gameplays"
INPUT_VID_PATH = os.path.join("./input", "clip.webm")
INPUT_VID_WO_EXT = os.path.join("./input", "clip")
OUTPUT_VIDS_PATH = "./output"

MAX_HIGHLIGHT_WORKERS = 10
MAX_VIDEO_WORKERS = 4


def get_yt_video_id(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        raise ValueError(f"{url=} doesnt have a query param")

    query_params = {
        item.split("=")[0]: item.split("=")[1] for item in parsed.query.split("&")
    }

    return query_params["v"]


def generate_short(segment: IDHighlightSegment):
    print(f"==> Generating clip for {segment.title}")
    generate_short_clip(
        INPUT_VID_PATH,
        os.path.join(GAMEPLAYS_PATH, random.choice(os.listdir(GAMEPLAYS_PATH))),
        os.path.join(OUTPUT_VIDS_PATH, f"out_{segment.id_}.mp4"),
        srt_time_to_seconds(segment.start_time),
        srt_time_to_seconds(segment.end_time),
    )


if __name__ == "__main__":
    VIDEO_URL = sys.argv[1]
    VIDEO_ID = get_yt_video_id(VIDEO_URL)
    print(f"==> Processing video with {VIDEO_ID=}...")
    NO_AUTO_SUBS = "--no-auto-subs" in sys.argv

    SUBTITLES_FILE = f"subs_{VIDEO_ID}.srt"
    HIGHLIGHTS_FILE = f"highlights_{VIDEO_ID}.json"

    if not os.path.exists(SUBTITLES_FILE):
        download_subtitles(VIDEO_URL, SUBTITLES_FILE, "en", not NO_AUTO_SUBS)
    else:
        print("==> Subtitles exist, skipping downloading them.")

    subtitle_chunks = chunk_subtitles(SUBTITLES_FILE)

    extract_highlights = True
    if os.path.exists(HIGHLIGHTS_FILE):
        try:
            with open(HIGHLIGHTS_FILE) as h:
                segments = [[IDHighlightSegment(**s) for s in json.load(h)]]
            extract_highlights = False
            print("==> Found cached highlights, skipping extraction.")
        except Exception as e:
            print(e)
            print("==> Failed to load cached highlights, fetching them again.")

    if extract_highlights:
        he = HighlightExtractor()
        with ThreadPoolExecutor(max_workers=min(MAX_HIGHLIGHT_WORKERS, len(subtitle_chunks))) as pool:
            segments = list(pool.map(he.extract, subtitle_chunks))

    flattened_segments = [s for ss in segments for s in ss]
    print(f"==> Found {len(flattened_segments)} segments, caching them.")
    with open(HIGHLIGHTS_FILE, "w") as f:
        f.write(json.dumps([fs.model_dump() for fs in flattened_segments]))

    if os.path.exists(INPUT_VID_PATH):
        print("==> Skipping downloading video as it already exists.")
    else:
        print("==> Downloading video...")
        download_video(VIDEO_URL, INPUT_VID_WO_EXT)

    os.makedirs(OUTPUT_VIDS_PATH, exist_ok=True)
    with ProcessPoolExecutor(max_workers=min(MAX_VIDEO_WORKERS, len(flattened_segments))) as pool:
        pool.map(generate_short, flattened_segments)

    # os.remove("./input/clip.webm")
    # os.remove("./highlights.json")
    # os.remove("./subs.srt")
