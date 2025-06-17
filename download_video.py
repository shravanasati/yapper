from yt_dlp import YoutubeDL


def download_video(video_url: str, out_path: str):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": out_path,
        "quiet": False,
        "noplaylist": True,
        "remux_video": "mp4",  # Convert to MP4 without re-encoding
        "cookiefile": "cookies.txt",
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])


if __name__ == "__main__":
    download_video("https://www.youtube.com/watch?v=UeUhbdApe6k", "clip")
