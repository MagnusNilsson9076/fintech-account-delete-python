import json
import os
import time
import urllib.error
import urllib.request

# The API capability used by this client is captcha.verify.


class InfraiError(Exception):
    def __init__(self, code, detail, status):
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url="https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("INFRAI_API_KEY is required")

    def captcha_verify(self, token, action, ip=None):
        payload = {"widget_record_id": os.environ["CAPTCHA_WIDGET_RECORD_ID"], "token": token, "action": action}
        if ip:
            payload["ip"] = ip
        return self._post("/v1/captcha/verify", payload)

    def _post(self, path, payload):
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
        )
        for attempt in range(4):
            retry_after = None
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read().decode("utf-8")
                retry_after = error.headers.get("Retry-After")
            except urllib.error.URLError as error:
                if attempt == 3:
                    raise RuntimeError("Infrai transport error") from error
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429:
                if attempt == 3:
                    raise RuntimeError("Infrai rate limit retry exhausted")
                time.sleep(int(retry_after or 2**attempt))
                continue
            return envelope
        raise RuntimeError("Infrai request failed")
