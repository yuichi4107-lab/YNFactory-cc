import os
import requests
import datetime
import base64

ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID", "1gvXD4cBSFWjTT7vN92elg")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID", "jn3Y7BycRh69YCvAQFB5VQ")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET", "1pUBHWhlsJ7IvVIEVF0Mbd5KTOpy4ppj")
ZOOM_API_BASE = "https://api.zoom.us/v2"


class ZoomClient:
    def __init__(self, account_id=None, client_id=None, client_secret=None):
        self.account_id = account_id or ZOOM_ACCOUNT_ID
        self.client_id = client_id or ZOOM_CLIENT_ID
        self.client_secret = client_secret or ZOOM_CLIENT_SECRET
        self._token = None
        self._token_expires = None

    def _get_token(self):
        """Get or refresh Server-to-Server OAuth access token."""
        now = datetime.datetime.now()
        if self._token and self._token_expires and now < self._token_expires:
            return self._token

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = requests.post(
            "https://zoom.us/oauth/token",
            headers={"Authorization": f"Basic {credentials}"},
            params={
                "grant_type": "account_credentials",
                "account_id": self.account_id,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        self._token_expires = now + datetime.timedelta(seconds=data.get("expires_in", 3600) - 60)
        return self._token

    def _headers(self):
        return {"Authorization": f"Bearer {self._get_token()}"}

    def list_meetings(self, user_id="me", from_date=None, to_date=None):
        """List past meetings for a user within a date range."""
        if from_date is None:
            from_date = datetime.date.today() - datetime.timedelta(days=1)
        if to_date is None:
            to_date = datetime.date.today()

        all_meetings = []
        next_page_token = ""

        while True:
            params = {
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
                "page_size": 300,
                "type": "past",
            }
            if next_page_token:
                params["next_page_token"] = next_page_token

            response = requests.get(
                f"{ZOOM_API_BASE}/users/{user_id}/meetings",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            meetings = data.get("meetings", [])
            all_meetings.extend(meetings)

            next_page_token = data.get("next_page_token", "")
            if not next_page_token:
                break

        print(f"  Found {len(all_meetings)} meetings ({from_date} ~ {to_date})")
        return all_meetings

    def get_meeting_summary(self, meeting_uuid):
        """Get AI Companion meeting summary by UUID."""
        try:
            import urllib.parse
            encoded = urllib.parse.quote(urllib.parse.quote(meeting_uuid, safe=''), safe='')
            response = requests.get(
                f"{ZOOM_API_BASE}/meetings/{encoded}/meeting_summary",
                headers=self._headers(),
            )
            if response.status_code in (400, 404):
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            return None

    def list_meeting_summaries(self, from_date=None, to_date=None):
        """List all AI Companion meeting summaries in a date range."""
        if from_date is None:
            from_date = datetime.date.today() - datetime.timedelta(days=1)
        if to_date is None:
            to_date = datetime.date.today()

        all_summaries = []
        next_page_token = ""

        while True:
            params = {
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
                "page_size": 30,
            }
            if next_page_token:
                params["next_page_token"] = next_page_token

            response = requests.get(
                f"{ZOOM_API_BASE}/meetings/meeting_summaries",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            summaries = data.get("summaries", [])
            all_summaries.extend(summaries)

            next_page_token = data.get("next_page_token", "")
            if not next_page_token:
                break

        print(f"  Found {len(all_summaries)} meeting summaries ({from_date} ~ {to_date})")
        return all_summaries

    def get_recordings(self, user_id="me", from_date=None, to_date=None):
        """List cloud recordings for a user (max 30-day range per request)."""
        if from_date is None:
            from_date = datetime.date.today() - datetime.timedelta(days=1)
        if to_date is None:
            to_date = datetime.date.today()

        all_recordings = []

        # Zoom allows max 30-day range, chunk if needed
        chunk_start = from_date
        while chunk_start < to_date:
            chunk_end = min(chunk_start + datetime.timedelta(days=30), to_date)
            next_page_token = ""

            while True:
                params = {
                    "from": chunk_start.strftime("%Y-%m-%d"),
                    "to": chunk_end.strftime("%Y-%m-%d"),
                    "page_size": 300,
                }
                if next_page_token:
                    params["next_page_token"] = next_page_token

                response = requests.get(
                    f"{ZOOM_API_BASE}/users/{user_id}/recordings",
                    headers=self._headers(),
                    params=params,
                )
                if response.status_code == 400:
                    break
                response.raise_for_status()
                data = response.json()

                meetings = data.get("meetings", [])
                all_recordings.extend(meetings)

                next_page_token = data.get("next_page_token", "")
                if not next_page_token:
                    break

            chunk_start = chunk_end

        print(f"  Found {len(all_recordings)} recordings ({from_date} ~ {to_date})")
        return all_recordings

    def download_transcript(self, download_url):
        """Download a VTT transcript file."""
        response = requests.get(download_url, headers=self._headers())
        response.raise_for_status()
        return response.text

    def summary_to_markdown(self, summary, meeting_topic=""):
        """Convert AI Companion summary to markdown."""
        lines = []
        lines.append(f"## {meeting_topic or 'Meeting Summary'}")
        lines.append("")

        meeting_start = summary.get("meeting_start_time", "")
        if meeting_start:
            lines.append(f"- **Date**: {meeting_start}")

        # Handle different summary structures
        summary_data = summary.get("summary", summary)

        if isinstance(summary_data, dict):
            overview = summary_data.get("summary_overview", "")
            if overview:
                lines.append(f"\n### Overview\n{overview}")

            details = summary_data.get("summary_details", [])
            for detail in details:
                label = detail.get("label", "")
                content = detail.get("content", "")
                if label and content:
                    lines.append(f"\n### {label}\n{content}")
        elif isinstance(summary_data, str):
            lines.append(f"\n{summary_data}")

        # Check for top-level fields
        for key in ["next_steps", "action_items", "keywords"]:
            val = summary.get(key)
            if val:
                lines.append(f"\n### {key.replace('_', ' ').title()}\n{val}")

        return "\n".join(lines)

    def vtt_to_markdown(self, vtt_text, meeting_topic=""):
        """Convert VTT transcript to readable markdown."""
        lines = []
        lines.append(f"## Transcript: {meeting_topic or 'Meeting'}")
        lines.append("")

        current_speaker = None
        for line in vtt_text.split("\n"):
            line = line.strip()
            if not line or line == "WEBVTT" or "-->" in line:
                continue
            if line.isdigit():
                continue
            # Check for speaker prefix
            if ": " in line:
                speaker, text = line.split(": ", 1)
                if speaker != current_speaker:
                    lines.append(f"\n**{speaker}**:")
                    current_speaker = speaker
                lines.append(f"  {text}")
            else:
                lines.append(f"  {line}")

        return "\n".join(lines)


if __name__ == "__main__":
    client = ZoomClient()
    # Test: get token
    token = client._get_token()
    print(f"Token obtained: {token[:20]}...")

    # Test: list yesterday's meetings
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    meetings = client.list_meetings(from_date=yesterday, to_date=datetime.date.today())
    for m in meetings[:3]:
        print(f"  - {m.get('topic', 'N/A')} ({m.get('start_time', 'N/A')})")
