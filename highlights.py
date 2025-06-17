import secrets
import string

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel


def _generate_id(length: int = 8) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


class HighlightSegment(BaseModel):
    start_time: str
    end_time: str
    title: str


class IDHighlightSegment(HighlightSegment):
    id_: str


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
            IDHighlightSegment(id_=_generate_id(), **s.model_dump()) for s in segments
        ]


if __name__ == "__main__":
    gcm = HighlightExtractor()
    with open("./subs.srt") as f:
        print(gcm.extract("".join(f.readlines(1000))))
