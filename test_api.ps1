# PowerShell测试脚本
Write-Host "测试API编码..." -ForegroundColor Green

# 测试模型API
$response = Invoke-WebRequest -Uri "http://39.105.12.124/api/models" -UseBasicParsing
Write-Host "`n状态码: $($response.StatusCode)" -ForegroundColor Cyan

# 显示原始内容（前500字符）
$content = $response.Content
Write-Host "`n原始响应内容:" -ForegroundColor Yellow
Write-Host $content.Substring(0, [Math]::Min(500, $content.Length))

# 检查是否有Unicode转义
if ($content -match '\u[0-9a-fA-F]{4}') {
    Write-Host "`n❌ 发现Unicode转义序列 - 编码有问题" -ForegroundColor Red
} else {
    Write-Host "`n✅ 没有Unicode转义 - 中文编码正常" -ForegroundColor Green
}

# 解析JSON
$data = $response.Content | ConvertFrom-Json
if ($data.models) {
    Write-Host "`n第一个模型:" -ForegroundColor Cyan
    Write-Host "  名称: $($data.models[0].name)"
    Write-Host "  描述: $($data.models[0].description)"
}
