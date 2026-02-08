# Claude AI Backend Add-on for Home Assistant

Home Assistant add-on that provides the backend API for Claude AI Assistant integration.

## Installation

1. **Add Repository to Home Assistant**:
   - Settings → Add-ons → Repositories
   - Add: `https://github.com/Bobsilvio/ha-claude-addon-repo`
   - Click "Create"

2. **Install Add-on**:
   - Settings → Add-ons → Claude AI Backend
   - Click "Install"

3. **Configure Add-on**:
   - Click on "Claude AI Backend"
   - Go to "Configuration" tab
   - Add your Home Assistant Long-lived Token:
     - Go to Settings → Developer Tools → Long-lived access tokens
     - Create a new token
     - Paste it in add-on configuration
   - Save

4. **Start Add-on**:
   - Click "Start" button
   - The add-on will start on port 5000

5. **Configure Claude Integration**:
   - Settings → Devices & Services → Create Integration
   - Search for "Claude"
   - API Endpoint: `http://localhost:5000`
   - Select your preferred model
   - Click "Submit"

## Configuration

### Basic Configuration

```yaml
ha_token: "your_long_lived_token_here"
api_port: 5000
debug_mode: false
```

### Advanced Configuration

```yaml
ha_token: "your_long_lived_token_here"
ha_url: "http://homeassistant:8123"
api_port: 5000
debug_mode: true
polling_interval: 60
timeout: 30
max_retries: 3
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| ha_token | - | Your Home Assistant long-lived access token (required) |
| ha_url | http://homeassistant:8123 | Home Assistant URL |
| api_port | 5000 | Port for the API server |
| debug_mode | false | Enable debug logging |
| polling_interval | 60 | Seconds between entity updates |
| timeout | 30 | API request timeout in seconds |
| max_retries | 3 | Number of retries for failed requests |

## Getting Your Token

1. Go to Home Assistant Settings
2. Select "Developer Tools"
3. Go to "Long-lived Access Tokens" tab
4. Click "Create Token"
5. Give it a name (e.g., "Claude Backend")
6. Copy the token
7. Paste in add-on configuration

## Troubleshooting

### Add-on won't start
- Check logs: Settings → Add-ons → Claude AI Backend → Logs
- Ensure HA_TOKEN is set correctly
- Check internet connectivity

### "Cannot connect to API" error in Claude Integration
- Verify add-on is running: Settings → Add-ons → Claude AI Backend → Status shows "Running"
- Check logs for errors
- Try API health check: `curl http://localhost:5000/health`

### Integration can't connect to Home Assistant
- Check HA_TOKEN is valid (re-create if needed)
- Verify HA URL is correct in configuration
- Check port 8123 is accessible

## Architecture

```
┌─────────────────────────────────────┐
│  Home Assistant (Core)              │
│  ├── Claude Integration (Component) │
│  │   └── Calls API on :5000        │
│  │                                 │
│  └── Claude AI Backend (Add-on)     │
│      └── Runs on :5000             │
│          └── Controls HA via API   │
└─────────────────────────────────────┘
```

## Support

- GitHub Issues: https://github.com/Bobsilvio/ha-claude/issues
- Documentation: https://github.com/Bobsilvio/ha-claude
- Home Assistant Community: https://community.home-assistant.io/

## License

MIT License - See LICENSE file in main repository
