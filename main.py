import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from urllib.parse import urlparse

from download_video import download_video
from highlights import HighlightExtractor, IDHighlightSegment, obey_valid_length
from publish import upload_short
from subtitles import chunk_subtitles, download_subtitles
from video_gen import ShortGenerator

GAMEPLAYS_PATH = "./gameplays"
INPUT_VID_PATH = ""
INPUT_VID_WO_EXT = ""
OUTPUT_VIDS_DIR = ""

MAX_HIGHLIGHT_WORKERS = 10
MAX_VIDEO_WORKERS = 4
MAX_PUBLISH_WORKERS = 4


def get_yt_video_id(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        raise ValueError(f"{url=} doesnt have a query param")

    query_params = {
        item.split("=")[0]: item.split("=")[1] for item in parsed.query.split("&")
    }

    return query_params["v"]


def publish_short(segment: IDHighlightSegment):
    try:
        print(f"==> Uploading short {segment.title}")
        video_path = os.path.join(OUTPUT_VIDS_DIR, f"out_{segment.id_}.mp4")
        if not os.path.exists(video_path):
            print(f"==> ERROR: {video_path=} doesn't exist")
            return
        upload_short(
            video_path, segment.title, segment.title
        )  # Assuming upload_short is synchronous and raises an error on failure
        with open(PUBLISHED_VIDS_FILE, "a") as f:
            f.write(f"{segment.id_}\n")
        print(f"==> Marked {segment.title} (ID: {segment.id_}) as published.")
    except Exception as error:
        print(f"==> Failed to upload {segment.title}, {error=}")


if __name__ == "__main__":
    VIDEO_URL = sys.argv[1]
    VIDEO_ID = get_yt_video_id(VIDEO_URL)
    print(f"==> Processing video with {VIDEO_ID=}...")
    NO_AUTO_SUBS = "--no-auto-subs" in sys.argv

    vid_name = f"clip_{VIDEO_ID}"
    INPUT_VID_PATH = os.path.join("./input", f"{vid_name}.webm")
    globals()["INPUT_VID_PATH"] = INPUT_VID_PATH
    INPUT_VID_WO_EXT = os.path.join("./input", vid_name)

    OUTPUT_VIDS_DIR = os.path.join("./output", VIDEO_ID)

    SUBTITLES_FILE = f"subs_{VIDEO_ID}.srt"
    HIGHLIGHTS_FILE = f"highlights_{VIDEO_ID}.json"
    PUBLISHED_VIDS_FILE = f"published_{VIDEO_ID}.txt"

    if not os.path.exists(SUBTITLES_FILE):
        download_subtitles(VIDEO_URL, SUBTITLES_FILE, "en", not NO_AUTO_SUBS)
    else:
        print("==> Subtitles exist, skipping downloading them.")

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
        subtitle_chunks = chunk_subtitles(SUBTITLES_FILE)
        he = HighlightExtractor()
        with ThreadPoolExecutor(
            max_workers=min(MAX_HIGHLIGHT_WORKERS, len(subtitle_chunks))
        ) as pool:
            segments = list(pool.map(he.extract, subtitle_chunks))

    flattened_segments = [s for ss in segments for s in ss if obey_valid_length(s)]
    print(f"==> Found {len(flattened_segments)} segments.")
    with open(HIGHLIGHTS_FILE, "w") as f:
        f.write(json.dumps([fs.model_dump() for fs in flattened_segments]))

    if os.path.exists(INPUT_VID_PATH):
        print("==> Skipping downloading video as it already exists.")
    else:
        print("==> Downloading video...")
        download_video(VIDEO_URL, INPUT_VID_WO_EXT)

    os.makedirs(OUTPUT_VIDS_DIR, exist_ok=True)
    if len([f for f in os.listdir(OUTPUT_VIDS_DIR) if f.endswith(".mp4")]) > 0:
        print("==> Skipping video generation as output folder is already populated.")
    else:
        short_gen = ShortGenerator(INPUT_VID_PATH, GAMEPLAYS_PATH, OUTPUT_VIDS_DIR)
        with ProcessPoolExecutor(
            max_workers=min(MAX_VIDEO_WORKERS, len(flattened_segments))
        ) as pool:
            pool.map(short_gen.generate_short_clip, flattened_segments)

    published_segment_ids: set[str]
    if os.path.exists(PUBLISHED_VIDS_FILE):
        with open(PUBLISHED_VIDS_FILE) as f:
            published_segment_ids = set(f.read().split())
    else:
        published_segment_ids = set()

    segment_ids_to_upload = {s.id_ for s in flattened_segments} - published_segment_ids
    if len(segment_ids_to_upload) == 0:
        # all published
        print("All shorts have been published, performing cleanup.")
        os.remove(SUBTITLES_FILE)
        os.remove(HIGHLIGHTS_FILE)
        os.remove(PUBLISHED_VIDS_FILE)
        os.remove(INPUT_VID_PATH)
        shutil.rmtree(OUTPUT_VIDS_DIR)
        exit(0)

    segments_to_upload = [
        s for s in flattened_segments if s.id_ in segment_ids_to_upload
    ]
    print(f"==> Found {len(segment_ids_to_upload)} shorts yet to be published.")
    with ThreadPoolExecutor(
        max_workers=min(MAX_PUBLISH_WORKERS, len(flattened_segments))
    ) as pool:
        pool.map(publish_short, segments_to_upload)

    print("==> Rerun the script with same parameters to ensure cleanup.")
