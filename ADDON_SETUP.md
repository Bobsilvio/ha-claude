# Setup Guide - Home Assistant Add-on Repository

## How to Create Your Add-on Repository

### Step 1: Create GitHub Repository

1. Go to GitHub.com
2. Create new repository: `ha-claude-addon-repo`
3. Clone it locally:
   ```bash
   git clone https://github.com/your-username/ha-claude-addon-repo.git
   cd ha-claude-addon-repo
   ```

### Step 2: Copy Add-on Files

```bash
# From this repo, copy the addons folder structure
cp -r addons/ ha-claude-addon-repo/
cp repository.json ha-claude-addon-repo/
```

Your repo structure should be:
```
ha-claude-addon-repo/
├── addons/
│   └── claude-backend/
│       ├── addon.yaml
│       ├── Dockerfile
│       ├── run.sh
│       ├── requirements.txt
│       └── README.md
├── repository.json
└── README.md
```

### Step 3: Update Files

Edit `repository.json`:
```json
{
  "name": "Claude AI Backend",
  "url": "https://github.com/Bobsilvio/ha-claude-addon-repo",
  "maintainer": "Bobsilvio"
}
```

Edit `addons/claude-backend/addon.yaml`:
```yaml
image: "ghcr.io/Bobsilvio/claude-backend:{VERSION}"
...
documentation: "https://github.com/Bobsilvio/ha-claude"
support: "https://github.com/Bobsilvio/ha-claude/issues"
maintainers:
  - Bobsilvio
```

### Step 4: Push to GitHub

```bash
cd ha-claude-addon-repo
git add .
git commit -m "Initial Claude AI Backend add-on"
git push origin main
```

### Step 5: Use in Home Assistant

In Home Assistant:

1. Settings → Add-ons & backups → Add-ons menu (⋮) → Repositories
2. Add: `https://github.com/YOUR-USERNAME/ha-claude-addon-repo`
3. Click "Create"
4. Go back to Add-ons
5. Search for "Claude AI Backend"
6. Install!

## Docker Image Registry

To push to GitHub Container Registry (GHCR):

```bash
# Login
docker login ghcr.io -u Bobsilvio

# Build and push (from addons/claude-backend/)
docker buildx build \
  --push \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t ghcr.io/Bobsilvio/claude-backend:1.0.0 \
  .
```

## Troubleshooting

### Add-on not appearing in Home Assistant

1. Verify repository URL is exactly correct
2. Go to Settings → System → Updates → Check for updates
3. Restart Home Assistant

### Build fails for ARM architectures

- Install buildx: `docker buildx create --use`
- Ensure QEMU is installed for multi-platform builds

### OAuth/Authentication issues

- Generate GitHub token with `repo` and `read:packages` scopes
- Use token for login: `docker login ghcr.io -u Bobsilvio -p YOUR-TOKEN`

## Support

For issues related to the add-on:
- GitHub Issues: https://github.com/Bobsilvio/ha-claude/issues
- Home Assistant Community: https://community.home-assistant.io/

## References

- Home Assistant Add-ons: https://developers.home-assistant.io/docs/add-ons/
- Add-on Development: https://developers.home-assistant.io/docs/add-ons/development/
- Add-on Repository: https://developers.home-assistant.io/docs/add-ons/repository/
