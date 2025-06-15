from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import json
import os
import random
from download_video import download_video
from subtitles import download_subtitles, chunk_subtitles, srt_time_to_seconds
from highlights import HighlightExtractor, IDHighlightSegment

import sys

from video_gen import generate_short_clip


def generate_short(segment: IDHighlightSegment):
    print(f"==> Generating clip for {segment.title}")
    generate_short_clip(
        "./input/clip.webm",
        random.choice(
            os.listdir("./gameplays")
        ),
        f"./output/out_{segment.id_}.mp4",
        srt_time_to_seconds(segment.start_time),
        srt_time_to_seconds(segment.end_time),
    )


if __name__ == "__main__":
    video_url = sys.argv[1]
    NO_AUTO_SUBS = "--no-auto-subs" in sys.argv
    subs_out = "subs.srt"
    if not os.path.exists(subs_out):
        download_subtitles(video_url, subs_out, "en", not NO_AUTO_SUBS)
    else:
        print("==> Subtitles exist, skipping downloading them.")

    subtitle_chunks = chunk_subtitles(subs_out)

    extract_highlights = True
    if os.path.exists("./highlights.json"):
        try:
            with open("./highlights.json") as h:
                segments = [[IDHighlightSegment(**s) for s in json.load(h)]]
            extract_highlights = False
            print("==> Found cached highlights, skipping extraction.")
        except Exception as e:
            print(e)
            print("==> Failed to load cached highlights, fetching them again.")

    if extract_highlights:
        he = HighlightExtractor()
        with ThreadPoolExecutor(max_workers=min(10, len(subtitle_chunks))) as pool:
            segments = list(pool.map(he.extract, subtitle_chunks))

    flattened_segments = [s for ss in segments for s in ss]
    with open("./highlights.json", "w") as f:
        f.write(json.dumps([fs.model_dump() for fs in flattened_segments]))

    if os.path.exists("./input/clip.webm"):
        print("==> Skipping downloading video as it already exists.")
    else:
        print("==> Downloading video...")
        download_video(video_url, "clip")

    os.makedirs("./output", exist_ok=True)
    with ProcessPoolExecutor(max_workers=min(4, len(flattened_segments))) as pool:
        pool.map(generate_short, flattened_segments)

    # os.remove("./input/clip.webm")
    # os.remove("./highlights.json")
    # os.remove("./subs.srt")
