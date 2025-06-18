import os
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# OAuth scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


# Authenticate and return API client
def get_authenticated_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
        creds = flow.run_local_server(port=8080)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: str,
    title: str,
    description: str,
    tags=["shorts", "podcast", "viral", "funny"],
):
    youtube = get_authenticated_service()

    request_body = {
        "snippet": {
            "title": title[:100],  # max allowed title for youtube video is 100 chars
            "description": description,
            "tags": tags or [],
            "categoryId": "22",  # "People & Blogs" (common for Shorts)
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, resumable=True, mimetype="video/*")

    request = youtube.videos().insert(
        part="snippet,status", body=request_body, media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print("✅ Upload complete:", response["id"])
    return response


# Example usage
if __name__ == "__main__":
    upload_short(
        video_path="./output/out_2u65tQwU.mp4",
        title="🚨 THIS BLEW MY MIND 🤯 #podcast #viral #shorts",
        description="Crazy moment from the latest episode.",
        tags=["shorts", "podcast", "viral", "funny"],
    )
