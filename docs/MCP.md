# Model Context Protocol (MCP) Setup Guide

Connect custom tools and services to your Amira via **MCP**, following the standard MCP configuration format.

---

## 📌 What is MCP?

MCP (Model Context Protocol) allows your AI to:
- 📁 Access local files and directories
- 🔍 Search the web via Brave Search
- 🔀 Inspect Git repositories 
- 💾 Query databases
- 🤖 Connect to external APIs
- 🖥️ Run custom tools on your system

---

## 🏠 Home Assistant Addon Setup

### Where Configuration Goes

The addon runs in **isolated Docker containers**, so paths matter:

| Path | Accessible | Use For |
|------|-----------|---------|
| `/config/` | ✅ YES | MCP config files, persist data |
| `/config/amira/mcp_config.json` | ✅ YES | **Your MCP configuration** |
| Addon code (`/app/`) | ❌ NO | Don't edit addon internals |

### ⚡ Quick Start (3 Steps)

**Step 1: Create Configuration File**

Open a terminal in Home Assistant (SSH or Settings → System → Terminal):

```bash
cat > /config/amira/mcp_config.json << 'EOF'
{
  "filesystem": {
    "transport": "http",
    "url": "http://YOUR-SERVER-IP:PORT"
  }
}
EOF
```

**Step 2: Verify Configuration**

Check that file exists:
```bash
ls -la /config/mcp_config.json
cat /config/mcp_config.json
```

**Step 3: Restart Addon**

1. Go to **Settings → Add-ons → Amira**
2. Click **Restart**
3. Check logs: You should see `MCP Config: configured`

---

## 🔧 Common MCP Servers

### 1. Filesystem Access (Read/List Files)

Allows AI to read automation files, scripts, configurations.

```json
{
  "filesystem": {
    "command": "uv",
    "args": ["run", "python", "-m", "mcp.server.stdio.filesystem"],
    "env": {
      "MCP_FILESYSTEM_ROOTS": "/config",
      "MCP_ALLOWED_DIRS": "/config:/config/automations:/config/scripts:/config/packages"
    }
  }
}
```

**What it enables:**
- AI can list files in `/config`
- AI can read YAML files (automations, scripts, packages)
- AI can suggest edits to existing files
- Useful for: "Show me all my automations" or "What scripts do I have?"

---

### 2. Web Search (Via Brave Search API)

Enable AI to search the web for real-time information.

```json
{
  "web_search": {
    "command": "python",
    "args": ["-m", "mcp.server.brave_search"],
    "env": {
      "BRAVE_API_KEY": "YOUR_BRAVE_API_KEY_HERE"
    }
  }
}
```

**Get API Key:**
1. Go to [api.search.brave.com](https://api.search.brave.com)
2. Sign up → Get free tier API key
3. Replace `YOUR_BRAVE_API_KEY_HERE` with your key

**What it enables:**
- "What's the weather forecast for tomorrow?"
- "Find recent news about X"
- "Search for home automation tips"

---

### 3. Git Repository Access

Let AI inspect git history, branches, commits (if you version-control your HA config).

```json
{
  "git": {
    "command": "python",
    "args": ["-m", "mcp.server.git"],
    "env": {
      "GIT_REPOSITORY_PATH": "/config"
    }
  }
}
```

**What it enables:**
- "When did I last edit this automation?"
- "Show me recent changes to my config"
- "Compare this with the previous version"

---

### 4. Slack Integration

Post messages and read Slack channels from within your assistant.

```json
{
  "slack": {
    "command": "uvx",
    "args": ["mcp-server-slack"],
    "env": {
      "SLACK_BOT_TOKEN": "xoxb-YOUR-SLACK-BOT-TOKEN"
    }
  }
}
```

**Get Token:**
1. Create Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable "Socket Mode"
3. Add bot token scopes: `chat:write`, `channels:read`, `users:read`
4. Copy token starting with `xoxb-`

---

### 5. GitHub Integration

Connect to your GitHub repositories (check issues, PRs, docs).

```json
{
  "github": {
    "command": "uvx",
    "args": ["mcp-server-github", "--repository", "owner/repo"],
    "env": {
      "GITHUB_TOKEN": "ghp_YOUR-PERSONAL-ACCESS-TOKEN"
    }
  }
}
```

**Get Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Create new token with scopes: `repo`, `read:org`
3. Copy token (`ghp_...`)

---

### 6. SQLite Database Access

Query and modify SQLite databases.

```json
{
  "sqlite": {
    "command": "uvx",
    "args": ["mcp-server-sqlite", "/config/my_database.db"],
    "env": {}
  }
}
```

**What it enables:**
- "Query my history database"
- "Show sensor readings from the last week"
- "Save this data to database"

---

## 🧩 Multiple Servers at Once

You can enable multiple MCP servers in one config file:

```json
{
  "filesystem": {
    "command": "uv",
    "args": ["run", "python", "-m", "mcp.server.stdio.filesystem"],
    "env": {
      "MCP_FILESYSTEM_ROOTS": "/config",
      "MCP_ALLOWED_DIRS": "/config"
    }
  },
  "web_search": {
    "command": "python",
    "args": ["-m", "mcp.server.brave_search"],
    "env": {
      "BRAVE_API_KEY": "YOUR_KEY_HERE"
    }
  },
  "git": {
    "command": "python",
    "args": ["-m", "mcp.server.git"],
    "env": {
      "GIT_REPOSITORY_PATH": "/config"
    }
  }
}
```

---

## ✅ Verify Setup is Working

### Check Logs

1. Go to **Settings → Add-ons → Amira**
2. Click **Logs** tab
3. You should see:
   ```
   MCP Config: configured
   ```

### Test in Chat

Ask your AI:
- "List my config files" (tests filesystem)
- "Search the web for ..." (tests web_search)
- "When did I last modify X?" (tests git)

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"MCP Config: not configured"** | Check `/config/amira/mcp_config.json` exists and is valid JSON |
| **JSON syntax error** | Use [jsonlint.com](https://www.jsonlint.com) to validate your JSON |
| **API key errors** | Verify keys are correct, not expired, not revoked |
| **"Permission denied"** | MCP path must be readable from `/config/` |
| **AI doesn't use tools** | Check MCP section appears in addon logs on restart |
| **Tool doesn't work** | Verify server `command` is installed (python, uv, npm) |

---

## 📝 Example: Full Featured Setup

```json
{
  "filesystem": {
    "command": "uv",
    "args": ["run", "python", "-m", "mcp.server.stdio.filesystem"],
    "env": {
      "MCP_FILESYSTEM_ROOTS": "/config",
      "MCP_ALLOWED_DIRS": "/config:/config/automations:/config/scripts:/config/packages:/config/www"
    }
  },
  "web_search": {
    "command": "python",
    "args": ["-m", "mcp.server.brave_search"],
    "env": {
      "BRAVE_API_KEY": "YOUR_BRAVE_API_KEY"
    }
  },
  "git": {
    "command": "python",
    "args": ["-m", "mcp.server.git"],
    "env": {
      "GIT_REPOSITORY_PATH": "/config"
    }
  }
}
```

---

## 🔐 Security Notes

- **Never commit** `/config/amira/mcp_config.json` to git if it contains API keys
- Add to `.gitignore`:
  ```
  /config/amira/mcp_config.json
  ```
- API keys in environment variables are isolated to the addon container
- File access is restricted to paths in `MCP_ALLOWED_DIRS`

---

## 📚 More Info

- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Claude Desktop MCP Setup](https://modelcontextprotocol.io/docs/tools/client)
- [MCP Server Directory](https://github.com/modelcontextprotocol/servers)

