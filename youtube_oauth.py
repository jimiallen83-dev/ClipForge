import os

try:
    import isodate
except Exception:
    isodate = None

try:
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    _have_google = True
except Exception:
    Flow = None
    Credentials = None
    build = None
    _have_google = False

SCOPES = [
    "openid",
    # use the userinfo scopes to match Google's returned scope names
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
]
CLIENT_SECRETS_FILE = os.environ.get("CLIENT_SECRETS_FILE", "client_secrets.json")


def _load_client_config():
    # support alternative filenames and env override
    candidates = [CLIENT_SECRETS_FILE, "client_secret.json", "client_secrets.json"]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        "Create OAuth client secrets JSON (one of %s) in the project root "
        "or set CLIENT_SECRETS_FILE env var." % (candidates,)
    )


def make_flow(redirect_uri):
    if not _have_google:
        raise RuntimeError(
            "google oauth libraries not installed. Install "
            "'google-auth-oauthlib' and 'google-api-python-client'."
        )
    # Allow insecure (HTTP) redirect URIs for localhost during development when appropriate.
    # This sets OAUTHLIB_INSECURE_TRANSPORT only for localhost/127.0.0.1 http URLs.
    try:
        if redirect_uri.startswith("http://") and (
            "localhost" in redirect_uri or "127.0.0.1" in redirect_uri
        ):
            os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    except Exception:
        pass
    client_config = _load_client_config()
    flow = Flow.from_client_secrets_file(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow


def build_authorize_url(redirect_uri):
    flow = make_flow(redirect_uri)
    # use lowercase 'true' to match OAuth provider expectations in query string
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    return auth_url, state


def exchange_code_for_credentials(redirect_uri, request_args):
    flow = make_flow(redirect_uri)
    # request_args should be a dict that contains full query parameters, e.g. request.url.query
    if "full_url" not in request_args:
        raise ValueError(
            "request_args must include 'full_url' with the full redirect URL from Google"
        )
    flow.fetch_token(
        authorization_response=request_args["full_url"]
    )  # full redirect URL
    creds = flow.credentials
    return creds


def fetch_channel_videos(credentials):
    if not _have_google:
        raise RuntimeError("google api libraries not installed")
    youtube = build("youtube", "v3", credentials=credentials)

    # Get authenticated user's channel
    ch_resp = (
        youtube.channels().list(part="contentDetails,snippet", mine=True).execute()
    )
    items = ch_resp.get("items", [])
    if not items:
        return [], None
    channel = items[0]
    uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    channel_id = channel["id"]
    channel_title = channel.get("snippet", {}).get("title")

    videos = []
    nextPage = None
    while True:
        pl_req = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=nextPage,
        )
        pl_resp = pl_req.execute()
        for it in pl_resp.get("items", []):
            vid_id = it["snippet"]["resourceId"]["videoId"]
            videos.append({"video_id": vid_id})
        nextPage = pl_resp.get("nextPageToken")
        if not nextPage:
            break

    # Batch call to videos().list to fetch details in chunks
    detailed = []
    for i in range(0, len(videos), 50):
        batch = videos[i:i + 50]
        ids = ",".join([v["video_id"] for v in batch])
        vids = (
            youtube.videos()
            .list(
                part="snippet,contentDetails,status",
                id=ids,
            )
            .execute()
        )
        for v in vids.get("items", []):
            dur = v.get("contentDetails", {}).get("duration")
            try:
                if isodate:
                    seconds = isodate.parse_duration(dur).total_seconds() if dur else 0
                else:
                    seconds = 0
            except Exception:
                seconds = 0
            detailed.append(
                {
                    "video_id": v["id"],
                    "title": v.get("snippet", {}).get("title"),
                    "description": v.get("snippet", {}).get("description"),
                    "duration": seconds,
                    "privacy": v.get("status", {}).get("privacyStatus", "unknown"),
                }
            )

    return detailed, {"channel_id": channel_id, "title": channel_title}
