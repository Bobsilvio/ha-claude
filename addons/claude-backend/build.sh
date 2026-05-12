#!/bin/bash

# Build script for Home Assistant Add-on

VERSION=$(grep '^version:' config.yaml | sed 's/version: *"\?\([^"]*\)"\?/\1/')
IMAGE_NAME="claude-backend"
REGISTRY="ghcr.io"
NAMESPACE="Bobsilvio"

echo "Building Claude Backend Add-on..."
echo "Version: $VERSION"
echo "Image: $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION"

# Remove macOS AppleDouble metadata files (._*) before building
find . -name '._*' -delete 2>/dev/null || true
echo "Cleaned up macOS AppleDouble files."

# Build for multiple architectures
docker buildx build \
  --push \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t "$REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION" \
  -t "$REGISTRY/$NAMESPACE/$IMAGE_NAME:latest" \
  .

echo "Build complete!"
echo ""
echo "Add-on repository structure:"
echo "your-addon-repo/"
echo "├── addons/"
echo "│   └── claude-backend/"
echo "│       ├── addon.yaml"
echo "│       ├── Dockerfile"
echo "│       ├── run.sh"
echo "│       ├── requirements.txt"
echo "│       └── README.md"
echo "├── repository.json"
echo "└── README.md"
