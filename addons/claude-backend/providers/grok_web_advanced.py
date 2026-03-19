"""Advanced Grok Web handshake helpers (reverse-engineered flow).

This module mirrors the anti-bot handshake strategy used by community
reverse clients:
- load grok.com/c and parse dynamic next-actions
- perform /c server-action challenge flow
- derive x-statsig-id for conversation endpoints

All logic is best-effort and may break when Grok frontend changes.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import random
import re
import time
import uuid
from dataclasses import dataclass
from struct import pack
from typing import Dict, List, Optional, Tuple


try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except Exception:
    BeautifulSoup = None
    BS4_AVAILABLE = False

try:
    from coincurve import PrivateKey
    COINCURVE_AVAILABLE = True
except Exception:
    PrivateKey = None
    COINCURVE_AVAILABLE = False

try:
    from curl_cffi import requests as cffi_requests
    from curl_cffi import CurlMime
    CFFI_AVAILABLE = True
except Exception:
    cffi_requests = None
    CurlMime = None
    CFFI_AVAILABLE = False


def available() -> bool:
    return bool(BS4_AVAILABLE and COINCURVE_AVAILABLE and CFFI_AVAILABLE)


def _between(text: str, start: str, end: str) -> str:
    s = text.find(start)
    if s == -1:
        return ""
    s += len(start)
    e = text.find(end, s)
    if e == -1:
        return ""
    return text[s:e]


def _fix_order(headers: Dict[str, str], base_order: List[str]) -> Dict[str, str]:
    ordered: Dict[str, str] = {}
    for k in base_order:
        if k in headers:
            ordered[k] = headers[k]
    for k, v in headers.items():
        if k not in ordered:
            ordered[k] = v
    return ordered


def _gen_keys() -> Dict[str, object]:
    seed = random.randbytes(32)
    priv = PrivateKey(seed)
    pub = list(priv.public_key.format(compressed=True))
    priv_b64 = base64.b64encode(seed).decode()
    return {"private_key_b64": priv_b64, "public_key_arr": pub}


def _sign_challenge(challenge_data: bytes, private_key_b64: str) -> Dict[str, str]:
    key_bytes = base64.b64decode(private_key_b64)
    priv = PrivateKey(key_bytes)
    sig = priv.sign_recoverable(hashlib.sha256(challenge_data).digest(), hasher=None)[:64]
    return {
        "challenge": base64.b64encode(challenge_data).decode(),
        "signature": base64.b64encode(sig).decode(),
    }


def _extract_anim(verification_token: str) -> int:
    arr = list(base64.b64decode(verification_token))
    return int(arr[5] % 4) if len(arr) > 5 else 0


def _parse_grok_actions_and_xsid_script(html: str, scripts: List[str], session) -> Tuple[List[str], str]:
    action_script_content = ""
    xsid_script_content = ""
    xsid_script_name = ""

    for script in scripts:
        url = f"https://grok.com{script}"
        r = session.get(url, timeout=30)
        if r.status_code != 200:
            continue
        txt = r.text or ""
        if "anonPrivateKey" in txt:
            action_script_content = txt
        if "880932)" in txt:
            xsid_script_content = txt

    actions = re.findall(r'createServerReference\)\("([a-f0-9]+)"', action_script_content)
    m = re.search(r'"(static/chunks/[^"]+\.js)"[^}]*?\(880932\)', xsid_script_content)
    if m:
        xsid_script_name = m.group(1)
    if not actions or not xsid_script_name:
        return [], ""
    return actions[:3], xsid_script_name


def _parse_values_and_numbers(html: str, loading: int, xsid_script: str, session) -> Tuple[str, List[int]]:
    match = re.findall(r'\[\[{"color".*?}\]\]', html)
    if not match:
        return "", []
    d_values = json.loads(match[0])[loading]
    svg_data = "M 10,30 C" + " C".join(
        f" {item['color'][0]},{item['color'][1]} {item['color'][2]},{item['color'][3]} {item['color'][4]},{item['color'][5]}"
        f" h {item['deg']}"
        f" s {item['bezier'][0]},{item['bezier'][1]} {item['bezier'][2]},{item['bezier'][3]}"
        for item in d_values
    )

    script_link = f"https://grok.com/_next/{xsid_script}"
    r = session.get(script_link, timeout=30)
    txt = r.text if r.status_code == 200 else ""
    numbers = [int(x) for x in re.findall(r"x\[(\d+)\]\s*,\s*16", txt)]
    return svg_data, numbers


def _signature_xa(svg: str) -> List[List[int]]:
    parts = svg[9:].split("C")
    out = []
    for part in parts:
        cleaned = re.sub(r"[^\d]+", " ", part).strip()
        nums = [int(tok) for tok in cleaned.split()] if cleaned else [0]
        out.append(nums)
    return out


def _signature_h(x: float, p: float, c: float, e: bool):
    f = ((x * (c - p)) / 255.0) + p
    return math.floor(f) if e else (0.0 if round(float(f), 2) == 0.0 else round(float(f), 2))


def _cubic_bezier_eased(t: float, x1: float, y1: float, x2: float, y2: float) -> float:
    def bezier(u: float):
        omu = 1.0 - u
        b1 = 3.0 * omu * omu * u
        b2 = 3.0 * omu * u * u
        b3 = u * u * u
        x = b1 * x1 + b2 * x2 + b3
        y = b1 * y1 + b2 * y2 + b3
        return x, y

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if bezier(mid)[0] < t:
            lo = mid
        else:
            hi = mid
    u = 0.5 * (lo + hi)
    return bezier(u)[1]


def _tohex(num: float) -> str:
    rounded = round(float(num), 2)
    if rounded == 0.0:
        return "0"
    sign = "-" if math.copysign(1.0, rounded) < 0 else ""
    absval = abs(rounded)
    intpart = int(math.floor(absval))
    frac = absval - intpart
    if frac == 0.0:
        return sign + format(intpart, "x")
    frac_digits = []
    f = frac
    for _ in range(20):
        f *= 16
        digit = int(math.floor(f + 1e-12))
        frac_digits.append(format(digit, "x"))
        f -= digit
        if abs(f) < 1e-12:
            break
    frac_str = "".join(frac_digits).rstrip("0")
    if not frac_str:
        return sign + format(intpart, "x")
    return sign + format(intpart, "x") + "." + frac_str


def _simulate_style(values: List[int], c: int) -> Dict[str, str]:
    duration = 4096
    current_time = round(c / 10.0) * 10
    t = current_time / duration
    cp = [_signature_h(v, -1 if (i % 2) else 0, 1, False) for i, v in enumerate(values[7:])]
    eased_y = _cubic_bezier_eased(t, cp[0], cp[1], cp[2], cp[3])

    start = [float(x) for x in values[0:3]]
    end = [float(x) for x in values[3:6]]
    r = round(start[0] + (end[0] - start[0]) * eased_y)
    g = round(start[1] + (end[1] - start[1]) * eased_y)
    b = round(start[2] + (end[2] - start[2]) * eased_y)
    color = f"rgb({r}, {g}, {b})"

    end_angle = _signature_h(values[6], 60, 360, True)
    angle = end_angle * eased_y
    rad = angle * math.pi / 180.0
    cosv = math.cos(rad)
    sinv = math.sin(rad)
    a = 0 if abs(cosv) < 1e-7 else (int(round(cosv)) if abs(cosv - round(cosv)) < 1e-7 else f"{cosv:.6f}")
    d = a
    bval = 0 if abs(sinv) < 1e-7 else (int(round(sinv)) if abs(sinv - round(sinv)) < 1e-7 else f"{sinv:.7f}")
    cval = 0 if abs(sinv) < 1e-7 else (int(round(-sinv)) if abs(sinv - round(sinv)) < 1e-7 else f"{(-sinv):.7f}")
    transform = f"matrix({a}, {bval}, {cval}, {d}, 0, 0)"
    return {"color": color, "transform": transform}


def _xs(x_bytes: bytes, svg: str, x_values: List[int]) -> str:
    arr = list(x_bytes)
    if len(x_values) < 4:
        return ""
    idx = arr[x_values[0]] % 16
    c = ((arr[x_values[1]] % 16) * (arr[x_values[2]] % 16)) * (arr[x_values[3]] % 16)
    vals = _signature_xa(svg)[idx]
    k = _simulate_style(vals, c)
    concat = str(k["color"]) + str(k["transform"])
    matches = re.findall(r"[\d\.\-]+", concat)
    converted = [_tohex(float(m)) for m in matches]
    return "".join(converted).replace(".", "").replace("-", "")


def generate_xsid(path: str, method: str, verification: str, svg: str, x_values: List[int]) -> str:
    n = int(time.time() - 1682924400)
    t = pack("<I", n)
    r = base64.b64decode(verification)
    o = _xs(r, svg, x_values)
    msg = "!".join([method, path, str(n)]) + "obfiowerehiring" + o
    digest = hashlib.sha256(msg.encode("utf-8")).digest()[:16]
    prefix = int(math.floor(random.random() * 256))
    assembled = bytes([prefix]) + r + t + digest + bytes([3])
    arr = bytearray(assembled)
    if arr:
        first = arr[0]
        for i in range(1, len(arr)):
            arr[i] ^= first
    return base64.b64encode(bytes(arr)).decode("ascii").replace("=", "")


@dataclass
class HandshakeState:
    session: object
    actions: List[str]
    verification_token: str
    svg_data: str
    numbers: List[int]
    baggage: str
    sentry_trace: str
    anon_user_id: str
    private_key_b64: str


def build_conversation_headers(state: HandshakeState, path: str) -> Dict[str, str]:
    xsid = generate_xsid(path, "POST", state.verification_token, state.svg_data, state.numbers)
    sentry = state.sentry_trace
    trace_suffix = str(uuid.uuid4()).replace("-", "")[:16]
    traceparent = f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-00"
    headers = {
        "x-xai-request-id": str(uuid.uuid4()),
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "baggage": state.baggage,
        "sentry-trace": f"{sentry}-{trace_suffix}-0" if sentry else "",
        "traceparent": traceparent,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "content-type": "application/json",
        "x-statsig-id": xsid,
        "accept": "*/*",
        "origin": "https://grok.com",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://grok.com/",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i",
    }
    base = [
        "x-xai-request-id", "sec-ch-ua-platform", "sec-ch-ua", "sec-ch-ua-mobile",
        "baggage", "sentry-trace", "traceparent", "user-agent", "content-type",
        "x-statsig-id", "accept", "origin", "sec-fetch-site", "sec-fetch-mode",
        "sec-fetch-dest", "referer", "accept-encoding", "accept-language", "priority",
    ]
    return _fix_order(headers, base)


def init_handshake(cookie_header: str, impersonate: str = "chrome136") -> Optional[HandshakeState]:
    if not available():
        return None

    session = cffi_requests.Session(impersonate=impersonate, default_headers=False)
    session.headers = {
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=0, i",
        "cookie": cookie_header,
    }
    load_site = session.get("https://grok.com/c", timeout=30)
    if load_site.status_code != 200:
        return None

    html = load_site.text or ""
    soup = BeautifulSoup(html, "html.parser")
    scripts = [
        s["src"] for s in soup.find_all("script", src=True)
        if s.get("src", "").startswith("/_next/static/chunks/")
    ]
    actions, xsid_script = _parse_grok_actions_and_xsid_script(html, scripts, session)
    if len(actions) < 3 or not xsid_script:
        return None

    baggage = _between(html, '<meta name="baggage" content="', '"')
    sentry_trace = _between(html, '<meta name="sentry-trace" content="', "-")
    keys = _gen_keys()

    # c_request #1 (multipart)
    c_headers = {
        "next-action": actions[0],
        "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22c%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22%22%2C%22oc%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
        "baggage": baggage,
        "sentry-trace": f"{sentry_trace}-{uuid.uuid4().hex[:16]}-0" if sentry_trace else "",
        "user-agent": session.headers.get("user-agent", ""),
        "accept": "text/x-component",
        "origin": "https://grok.com",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://grok.com/c",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i",
        "cookie": cookie_header,
    }
    c_headers = _fix_order(c_headers, list(c_headers.keys()))
    mime = CurlMime()
    mime.addpart(name="1", data=bytes(keys["public_key_arr"]), filename="blob", content_type="application/octet-stream")
    mime.addpart(name="0", filename=None, data='[{"userPublicKey":"$o1"}]')
    c1 = session.post("https://grok.com/c", headers=c_headers, multipart=mime, timeout=30)
    if c1.status_code != 200:
        return None
    anon_user = _between(c1.text or "", '{"anonUserId":"', '"')
    if not anon_user:
        return None

    # c_request #2
    c_headers["next-action"] = actions[1]
    c2 = session.post("https://grok.com/c", headers=c_headers, data=json.dumps([{"anonUserId": anon_user}]), timeout=30)
    if c2.status_code != 200:
        return None
    payload_hex = c2.content.hex()
    start_idx = payload_hex.find("3a6f38362c")
    if start_idx == -1:
        return None
    start_idx += len("3a6f38362c")
    end_idx = payload_hex.find("313a", start_idx)
    if end_idx == -1:
        return None
    challenge_bytes = bytes.fromhex(payload_hex[start_idx:end_idx])
    challenge = _sign_challenge(challenge_bytes, keys["private_key_b64"])

    # c_request #3
    c_headers["next-action"] = actions[2]
    c3_payload = [{"anonUserId": anon_user, **challenge}]
    c3 = session.post("https://grok.com/c", headers=c_headers, data=json.dumps(c3_payload), timeout=30)
    if c3.status_code != 200:
        return None
    c3_html = c3.text or ""
    verification_token = _between(c3_html, '"name":"grok-site-verification","content":"', '"')
    if not verification_token:
        return None
    anim = _extract_anim(verification_token)
    svg_data, numbers = _parse_values_and_numbers(c3_html, anim, xsid_script, session)
    if not svg_data or not numbers:
        return None

    return HandshakeState(
        session=session,
        actions=actions,
        verification_token=verification_token,
        svg_data=svg_data,
        numbers=numbers,
        baggage=baggage,
        sentry_trace=sentry_trace,
        anon_user_id=anon_user,
        private_key_b64=keys["private_key_b64"],
    )

