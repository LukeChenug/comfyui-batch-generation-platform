#!/bin/bash

# ComfyUI批量生图平台 - 快速启动脚本
# 一键部署和启动完整的批量生图解决方案

set -e

echo "🎨 ComfyUI批量生图平台 - 快速启动"
echo "=================================="

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ 错误: 未找到Python，请先安装Python 3.7+"
        exit 1
    fi
    
    echo "✅ Python: $($PYTHON_CMD --version)"
}

# 检查pip
check_pip() {
    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        echo "❌ 错误: pip未安装，请先安装pip"
        exit 1
    fi
    
    echo "✅ pip可用"
}

# 安装依赖
install_dependencies() {
    echo "📦 安装Python依赖..."
    
    if [ -f "requirements.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements.txt
        echo "✅ 依赖安装完成"
    else
        echo "⚠️  requirements.txt未找到，手动安装核心依赖..."
        $PYTHON_CMD -m pip install fastapi uvicorn aiohttp websockets pydantic
        echo "✅ 核心依赖安装完成"
    fi
}

# 创建必要目录
setup_directories() {
    echo "📁 创建必要目录..."
    
    mkdir -p generated_images
    mkdir -p logs
    
    echo "✅ 目录创建完成"
}

# 检查ComfyUI连接
check_comfyui_connection() {
    echo "🔗 检查ComfyUI服务器连接..."
    
    COMFYUI_URL="http://117.50.218.83:8188"
    
    if curl -s -f "$COMFYUI_URL" > /dev/null; then
        echo "✅ ComfyUI服务器连接正常: $COMFYUI_URL"
        return 0
    else
        echo "⚠️  ComfyUI服务器连接失败: $COMFYUI_URL"
        echo "💡 请确认ComfyUI服务器地址或修改 comfyui_api_server.py 中的配置"
        return 1
    fi
}

# 启动API服务器
start_api_server() {
    echo "🚀 启动API服务器..."
    
    # 检查端口是否被占用
    if lsof -i:8000 > /dev/null 2>&1; then
        echo "⚠️  端口8000已被占用，尝试停止现有进程..."
        pkill -f "comfyui_api_server" || true
        sleep 2
    fi
    
    # 启动服务器
    if [ -f "comfyui_api_server.py" ]; then
        echo "启动中..."
        nohup $PYTHON_CMD comfyui_api_server.py > logs/api_server.log 2>&1 &
        API_PID=$!
        
        # 等待服务启动
        sleep 3
        
        # 检查服务是否正常启动
        if curl -s -f "http://localhost:8000/health" > /dev/null; then
            echo "✅ API服务器启动成功 (PID: $API_PID)"
            echo "🌐 访问地址: http://localhost:8000"
            echo "📖 API文档: http://localhost:8000/docs"
            return 0
        else
            echo "❌ API服务器启动失败，查看日志："
            tail -n 20 logs/api_server.log
            return 1
        fi
    else
        echo "❌ 错误: comfyui_api_server.py 文件未找到"
        return 1
    fi
}

# 启动Web界面
start_web_interface() {
    echo "🌐 启动Web管理界面..."
    
    if [ -f "batch_generation_dashboard.html" ]; then
        # 检查8080端口
        if lsof -i:8080 > /dev/null 2>&1; then
            echo "⚠️  端口8080已被占用，尝试使用其他端口..."
            WEB_PORT=8081
        else
            WEB_PORT=8080
        fi
        
        # 启动简单HTTP服务器
        nohup $PYTHON_CMD -m http.server $WEB_PORT > logs/web_server.log 2>&1 &
        WEB_PID=$!
        
        sleep 2
        
        echo "✅ Web界面启动成功 (PID: $WEB_PID)"
        echo "🖥️  管理界面: http://localhost:$WEB_PORT/batch_generation_dashboard.html"
        
        return 0
    else
        echo "⚠️  batch_generation_dashboard.html 未找到，跳过Web界面启动"
        return 1
    fi
}

# 运行测试
run_tests() {
    echo "🧪 运行连接测试..."
    
    if [ -f "api_examples.py" ]; then
        # 运行健康检查
        $PYTHON_CMD -c "
import requests
import sys

try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        data = response.json()
        print('✅ API服务健康检查通过')
        print(f'   API服务器: {data[\"api_server\"]}')
        print(f'   ComfyUI服务器: {data[\"comfyui_server\"]}')
        print(f'   活跃任务: {data[\"active_tasks\"]}')
        
        if data['comfyui_server'] == 'offline':
            print('⚠️  ComfyUI服务器离线，部分功能可能不可用')
    else:
        print('❌ API健康检查失败')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ 连接测试失败: {e}')
    sys.exit(1)
"
    else
        echo "⚠️  api_examples.py 未找到，跳过测试"
    fi
}

# 显示使用说明
show_usage_info() {
    echo ""
    echo "🎉 ComfyUI批量生图平台启动完成！"
    echo "=================================="
    echo ""
    echo "📋 访问地址:"
    echo "   🖥️  管理界面: http://localhost:8080/batch_generation_dashboard.html"
    echo "   📖 API文档:  http://localhost:8000/docs"
    echo "   🏥 健康检查: http://localhost:8000/health"
    echo ""
    echo "📁 重要文件:"
    echo "   📊 API日志:  logs/api_server.log"
    echo "   🌐 Web日志:  logs/web_server.log"
    echo "   🖼️  生成图像: generated_images/"
    echo ""
    echo "🔧 常用命令:"
    echo "   查看API日志:   tail -f logs/api_server.log"
    echo "   停止所有服务:  pkill -f 'comfyui_api_server|http.server'"
    echo "   重启服务:      ./quick_start.sh"
    echo ""
    echo "📚 使用示例:"
    echo "   运行API示例:   python api_examples.py"
    echo "   查看详细文档:  cat 批量生图平台部署指南.md"
    echo ""
    echo "💡 提示: 首次使用建议先阅读部署指南了解完整功能"
}

# 主函数
main() {
    echo "开始初始化..."
    
    # 环境检查
    check_python
    check_pip
    
    # 安装和配置
    install_dependencies
    setup_directories
    
    # 启动服务
    echo ""
    echo "🚀 启动服务..."
    
    # 检查ComfyUI连接（非强制）
    check_comfyui_connection || echo "继续启动API服务器..."
    
    # 启动API服务器
    if start_api_server; then
        # 启动Web界面
        start_web_interface || true
        
        # 运行测试
        echo ""
        run_tests
        
        # 显示使用信息
        show_usage_info
        
        echo ""
        echo "✨ 服务启动成功！按 Ctrl+C 查看实时日志"
        
        # 显示实时日志
        tail -f logs/api_server.log
        
    else
        echo "❌ 启动失败，请检查错误信息"
        exit 1
    fi
}

# 信号处理
cleanup() {
    echo ""
    echo "🛑 停止服务..."
    pkill -f "comfyui_api_server" || true
    pkill -f "http.server" || true
    echo "👋 服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 检查命令行参数
case "${1:-start}" in
    "start"|"")
        main
        ;;
    "stop")
        echo "🛑 停止所有服务..."
        pkill -f "comfyui_api_server" || true
        pkill -f "http.server" || true
        echo "✅ 服务已停止"
        ;;
    "restart")
        echo "🔄 重启服务..."
        pkill -f "comfyui_api_server" || true
        pkill -f "http.server" || true
        sleep 2
        main
        ;;
    "status")
        echo "📊 服务状态:"
        if pgrep -f "comfyui_api_server" > /dev/null; then
            echo "   ✅ API服务器: 运行中"
        else
            echo "   ❌ API服务器: 已停止"
        fi
        
        if pgrep -f "http.server" > /dev/null; then
            echo "   ✅ Web服务器: 运行中"
        else
            echo "   ❌ Web服务器: 已停止"
        fi
        ;;
    "logs")
        echo "📊 显示API服务器日志:"
        tail -f logs/api_server.log
        ;;
    "help")
        echo "ComfyUI批量生图平台 - 使用帮助"
        echo ""
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  start    启动所有服务 (默认)"
        echo "  stop     停止所有服务"
        echo "  restart  重启所有服务"  
        echo "  status   查看服务状态"
        echo "  logs     查看API日志"
        echo "  help     显示此帮助"
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac
