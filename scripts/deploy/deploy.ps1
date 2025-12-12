# PowerShell 部署脚本
# 用于将修复后的应用部署到服务器

$SERVER = "39.105.12.124"
$USER = "u_topn"
$PASSWORD = "TopN@2024"
$DEPLOY_DIR = "/home/u_topn/TOP_N"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "  部署 TOP_N 平台到服务器 (修复版本)" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 转换密码为安全字符串
$SecurePassword = ConvertTo-SecureString $PASSWORD -AsPlainText -Force
$Credential = New-Object System.Management.Automation.PSCredential ($USER, $SecurePassword)

Write-Host "【1】上传修复后的文件到服务器..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

# 使用 pscp (PuTTY) 或 scp
$pscpPath = "pscp.exe"
$files = @(
    @{Source="backend\app_with_upload.py"; Dest="${USER}@${SERVER}:${DEPLOY_DIR}/backend/app_with_upload.py"},
    @{Source="backend\app.py"; Dest="${USER}@${SERVER}:${DEPLOY_DIR}/backend/app.py"},
    @{Source="requirements.txt"; Dest="${USER}@${SERVER}:${DEPLOY_DIR}/requirements.txt"}
)

Write-Host "提示: 需要手动输入密码: TopN@2024" -ForegroundColor Cyan
Write-Host ""

foreach ($file in $files) {
    Write-Host "上传 $($file.Source)..." -ForegroundColor Gray
    # 使用 scp 命令
    & scp -o StrictHostKeyChecking=no $file.Source $file.Dest
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $($file.Source) 上传成功" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($file.Source) 上传失败" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "【2】在服务器上执行部署命令..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

$commands = @"
cd ${DEPLOY_DIR}
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart topn
sleep 3
sudo systemctl status topn --no-pager | head -20
sudo journalctl -u topn -n 20 --no-pager
"@

Write-Host "执行远程命令..." -ForegroundColor Gray
Write-Host ""

# 保存命令到临时文件
$commands | Out-File -FilePath "temp_deploy_commands.sh" -Encoding ASCII

Write-Host "请手动执行以下命令完成部署:" -ForegroundColor Cyan
Write-Host ""
Write-Host "ssh ${USER}@${SERVER}" -ForegroundColor White
Write-Host "密码: ${PASSWORD}" -ForegroundColor White
Write-Host ""
Write-Host "然后在服务器上执行:" -ForegroundColor Cyan
Write-Host "cd ${DEPLOY_DIR}" -ForegroundColor White
Write-Host "source venv/bin/activate" -ForegroundColor White
Write-Host "pip install -r requirements.txt --upgrade" -ForegroundColor White
Write-Host "sudo systemctl restart topn" -ForegroundColor White
Write-Host "sudo systemctl status topn" -ForegroundColor White
Write-Host "sudo journalctl -u topn -n 30 --no-pager" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  部署脚本准备完成" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
