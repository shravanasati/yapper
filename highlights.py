import secrets
import string
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from pydantic import BaseModel

from subtitles import srt_time_to_seconds


def _generate_id(length: int = 8) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


class HighlightSegment(BaseModel):
    start_time: str
    end_time: str
    title: str


class IDHighlightSegment(HighlightSegment):
    id_: str


def obey_valid_length(segment: IDHighlightSegment) -> bool:
    """
    Predicate function to check whether the segment obeys valid short duration.

    10s is too short, and 3 mins is YT's defined limit for a short.
    """
    start = srt_time_to_seconds(segment.start_time)
    end = srt_time_to_seconds(segment.end_time)
    duration = end - start
    max_video_len = 60 * 3  # 3 mins
    min_video_len = 10
    return min_video_len <= duration <= max_video_len


load_dotenv()


SYSTEM_MESSAGE = """
**Analyze the following podcast transcript, which is in SRT format, and identify key segments that would make excellent YouTube Shorts or TikTok videos. Each segment should be atleast 20s long.**

**Your Goal:** For each segment, provide the start time, end time, and a catchy, clickbaity title. You can use CAPS for emphasis, emojis and add hashtags as well for virality.

**Look for segments that contain:**
* Strong, controversial, or surprising statements.
* Highly emotional moments (laughter, frustration, excitement).
* Actionable advice, tips, or "hacks."
* A compelling short story or anecdote.
* A "mic drop" moment or a powerful concluding thought.
* A heated debate or a moment of clear disagreement.

**Output Format:**
For each identified segment, provide the following in JSON format:

- **Segment #:**
- **Start Time:** [Provide the start timestamp from the SRT file, e.g., HH:MM:SS,ms]
- **End Time:** [Provide the end timestamp from the SRT file, e.g., HH:MM:SS,ms]
- **Proposed Title:** [Your catchy, clickbaity title]
""".strip()


class HighlightExtractor:
    def __init__(self) -> None:
        self.client = genai.Client()

    def extract(self, subtitle_chunk: str) -> list[IDHighlightSegment]:
        print("Extracting highlights from subtitle chunk...")
        retries = 5
        delay = 15  # seconds

        for i in range(retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-preview-05-20",
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_MESSAGE,
                        temperature=1,
                        response_mime_type="application/json",
                        response_schema=list[HighlightSegment],
                    ),
                    contents=subtitle_chunk,
                )

                segments: list[HighlightSegment] = response.parsed
                return [
                    IDHighlightSegment(id_=_generate_id(), **s.model_dump())
                    for s in segments
                ]
            except ClientError as e:
                if not e.code == 429:
                    # only handle rate limit errors
                    raise e
                if i < retries - 1:
                    print(
                        f"Rate limit exceeded. Retrying in {delay} seconds... ({i + 1}/{retries})"
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print("Max retries reached. Failed to extract highlights.")
                    raise e
        return []


if __name__ == "__main__":
    gcm = HighlightExtractor()
    with open("./subs.srt") as f:
        print(gcm.extract("".join(f.readlines(1000))))
