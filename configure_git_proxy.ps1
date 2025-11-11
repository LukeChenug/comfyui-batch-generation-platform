# Git代理配置脚本
# 使用方法: .\configure_git_proxy.ps1

Write-Host "=== Git 代理配置工具 ===" -ForegroundColor Green
Write-Host ""

# 检查当前代理配置
Write-Host "当前代理配置:" -ForegroundColor Yellow
$currentHttpProxy = git config --global --get http.proxy
$currentHttpsProxy = git config --global --get https.proxy

if ($currentHttpProxy) {
    Write-Host "HTTP代理: $currentHttpProxy" -ForegroundColor Cyan
} else {
    Write-Host "HTTP代理: 未配置" -ForegroundColor Gray
}

if ($currentHttpsProxy) {
    Write-Host "HTTPS代理: $currentHttpsProxy" -ForegroundColor Cyan
} else {
    Write-Host "HTTPS代理: 未配置" -ForegroundColor Gray
}

Write-Host ""

# 询问用户代理信息
Write-Host "请选择代理类型:" -ForegroundColor Yellow
Write-Host "1. HTTP/HTTPS 代理 (例如: http://127.0.0.1:7890)" -ForegroundColor Cyan
Write-Host "2. SOCKS5 代理 (例如: socks5://127.0.0.1:1080)" -ForegroundColor Cyan
Write-Host "3. 清除代理配置" -ForegroundColor Cyan
Write-Host "4. 取消" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "请输入选项 (1-4)"

switch ($choice) {
    "1" {
        $proxyUrl = Read-Host "请输入HTTP/HTTPS代理地址 (例如: http://127.0.0.1:7890)"
        if ($proxyUrl) {
            git config --global http.proxy $proxyUrl
            git config --global https.proxy $proxyUrl
            Write-Host "✓ 已配置HTTP/HTTPS代理: $proxyUrl" -ForegroundColor Green
        }
    }
    "2" {
        $proxyUrl = Read-Host "请输入SOCKS5代理地址 (例如: socks5://127.0.0.1:1080)"
        if ($proxyUrl) {
            git config --global http.proxy $proxyUrl
            git config --global https.proxy $proxyUrl
            Write-Host "✓ 已配置SOCKS5代理: $proxyUrl" -ForegroundColor Green
        }
    }
    "3" {
        git config --global --unset http.proxy
        git config --global --unset https.proxy
        Write-Host "✓ 已清除代理配置" -ForegroundColor Green
    }
    "4" {
        Write-Host "已取消" -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "无效选项" -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "测试GitHub连接..." -ForegroundColor Yellow
try {
    $testResult = git ls-remote --heads origin 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "连接成功！" -ForegroundColor Green
    } else {
        Write-Host "连接失败，请检查代理配置和网络连接" -ForegroundColor Red
        Write-Host "错误信息:" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor Red
    }
} catch {
    Write-Host "连接测试出错" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

