import subprocess


def generate_short_clip(
    podcast_path: str,
    gameplay_path: str,
    output_path: str,
    start: float,
    end: float,
):
    duration = end - start
    # Output video size for Shorts (9:16)
    output_width = 720
    output_height = 1280

    podcast_video_height = int(output_height * 0.6)
    # Ensure the sum of heights is exactly output_height
    gameplay_video_height = output_height - podcast_video_height

    filter_complex = (
        f"[0:v]scale={output_width}:{podcast_video_height},setsar=1[podcast_v];"
        f"[1:v]scale={output_width}:{gameplay_video_height},setsar=1[gameplay_v];"
        f"[podcast_v][gameplay_v]vstack=inputs=2[final_v]"
    )

    command = [
        "ffmpeg",
        "-y",
        # "-hwaccel",
        # "qsv",  # Intel Quick Sync hardware acceleration
        "-ss",
        str(start),
        "-t",
        str(duration),
        "-i",
        podcast_path,
        "-stream_loop",
        "-1",
        # "-hwaccel",
        # "qsv",  # For second input too
        "-i",
        gameplay_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[final_v]",  # Map the combined video stream
        "-map",
        "0:a",
        "-c:v",
        "h264_qsv",  # Intel QSV H.264 encoder
        "-preset",
        "fast",
        "-b:v",
        "2M",  # Bitrate
        "-r",  # Set output frame rate
        "30",  # Set output frame rate
        "-shortest",
        output_path,
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    generate_short_clip(
        "./input/clip.webm", "./gameplays/subway surfers gameplay.mp4", "out.mp4", 4, 24
    )
