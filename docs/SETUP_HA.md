# Amira — Setup Guide

---

## Prerequisites

- Home Assistant with Supervisor (2024.1+)
- API key for at least one AI provider
- 2GB+ RAM recommended

---

## Installation

1. **Add repository** — Settings → Add-ons → Add-on Store → ⋮ → Repositories → add `https://github.com/Bobsilvio/ha-claude`
2. **Install** — search "Amira" → click Install
3. **Configure** — go to **Configuration** tab, paste at least one API key, set language if needed, Save
4. **Start** — click Start, then open Amira from the sidebar

> First time? Groq and Google Gemini both have free tiers and require no credit card.

---

## Optional Features

Enable these in the **Configuration** tab:

| Feature | Setting | Guide |
|---------|---------|-------|
| Telegram bot | `telegram_bot_token` | [MESSAGING.md](MESSAGING.md) |
| WhatsApp (Twilio) | `twilio_account_sid` + others | [MESSAGING.md](MESSAGING.md) → [WHATSAPP.md](WHATSAPP.md) |
| MCP custom tools | create `/config/amira/mcp_config.json` | [MCP.md](MCP.md) |
| File read/write | `enable_file_access: true` | — |
| Persistent memory | `enable_memory: true` | — |
| Floating chat bubble | `enable_chat_bubble: true` | — |
| Document upload (PDF/DOCX) | `enable_file_upload: true` | — |

Full configuration reference: [DOCS.md](../addons/claude-backend/DOCS.md)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Amira not in sidebar | Restart HA, clear browser cache |
| "Invalid API key" | Check key has no extra spaces, correct provider selected |
| File access not working | Set `enable_file_access: true`, restart |
| MCP not loading | Validate JSON at `/config/amira/mcp_config.json` |

Logs: **Settings → Add-ons → Amira → Logs**

Issues: [github.com/Bobsilvio/ha-claude/issues](https://github.com/Bobsilvio/ha-claude/issues)
