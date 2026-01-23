import json
import time
import os
import requests
import argparse

from plugin import tx_cos

API_KEY = "AIzaSyDApihFfl2SN22Cwy5hp2FVKaJYrYsEL3g"
PROJECT_ID = "videostudio-production"
STATE_FILE = os.path.expanduser("~/.speechify_token.json")
REFRESH_TOKEN = "AMf-vByNQCc_kX6TQJIz1KbtnRA0hHezyILxdblKPeV1DqyAX7mxqE2Rvl0oH3fMPHKIao6_uLAuQJlQMjQD1QmLPnxeXNOwDLrbGNdif94QIzKSrBzTkGZzDiZNgp2JqWh2p8o0_-3vCWNWdNVNuReabzAyOdVuwuJgiCMLQxyr7kYHCiqW7Rwz3VGNrLg2remDI9WynzOfyKuC07T5D9XuKeNi6Fmhc82aGpDMOYjy6yI0NKLXYF6dtQfYNc3YoD5-0VCWDm6X_n3cCZzg7ELmJjJgE-bKusN4NuUp8U1A0B2BkD3UEToPh49Je1kiWf3LU02Lai9eUbz2UCJSKZRTz1hA1NmjShR1DK0qif0RCf83UpwtmOWlidEbk6ZXKnx_VMbek-n5iWnhVubmRoat5NCznv3qRRQsNvB1-jALkfbe1JBMteI"
proxies = {
    "http": "http://127.0.0.1:7890",   # HTTP 代理
    "https": "http://127.0.0.1:7890",  # HTTPS 代理
}


class SpeechifyTokenManager:

    def __init__(self):
        self.state_file = STATE_FILE
        self.refresh_token = REFRESH_TOKEN

    def _now(self) -> int:
        return int(time.time())

    def _load_state(self):
        if not os.path.exists(self.state_file):
            return None
        with open(self.state_file, "r") as f:
            return json.load(f)

    def _save_state(self, token: str, expires_at: int):
        with open(self.state_file, "w") as f:
            json.dump(
                {
                    "speechify_token": token,
                    "expires_at": expires_at,
                },
                f,
            )

    def _google_refresh(self):
        url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        resp = requests.post(
            url,
            headers={"content-type": "application/x-www-form-urlencoded"},
            data=data,
            timeout=10,
            proxies=proxies
        )
        resp.raise_for_status()
        return resp.json()

    def _exchange_speechify_token(self, google_id_token: str):
        url = "https://auth.api.speechify.com/v1/id-tokens"
        resp = requests.post(
            url,
            headers={
                "authorization": f"Bearer {google_id_token}",
                "content-type": "application/json",
            },
            json={"projectId": PROJECT_ID},
            timeout=10,
            proxies=proxies
        )
        resp.raise_for_status()
        return resp.json()

    def get_token(self) -> str:
        state = self._load_state()
        if state and self._now() < state["expires_at"]:
            return state["speechify_token"]

        google_data = self._google_refresh()
        google_id_token = google_data["id_token"]
        expires_in = int(google_data["expires_in"])

        speechify_data = self._exchange_speechify_token(google_id_token)

        speechify_token = (
            speechify_data.get("token")
            or speechify_data.get("accessToken")
            or speechify_data.get("access_token")
        )

        if not speechify_token:
            raise RuntimeError(f"Unexpected response: {speechify_data}")

        expires_at = self._now() + expires_in - 60
        self._save_state(speechify_token, expires_at)
        return speechify_token


def tts_scratchpad(token, text, output, voice_id, pitch, speed, prompt, *, cos_key=None):
    url = "https://videostudio.api.speechify.com/tts/v2/scratchpad/stream"

    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "origin": "https://studio.speechify.com",
        "referer": "https://studio.speechify.com/",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }

    payload = {
        "content": [
            {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": text}
                        ]
                    }
                ]
            }
        ],
        "voiceId": voice_id,
        "options": {"emotion": None, "pitch": pitch, "speed": speed},
        "prompt": prompt,
        "forceRegenerate": False,
    }

    with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, proxies=proxies) as r:
        r.raise_for_status()
        if cos_key:
            cos_url = tx_cos.upload(cos_key, r.content)
            return cos_url
        with open(output, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"Saved TTS output to {output}")


def speechify_tts(uid, *, text: str, pitch=5, speed=5, prompt="少女音"):
    tm = SpeechifyTokenManager()
    token = tm.get_token()
    now = int(time.time() * 1000)
    prefix = tx_cos.store_dir('audio')
    cos_key = f"{prefix}/{uid}/{now}.wav"
    return tts_scratchpad(
        token,
        text,
        f"audio/{now}.wav",
        "PERSONA:98bBIhEQq7g0TslAyyAk5",
        pitch, speed, prompt,
        cos_key=cos_key
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="要合成的文本")
    parser.add_argument("--output", required=True, help="输出 WAV 文件路径")
    parser.add_argument("--voice-id", default="PERSONA:98bBIhEQq7g0TslAyyAk5", help="voiceId")
    parser.add_argument("--pitch", type=int, default=13, help="音高")
    parser.add_argument("--speed", type=int, default=16, help="语速")
    parser.add_argument("--prompt", default="情色小说独白激烈娇喘少女音", help="prompt")
    args = parser.parse_args()

    tm = SpeechifyTokenManager()
    token = tm.get_token()

    tts_scratchpad(
        token,
        args.text,
        args.output,
        args.voice_id,
        args.pitch,
        args.speed,
        args.prompt,
    )


if __name__ == "__main__":
    # main()
    url = speechify_tts("啊啊啊~要不行了~", 787841563)
    print(url)

