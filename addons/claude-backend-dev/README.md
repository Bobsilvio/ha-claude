# AI Assistant for Home Assistant (Add-on)

This add-on provides the **AI Assistant web UI** (via Home Assistant Ingress) and the **backend API** that can read states, call services, and optionally edit configuration files.

**No Home Assistant long-lived token is required**: the add-on uses the Supervisor-managed Home Assistant API access.

## What you get

- Sidebar chat UI with streaming responses
- Multi-provider agents: **Anthropic**, **OpenAI**, **Google Gemini**, **NVIDIA NIM**, **GitHub Models**
- Optional **File Access** with automatic snapshots + restore

## Installation

1. Add repository: **Settings → Add-ons & Backups → Add-on Store → ⋮ → Repositories**
2. Add: `https://github.com/Bobsilvio/ha-claude`
3. Install **AI Assistant for Home Assistant**

## Configuration

1. Open the add-on **Configuration** tab
2. Paste **at least one provider key** (Anthropic / OpenAI / Google / NVIDIA / GitHub)
3. (Optional) Set **Language** and enable **File Access**
4. **Save** and **Start**

## First run (important)

Open **AI Assistant** from the sidebar and select an **agent/model** from the dropdown at the top.
The selection is saved automatically and persists across restarts.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| anthropic_api_key | - | Anthropic API key |
| openai_api_key | - | OpenAI API key |
| google_api_key | - | Google Gemini API key |
| github_token | - | GitHub fine-grained token for GitHub Models |
| nvidia_api_key | - | NVIDIA NIM API key |
| nvidia_thinking_mode | false | Extra reasoning tokens (when supported) |
| colored_logs | true | Attiva i log colorati e leggibili nella console dell'add-on. Consigliato per debug e sviluppo. |
| language | en | UI/assistant language (en/it/es/fr) |
| enable_file_access | false | Allow read/write of files under `/config` |
| debug_mode | false | Enable debug logging |
| timeout | 30 | Provider request timeout (seconds) |
| max_retries | 3 | Retry attempts for transient failures |

## Troubleshooting

### Sidebar item not visible
- Restart Home Assistant
- Ensure the add-on is **Running**
- Check add-on logs

### 401 / Home Assistant API issues
- The Supervisor token is managed automatically
- Open `/api/status` to check `ha_connection_ok`
- Restart the add-on and re-check logs

### File Access not working
- Set **enable_file_access: true**, save, restart the add-on
- Verify files exist under `/config/`

## Support

- Issues: https://github.com/Bobsilvio/ha-claude/issues
- Documentation: https://github.com/Bobsilvio/ha-claude
