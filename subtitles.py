import os
import re
from datetime import timedelta

import srt
from yt_dlp import YoutubeDL


def download_subtitles(
    video_url: str,
    output_path: str = "subs.srt",
    lang: str = "en",
    automatic_subs: bool = True,
):
    ydl_opts = {
        "writesubtitles": True,  # Download subtitles
        "subtitleslangs": [lang],  # Language of subtitles
        "subtitlesformat": "srt",  # Format: SRT
        "skip_download": True,  # Don't download the video
        "outtmpl": "temp",  # Temporary filename
        "writeautomaticsub": automatic_subs,
        "cookiefile": "cookies.txt",
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        if info is None:
            raise ValueError("unable to extract information from ytdl")

        # Construct expected subtitle filename
        # video_id = info.get("id")
        subtitle_filename = f"temp.{lang}.srt"

        if os.path.exists(subtitle_filename):
            if os.path.exists(output_path):
                print(f"{output_path=} already exists, overwriting it")
                os.remove(output_path)
            os.rename(subtitle_filename, output_path)
            print(f"✅ Subtitles downloaded to: {output_path}")
        else:
            print("❌ Subtitles not found (may not be available in this language)")

        # print("Pre-processing the subtitles file...")
        # _remove_numbers_from_subtitles(output_path)


def _remove_numbers_from_subtitles(srt_file: str):
    with open(srt_file) as f:
        content = f.read()

    numbers_regex = re.compile(r"^\d{1,}$\n", re.MULTILINE)
    numbers_removed_content = numbers_regex.sub("", content)
    with open(srt_file, "w") as f:
        f.write(numbers_removed_content)


def chunk_subtitles(sub_file: str, chunk_duration_minutes: int = 15):
    try:
        with open(sub_file, "r", encoding="utf-8") as f:
            srt_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{sub_file}' was not found.")
        return []

    print(f"Parsing subtitles from {sub_file}...")
    try:
        subtitles = list(srt.parse(srt_content))
    except srt.SRTParseError as e:
        print(f"Error parsing SRT file: {e}")
        return []

    if not subtitles:
        print("No subtitles found in the file.")
        return []

    print(f"Successfully parsed {len(subtitles)} subtitle blocks.")

    # Define the duration for each chunk
    chunk_delta = timedelta(minutes=chunk_duration_minutes)

    all_chunks = []
    current_chunk = []

    # The start time of the first subtitle in the current running chunk
    chunk_start_time = subtitles[0].start

    for sub in subtitles:
        # If the current chunk is empty, it's the beginning of a new chunk
        if not current_chunk:
            chunk_start_time = sub.start

        # Check if adding the current subtitle would exceed the chunk duration
        # We check from the start of the chunk to the start of the current subtitle
        if (sub.start - chunk_start_time) >= chunk_delta:
            # The current chunk is full. Finalize it.
            # We need to re-index the subtitles to start from 1 for each new file
            all_chunks.append(srt.compose(current_chunk, reindex=True))

            # Start a new chunk with the current subtitle
            current_chunk = [sub]
            chunk_start_time = sub.start
        else:
            # The chunk is not full yet, so add the subtitle to it
            current_chunk.append(sub)

    # After the loop, add the last remaining chunk
    if current_chunk:
        all_chunks.append(srt.compose(current_chunk, reindex=True))

    print(f"Successfully split the file into {len(all_chunks)} chunks.")
    return all_chunks


def srt_time_to_seconds(time_str: str):
    """Converts an SRT timestamp string to total seconds."""
    try:
        match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", time_str)
        if not match:
            # Fallback for timestamps with a period decimal separator
            match = re.match(r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})", time_str)
        if not match:
            raise ValueError(f"Invalid SRT time format: {time_str}")

        hours, minutes, seconds, milliseconds = map(int, match.groups())
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        return total_seconds
    except (ValueError, TypeError):
        # Return a default value or handle the error if the format is unexpected
        print(f"Warning: Could not parse timestamp '{time_str}'. Defaulting to 0.")
        return 0


if __name__ == "__main__":
    download_subtitles("https://www.youtube.com/watch?v=MdeQMVBuGgY")
