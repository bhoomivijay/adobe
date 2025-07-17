#!/bin/bash

echo "🚀 Building Docker image..."
docker build --platform=linux/amd64 -t outlineextractor:latest .

echo "✅ Build complete!"

echo "📂 Making sure input and output folders exist..."
mkdir -p input output

echo "🔍 Running container..."
docker run --platform=linux/amd64 --rm \
    -v "$(pwd)/input:/app/input" \
    -v "$(pwd)/output:/app/output" \
    --network none \
    outlineextractor:latest

echo "✅ Processing done! Check output folder:"
ls output/

echo "📄 Sample output content:"
cat output/*.json


