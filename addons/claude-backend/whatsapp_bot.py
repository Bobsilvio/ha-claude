"""WhatsApp Integration via Twilio.

Receives messages via webhook and sends responses.
Requires Twilio account with WhatsApp Business setup.
"""

import hmac
import hashlib
import logging
import requests
from base64 import b64encode
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts"


class WhatsAppBot:
    """WhatsApp bot handler via Twilio."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """Initialize WhatsApp bot.

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: WhatsApp sender number (e.g., whatsapp:+14155552671)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        # Twilio expects WhatsApp addresses in the form: "whatsapp:+E164"
        from_number = (from_number or "").strip()
        if from_number and not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number.replace('whatsapp:', '')}"
        self.from_number = from_number
        self.enabled = bool(account_sid and auth_token and from_number)

    def send_message(self, to_number: str, text: str) -> bool:
        """Send WhatsApp message via Twilio.

        Args:
            to_number: Recipient WhatsApp number (e.g., whatsapp:+39123456789)
            text: Message text (max 1600 chars)

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.warning("WhatsApp not configured")
            return False

        try:
            # Ensure proper format — strip spaces, then prefix with whatsapp:
            to_number = to_number.strip().replace("whatsapp:", "").strip()
            to_number = f"whatsapp:{to_number}"

            url = f"{TWILIO_API}/{self.account_sid}/Messages.json"
            data = {
                "From": self.from_number,
                "To": to_number,
                "Body": text[:1600]  # WhatsApp max 1600 chars
            }

            resp = requests.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=10
            )

            if resp.status_code in (200, 201):
                logger.debug(f"WhatsApp message sent to {to_number}")
                return True
            else:
                logger.error(f"Twilio error: {resp.status_code} - {resp.text}")
                return False

        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return False

    def validate_webhook_signature(
        self,
        url: str,
        params: Dict[str, Any],
        signature: str,
        *,
        skip_if_empty: bool = True,
    ) -> bool:
        """Validate Twilio webhook signature.

        Twilio signs requests using HMAC-SHA1 over the full callback URL +
        sorted POST parameters.  When Amira runs behind a reverse proxy
        (Nginx, Nabu Casa, ngrok…) Flask reconstructs the URL from internal
        headers, which may differ from the public URL that Twilio actually
        called.  We therefore try **two** candidate URLs:

          1. The URL passed in (already reconstructed by Flask or the caller).
          2. The same URL but with the scheme forced to ``https`` — the most
             common mismatch when the proxy terminates TLS.

        If neither candidate matches AND ``skip_if_empty`` is True *and* the
        signature header is absent/empty (Twilio Sandbox sometimes omits it
        during initial testing), we accept the request and log a warning so
        you can see it in the addon logs.

        Args:
            url:           Full request URL as seen by Flask.
            params:        POST form parameters as a plain dict.
            signature:     Value of the ``X-Twilio-Signature`` header.
            skip_if_empty: Accept the request when the signature header is
                           completely absent (useful for Sandbox testing).

        Returns:
            True if the signature is valid (or absent and skip_if_empty=True).
        """
        # ── No signature at all ─────────────────────────────────────────────
        if not signature:
            if skip_if_empty:
                logger.warning(
                    "WhatsApp webhook: X-Twilio-Signature absent — "
                    "accepting (sandbox/test mode). "
                    "Set TWILIO_SKIP_SIG_CHECK=false to enforce validation."
                )
                return True
            logger.warning("WhatsApp webhook: missing X-Twilio-Signature")
            return False

        # ── Build sorted param string (same for all candidate URLs) ─────────
        param_str = "".join(
            str(k) + str(v if v is not None else "")
            for k, v in sorted(params.items())
        )

        def _check(candidate_url: str) -> bool:
            data = (candidate_url + param_str).encode()
            expected = b64encode(
                hmac.new(self.auth_token.encode(), data, hashlib.sha1).digest()
            ).decode()
            return hmac.compare_digest(expected, signature)

        # ── Candidate 1: URL as-is ──────────────────────────────────────────
        if _check(url):
            return True

        # ── Candidate 2: force https scheme ────────────────────────────────
        if url.startswith("http://"):
            https_url = "https://" + url[len("http://"):]
            if _check(https_url):
                logger.debug("WhatsApp webhook: signature matched with https URL")
                return True

        # ── Candidate 3: strip port (some proxies add :5010 to Host) ────────
        import re as _re
        stripped = _re.sub(r":\d+(/|$)", r"\1", url)
        if stripped != url and _check(stripped):
            logger.debug("WhatsApp webhook: signature matched after stripping port")
            return True
        if stripped.startswith("http://"):
            stripped_https = "https://" + stripped[len("http://"):]
            if _check(stripped_https):
                logger.debug("WhatsApp webhook: signature matched (https + stripped port)")
                return True

        logger.warning(
            f"WhatsApp webhook: signature mismatch. "
            f"Tried url={url!r}. "
            "Check that the webhook URL in Twilio matches your public HA URL exactly."
        )
        return False

    def parse_webhook(self, form_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse incoming webhook message.

        Args:
            form_data: Form data from Twilio webhook

        Returns:
            Dict with from_number, message_id, text or None if invalid
        """
        try:
            return {
                "from": form_data.get("From", "").replace("whatsapp:", "").strip(),
                "message_id": form_data.get("MessageSid", ""),
                "text": form_data.get("Body", "").strip(),
                "num_media": int(form_data.get("NumMedia", 0))
            }
        except Exception as e:
            logger.error(f"Webhook parse error: {e}")
            return None


# Global instance
_bot: Optional[WhatsAppBot] = None


def get_whatsapp_bot(account_sid: str, auth_token: str, from_number: str) -> Optional[WhatsAppBot]:
    """Get or create WhatsApp bot instance."""
    global _bot
    if account_sid and auth_token and from_number and not _bot:
        _bot = WhatsAppBot(account_sid, auth_token, from_number)
    return _bot
