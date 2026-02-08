# 🚀 ALL-IN-ONE Installation (16 minutes!)

## What Happens

When you install the Claude add-on, **automatically**:
1. ✅ Deploys the Claude custom component
2. ✅ Starts the backend API on port 5000
3. ✅ Reloads Home Assistant
4. ✅ Everything is ready!

**No manual copying, no scripts, no waiting.**

---

## Installation Steps

### Step 1: Add Repository (5 min)
```
Settings → Add-ons & backups → Add-on store ⋮ → Repositories
Add: https://github.com/Bobsilvio/ha-claude
Create
```

### Step 2: Install Add-on (7 min)
```
Settings → Add-ons
Search "Claude AI Backend"
Install (wait for Docker image...)
```

### Step 3: Configure
```
Tab: Configuration
Add HA Token (Settings → Developer Tools → Long-lived tokens)
Save
```

### Step 4: Start
```
Click Start
Watch logs:
  ✓ Component deployed
  ✓ Home Assistant reloaded
  ✓ Claude AI Backend is ready!

Wait for Status = Running ✅
```

### Step 5: Create Integration
```
Settings → Devices & Services → Create Integration
Search: Claude
API Endpoint: http://localhost:5000
Model: Choose (Haiku/Sonnet/Opus)
Submit → Done! 🎉
```

---

## That's It!

Your Claude AI integration is **ready to use**!

Try it:
```yaml
service: claude.send_message
data:
  message: "Turn on the living room lights"
```

---

## Why This Is Fast

| Old Way | Now |
|---------|-----|
| Copy component manually | ✅ Auto |
| Copy backend manually | ✅ Auto |
| Run Python script | ✅ Auto |
| Configure on reboot | ✅ Auto restarts |
| **Time: 30+ minutes** | **Time: 16 minutes** |

---

## Issues?

See [docs/INSTALLATION.md](docs/INSTALLATION.md) → Troubleshooting section

---

**Done!** Now enjoy your AI-powered home! 🏠🤖
