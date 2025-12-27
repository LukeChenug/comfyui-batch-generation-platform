#!/bin/bash
echo "🚀 Building Runner v0.2 for macOS..."

# 清理旧构建
rm -rf build dist Runner.spec

# Build
# 增加显式的 hidden-import 以确保路由和逻辑被打包
pyinstaller --name "Runner" \
    --onefile \
    --paths . \
    --add-data "index.html:." \
    --add-data "runner_v0.2.html:." \
    --add-data "batch_generation_dashboard.html:." \
    --add-data "backend/src/scenes:backend/src/scenes" \
    --hidden-import "uvicorn.logging" \
    --hidden-import "uvicorn.loops" \
    --hidden-import "uvicorn.loops.auto" \
    --hidden-import "uvicorn.protocols" \
    --hidden-import "uvicorn.protocols.http" \
    --hidden-import "uvicorn.protocols.http.auto" \
    --hidden-import "uvicorn.lifespan" \
    --hidden-import "uvicorn.lifespan.on" \
    --hidden-import "engineio.async_drivers.aiohttp" \
    --hidden-import "sqlite3" \
    --hidden-import "backend.src.routes.task_routes" \
    --hidden-import "backend.src.services.task_service" \
    --hidden-import "backend.src.services.workflow_service" \
    --hidden-import "backend.src.database.db" \
    --hidden-import "backend.src.auth" \
    --hidden-import "backend.src.jobs.runner" \
    --hidden-import "backend.src.init_admin" \
    backend/src/simple_main.py

# 检查打包结果
if [ ! -d "dist" ]; then
    echo "❌ Build failed! 'dist' directory not found."
    exit 1
fi

echo "✅ Build complete! Check dist/Runner"

# Zip it
mkdir -p static/downloads
cd dist
mkdir -p Runner-v0.2
mv Runner Runner-v0.2/

# Create a Launch Script
echo '#!/bin/bash
cd "$(dirname "$0")"
./Runner
' > Runner-v0.2/Start.command
chmod +x Runner-v0.2/Start.command

echo "Please double click 'Start.command' to run the console." > Runner-v0.2/README.txt

# 打包
zip -r ../static/downloads/Runner-v0.2-macOS.zip Runner-v0.2
cd ..

echo "📦 Package ready: static/downloads/Runner-v0.2-macOS.zip"
