"""Error handling and humanization utilities."""

import re
from typing import Optional

import tools
from core.translations import get_lang_text


def _extract_http_error_code(error_text: str) -> Optional[int]:
    """Extract HTTP error code from error message text."""
    if not error_text:
        return None
    # "Error code: 429" (Anthropic/OpenAI style)
    m = re.search(r"Error code:\s*(\d{3})", error_text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    # "HTTP 429: ..." (httpx / _openai_compat_stream style)
    m = re.search(r"HTTP (\d{3})\b", error_text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    # "429 RESOURCE_EXHAUSTED" (google-genai style) or "'code': 429"
    m = re.search(r"^(\d{3})\s", error_text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    m = re.search(r"['\"]code['\"]\s*:\s*(\d{3})", error_text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    return None


def _extract_remote_message(error_text: str) -> str:
    """Best-effort extraction of a remote 'message' field from error strings."""
    if not error_text:
        return ""
    # Common shapes:
    # - {'error': {'message': '...'}}
    # - {"error": {"message": "..."}}
    # Handle escaped quotes inside strings, e.g.:
    # {"message":"model \"gpt-5.4\" is not accessible ..."}
    patterns = (
        r'"message"\s*:\s*"((?:\\.|[^"\\])*)"',
        r"'message'\s*:\s*'((?:\\.|[^'\\])*)'",
    )
    for pat in patterns:
        m = re.search(pat, error_text)
        if not m:
            continue
        raw_msg = (m.group(1) or "").strip()
        if not raw_msg:
            continue
        try:
            # Decode escape sequences safely by round-tripping through JSON.
            decoded = __import__("json").loads(f'"{raw_msg}"')
            if isinstance(decoded, str) and decoded.strip():
                return decoded.strip()
        except Exception:
            pass
        return raw_msg
    return ""


def humanize_provider_error(err: Exception, provider: str) -> str:
    """Turn provider exceptions into short, user-friendly UI messages."""
    raw = str(err) if err is not None else ""
    code = _extract_http_error_code(raw)
    remote_msg = _extract_remote_message(raw)
    # Search the FULL error text for classification keywords (the remote_msg
    # alone may strip away important fields like "code": "insufficient_quota").
    low = raw.lower()

    # Tool not available in the provider's tier (compact/extended mode)
    if "not in request.tools" in low or "attempted to call tool" in low:
        import re as _re
        # Detect malformed tool call: model embedded JSON args in the function name
        # e.g. "attempted to call tool 'update_automation,{"automation_id": ...}'"
        malformed_match = _re.search(r"attempted to call tool ['\"](\w+)[,{]", raw)
        if malformed_match:
            tool_name = malformed_match.group(1)
            tpl = get_lang_text("err_malformed_tool_call") or (
                "\u26a0\ufe0f The model generated a malformed tool call for '{tool_name}'. "
                "This is a model behavior issue \u2014 please try rephrasing your request or switch to a more capable model."
            )
            return tpl.format(tool_name=tool_name)
        tool_match = _re.search(r"attempted to call tool ['\"](\w+)['\"]", raw)
        tool_name = tool_match.group(1) if tool_match else None
        try:
            tier = tools._get_tool_tier()
        except Exception:
            tier = "unknown"
        if tool_name:
            tpl = get_lang_text("err_tool_not_in_tier") or "\u26a0\ufe0f Current model is in limited mode ({tier}) and does not support '{tool_name}'. Switch to a more powerful model (e.g. Claude, GPT-4o, Gemini)."
            return tpl.format(tier=tier, tool_name=tool_name)
        tpl = get_lang_text("err_tool_not_in_tier_generic") or "\u26a0\ufe0f Current model is in limited mode ({tier}) and does not support this feature. Switch to a more powerful model."
        return tpl.format(tier=tier)

    if provider == "github" and code == 403 and ("budget limit" in low or "reached its budget" in low):
        return get_lang_text("err_github_budget_limit") or (
            "GitHub Models: budget limit reached. Increase budget/credit or switch model/provider."
        )

    if provider == "github_copilot" and (
        "unsupported_api_for_model" in low
        or "/chat/completions endpoint" in low
        or "not accessible via the /chat/completions endpoint" in low
    ):
        return (
            get_lang_text("err_github_copilot_model_incompatible")
            or "GitHub Copilot: selected model is not compatible with the chat endpoint. "
               "Choose a chat-compatible model (e.g. gpt-4.1, gpt-4o, gpt-5.1)."
        )

    if provider == "github" and (code == 413 or "tokens_limit_reached" in low or "request body too large" in low):
        m = re.search(r"max size:\s*(\d+)\s*tokens", (remote_msg or raw), flags=re.IGNORECASE)
        limit = m.group(1) if m else ""
        limit_part = f" (max {limit} token)" if limit else ""
        tpl = get_lang_text("err_github_request_too_large")
        if tpl:
            try:
                return tpl.format(limit_part=limit_part)
            except Exception:
                return tpl
        return "GitHub Models: request too long for selected model." + limit_part

    _CREDITS_URLS = {
        "openrouter": "https://openrouter.ai/settings/credits",
        "openai": "https://platform.openai.com/settings/billing",
        "anthropic": "https://console.anthropic.com/settings/plans",
        "deepseek": "https://platform.deepseek.com",
        "xai": "https://console.x.ai",
        "grok_web": "https://grok.com",
        "groq": "https://console.groq.com",
        "mistral": "https://console.mistral.ai",
        "minimax": "https://platform.minimaxi.com",
        "aihubmix": "https://aihubmix.com",
        "siliconflow": "https://cloud.siliconflow.cn",
        "nvidia": "https://developer.nvidia.com/nim",
    }
    if code == 400 and ("usage limits" in low or "regain access on" in low or "api usage limits" in low):
        date_m = re.search(r"regain access on\s+(\S+)", raw, re.IGNORECASE)
        date_str = date_m.group(1) if date_m else ""
        tpl = get_lang_text("err_api_usage_limits")
        if tpl:
            return tpl.format(date=date_str) if date_str else tpl
        return f"❌ API usage limits reached. Access will be restored on {date_str or '?'}. Switch to another provider in the meantime."
    if code == 402 or "insufficient credits" in low or "insufficient balance" in low or "out of credits" in low or "credit balance is too low" in low or "credit balance" in low:
        base = get_lang_text("err_http_402") or "❌ Insufficient balance. Top up your account credits for this provider."
        url = _CREDITS_URLS.get(provider)
        # Preserve original message if it contains specific details
        if remote_msg and ("credit" in remote_msg.lower() or "balance" in remote_msg.lower() or "billing" in remote_msg.lower()):
            return f"❌ {remote_msg}\n⚠️ {url}" if url else f"❌ {remote_msg}"
        return f"{base}\n⚠️ {url}" if url else base
    if code == 401:
        return get_lang_text("err_http_401") or "Authentication failed (401)."
    if code == 403:
        if provider == "grok_web" and (
            "anti-bot" in low
            or "request rejected by anti-bot rules" in low
            or '"code":7' in low
        ):
            return (
                "Grok Web blocked the request (403 anti-bot). "
                "Use fresh full browser cookies (sso/sso-rw + cf_clearance + __cf_bm) "
                "from the same public IP/network as Home Assistant."
            )
        return get_lang_text("err_http_403") or "Access denied (403)."
    if code == 429 and ("insufficient_quota" in low or "insufficient quota" in low or "exceeded your current quota" in low or "run out of credits" in low):
        base = get_lang_text("err_openai_quota") or "❌ Quota exceeded. Your account has run out of credits. Check your billing details."
        url = _CREDITS_URLS.get(provider)
        return f"{base}\n⚠️ {url}" if url else base
    if code == 429 and provider == "google":
        # Pass through the original Google error message if it contains useful details (e.g. billing URL)
        if remote_msg and ("ai.google.dev" in remote_msg or "billing" in remote_msg.lower() or "quota" in remote_msg.lower()):
            return f"❌ {remote_msg}"
        return get_lang_text("err_google_quota") or "Google Gemini: quota exhausted (429). Wait a minute and retry, or switch to another model/provider."
    if code == 429:
        return get_lang_text("err_http_429") or "Rate limit (429)."

    if code == 413:
        return get_lang_text("err_http_413") or "Request too large (413)."

    # Quota keywords without recognised HTTP code (e.g. code extraction failed)
    if "insufficient_quota" in low or "exceeded your current quota" in low or "run out of credits" in low:
        base = get_lang_text("err_openai_quota") or "❌ Quota exceeded. Your account has run out of credits. Check your billing details."
        url = _CREDITS_URLS.get(provider)
        return f"{base}\n⚠️ {url}" if url else base

    # Fallback: keep the remote message if present, otherwise the raw error
    return remote_msg or raw
