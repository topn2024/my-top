# 服务器备份 PowerShell 脚本
# 用于Windows服务器的应用备份

param(
    [string]$BackupPath = "C:\backups",
    [string]$AppPath = "C:\topn"
)

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupName = "topn_backup_$Timestamp"
$LogFile = "C:\logs\topn_backup_$Timestamp.log"

# 日志函数
function Write-Log {
    param([string]$Message)
    $LogEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $LogEntry
    $LogEntry | Out-File -FilePath $LogFile -Append
}

# 创建备份目录
function New-BackupDirectory {
    if (-not (Test-Path $BackupPath)) {
        Write-Log "创建备份目录: $BackupPath"
        New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    }
}

# 停止服务
function Stop-ApplicationServices {
    Write-Log "停止应用服务..."

    # 停止可能的Python进程
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*topn*"} | Stop-Process -Force

    # 停止Windows服务（如果有）
    try {
        Stop-Service -Name "TopNApp" -ErrorAction SilentlyContinue
        Stop-Service -Name "TopNWorker" -ErrorAction SilentlyContinue
    } catch {
        Write-Log "Windows服务未找到或已停止"
    }

    Start-Sleep -Seconds 3
    Write-Log "应用服务已停止"
}

# 备份应用代码
function Backup-ApplicationCode {
    Write-Log "备份应用代码..."
    $CodeBackup = Join-Path $BackupPath "$BackupName\_code.zip"

    if (Test-Path $AppPath) {
        # 使用PowerShell压缩文件
        Compress-Archive -Path "$AppPath\*" -DestinationPath $CodeBackup -Force `
            -Exclude "*.git","__pycache__","*.pyc","*.log","venv","node_modules"

        Write-Log "应用代码备份完成: $CodeBackup"
    } else {
        Write-Log "警告: 应用目录不存在: $AppPath"
    }
}

# 备份数据库
function Backup-Database {
    Write-Log "备份数据库..."
    $DatabasePath = Join-Path $AppPath "data\topn.db"
    $DatabaseBackup = Join-Path $BackupPath "$BackupName\_database.db"

    if (Test-Path $DatabasePath) {
        Copy-Item $DatabasePath $DatabaseBackup -Force
        Write-Log "数据库备份完成: $DatabaseBackup"
    } else {
        Write-Log "警告: 数据库文件不存在: $DatabasePath"
    }
}

# 备份配置文件
function Backup-Configuration {
    Write-Log "备份配置文件..."
    $ConfigPath = Join-Path $BackupPath "$BackupName\_config"
    New-Item -ItemType Directory -Path $ConfigPath -Force | Out-Null

    # 备份环境变量文件
    $EnvFile = Join-Path $AppPath ".env"
    if (Test-Path $EnvFile) {
        Copy-Item $EnvFile $ConfigPath -Force
    }

    # 备份服务配置
    if (Test-Path "C:\services\topn\*.xml") {
        Copy-Item "C:\services\topn\*.xml" $ConfigPath -Force
    }

    Write-Log "配置文件备份完成: $ConfigPath"
}

# 生成备份报告
function New-BackupReport {
    Write-Log "生成备份报告..."
    $ReportPath = Join-Path $BackupPath "$BackupName\_report.txt"

    $Report = @"
# 服务器备份报告

## 备份信息
- 备份时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- 备份名称: $BackupName
- 应用路径: $AppPath
- 备份路径: $BackupPath

## 备份文件清单
"@

    # 添加文件信息
    Get-ChildItem $BackupPath -Name "$BackupName*" | ForEach-Object {
        $FilePath = Join-Path $BackupPath $_
        if (Test-Path $FilePath) {
            $Size = [math]::Round((Get-Item $FilePath).Length / 1MB, 2)
            $Report += "`n- $_ ($Size MB)"
        }
    }

    $Report += @"

## 恢复方法
1. 停止当前运行的服务
2. 恢复应用代码: 解压 $BackupName\_code.zip 到应用目录
3. 恢复数据库: 复制 $BackupName\_database.db 到 data\目录
4. 恢复配置: 复制 $BackupName\_config\ 中的配置文件
5. 重启应用服务

## 注意事项
- 请在恢复前备份当前运行状态
- 确认数据库兼容性
- 检查配置文件中的路径设置
"@

    $Report | Out-File -FilePath $ReportPath -Encoding UTF8
    Write-Log "备份报告生成完成: $ReportPath"
}

# 主函数
function Start-Backup {
    Write-Log "=== 开始服务器备份 ==="

    try {
        New-BackupDirectory
        Stop-ApplicationServices
        Backup-ApplicationCode
        Backup-Database
        Backup-Configuration
        New-BackupReport

        Write-Log "=== 服务器备份完成 ==="
        Write-Log "备份位置: $BackupPath"
        Write-Log "备份名称: $BackupName"

        # 显示备份文件
        Write-Host "`n生成的备份文件:"
        Get-ChildItem $BackupPath -Name "$BackupName*" | ForEach-Object {
            $FilePath = Join-Path $BackupPath $_
            $Size = [math]::Round((Get-Item $FilePath).Length / 1MB, 2)
            Write-Host "$_ ($Size MB)"
        }

    } catch {
        Write-Log "备份失败: $($_.Exception.Message)"
        exit 1
    }
}

# 执行备份
Start-Backup