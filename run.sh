#!/bin/bash
set -e

echo "🚀 Building Docker image..."
docker build --platform=linux/amd64 -t outlineextractor:latest .

echo "✅ Build complete!"
mkdir -p input output

echo "🔍 Running container..."
docker run --platform=linux/amd64 --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  --network none \
  outlineextractor:latest

echo "✅ Done. Output files:"
ls output/
echo "📄 Preview first output file (if any):"
cat output/* 2>/dev/null || true
