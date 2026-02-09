# Claude AI Backend Add-on for Home Assistant

✨ **Complete all-in-one add-on** that automatically installs the Claude custom component AND runs the backend API.

## What This Add-on Does

1. ✓ Deploys the Claude custom component automatically
2. ✓ Starts the backend Flask API on port 5000
3. ✓ Reloads Home Assistant to register the component
4. ✓ Ready to use in seconds!

## Installation (4 Simple Steps)

### Step 1: Add Repository
1. **Settings** → **Add-ons & backups** → **Add-on store**
2. Click **⋮** (menu) in top-right
3. **Repositories**
4. Add: `https://github.com/Bobsilvio/ha-claude`
5. **Create**

### Step 2: Install Add-on
1. **Settings** → **Add-ons**
2. Search for **"Claude AI Backend"**
3. Click **Install**

### Step 3: Configure
1. Click on **"Claude AI Backend"**
2. Go to **Configuration** tab
3. Add your **Home Assistant Long-lived Token**:
   - Go to Settings → Developer Tools → Long-lived Access Tokens
   - Click **Create Token**
   - Name it "Claude Backend"
   - Copy token
   - Paste in add-on configuration
4. Click **Save**

### Step 4: Start
1. Click **Start**
2. Watch logs - you'll see:
   ```
   ✓ Component deployed
   ✓ Home Assistant reloaded
   ✓ Claude AI Backend is ready!
   ```
3. Done! 🎉

## Configure Claude Integration

The component is now installed. Create the integration:

1. **Settings** → **Devices & Services** → **Integrations**
2. Click **Create Integration**
3. Search for **"Claude"**
4. **API Endpoint**: `http://localhost:5000`
5. **Model**: Choose your preference (Haiku/Sonnet/Opus)
6. **Submit**

**You're ready to use Claude!** 🚀

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
| enable_file_access | false | Enable access to Home Assistant configuration files (read/write) |
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
