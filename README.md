# 🏠🤖 Claude AI Backend for Home Assistant

Home Assistant Add-on - Chat interface powered by Claude AI integrated directly into your Home Assistant sidebar.

## 🎯 Features

- **Chat Interface**: Direct chat with Claude in the Home Assistant sidebar
- **Multiple Models**: Claude Haiku, Sonnet, or Opus
- **Smart Home Control**: Interact with your lights, automations, sensors, and devices
- **One-Click Install**: Docker add-on with automatic setup
- **Ingress UI**: Secure integration through Home Assistant ingress

## 📋 Requirements

- Home Assistant **2024.1.0+**
- Anthropic Claude API Key
- Home Assistant Long-lived Access Token

## 🚀 Installation

### 1. Add Repository

In Home Assistant:
```
Settings → Add-ons & backups → Add-on store (⋮) → Repositories
→ Add: https://github.com/Bobsilvio/ha-claude
```

### 2. Install Add-on

```
Settings → Add-ons & backups → Add-on store
→ Search "Claude AI Backend" → Install
```

### 3. Configure

1. Open the addon configuration page
2. Add your **HA Token** (Settings → Developer Tools → Long-lived Access Tokens)
3. Add your **Anthropic API Key** from https://console.anthropic.com/
4. Save and **Start** the addon

### 4. Access

Once running, click **"Claude AI"** in the Home Assistant sidebar!

## ⚙️ Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `ha_url` | Home Assistant URL | `http://homeassistant:8123` |
| `api_port` | Backend API port | `5000` |
| `debug_mode` | Enable debug logging | `false` |
| `polling_interval` | Update interval (seconds) | `60` |
| `timeout` | API timeout (seconds) | `30` |
| `max_retries` | Retry attempts | `3` |

## 🆘 Troubleshooting

### "Claude AI" not showing in sidebar
- Restart Home Assistant completely
- Check addon logs for errors
- Verify addon status is "Running"

### Cannot connect to API
- Verify HA Token is correct
- Check network connectivity within Home Assistant
- Review addon logs

### API Key errors
- Verify your Anthropic API key is valid
- Check for expired access tokens

## 📝 License

MIT

## 🤝 Support

Issues? Visit: https://github.com/Bobsilvio/ha-claude/issues

---

**Created with ❤️ for Home Assistant**
