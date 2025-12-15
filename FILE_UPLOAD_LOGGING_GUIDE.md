# 文件上传日志记录指南

## 概述

文件上传功能现在具有完整的日志记录链路，从 API 接收请求到文件保存再到文本提取，每个环节都有详细的日志输出。

## 日志层级说明

### 使用的日志符号

- ✓ - 操作成功
- ✗ - 操作失败
- 无符号 - 信息性日志

### 日志级别

- `INFO` - 正常流程信息（文件接收、保存成功、提取成功等）
- `WARNING` - 警告信息（文件名被清理、提取结果为空等）
- `ERROR` - 错误信息（文件不存在、提取失败、格式不支持等）
- `DEBUG` - 调试信息（编码尝试、分页提取进度等）

## 完整日志链路

### 1. API 层 (`backend/blueprints/api.py`)

**位置**: `/api/upload` 路由

**日志输出**:

```
# 开始阶段
INFO - Upload request for file: 公司简介.docx, size: 12345

# 保存成功
INFO - File saved successfully: /home/u_topn/TOP_N/uploads/upload_1702632145.docx

# 提取成功
INFO - ✓ Upload complete: file=公司简介.docx, text_length=1500

# 异常情况
WARNING - Upload attempt with no file
ERROR - File save failed: 不支持的文件类型
ERROR - Text extraction failed for file: /path/to/file.docx
```

### 2. 文件服务层 (`backend/services/file_service.py`)

#### save_file() 方法

**日志示例**:

```
INFO - Processing file upload: original filename='公司简介.docx'
DEBUG - Extracted: name='公司简介', extension='.docx'
DEBUG - Sanitized name: ''
WARNING - Filename sanitized to empty, using timestamp: 'upload_1702632145'
INFO - Final filename: 'upload_1702632145.docx', saving to: '/home/u_topn/TOP_N/uploads/upload_1702632145.docx'
INFO - ✓ File saved successfully: original='公司简介.docx' → saved='upload_1702632145.docx'
```

**关键信息**:
- 原始文件名
- 文件名和扩展名的分离结果
- 安全化后的文件名
- 是否使用了时间戳兜底
- 最终文件名转换（原始 → 保存）

#### extract_text() 方法

**日志示例**:

```
INFO - Attempting to extract text from: /home/u_topn/TOP_N/uploads/upload_1702632145.docx
DEBUG - Detected file extension: 'docx'
INFO - Extracting DOCX: /home/u_topn/TOP_N/uploads/upload_1702632145.docx
INFO - DOCX has 15 paragraphs
INFO - ✓ DOCX extraction successful, total length: 1500
INFO - ✓ Successfully extracted 1500 characters. Preview: XXX公司成立于2020年，专注于...
```

**异常情况**:

```
ERROR - ✗ File not found: /path/to/missing.docx
ERROR - ✗ File has no extension: /path/to/uploads/docx
WARNING - ✗ Unsupported file type: exe for file: /path/to/file.exe
WARNING - ✗ No text extracted from /path/to/empty.pdf
ERROR - ✗ Error extracting text from /path/to/file.docx: [exception details]
```

### 3. 文本提取子方法

#### _extract_text_file() - 文本文件提取

```
DEBUG - Trying encoding: utf-8
INFO - ✓ Successfully decoded with utf-8, length: 1200

# 如果失败尝试其他编码
DEBUG - Encoding utf-8 failed: 'utf-8' codec can't decode byte...
DEBUG - Trying encoding: gbk
INFO - ✓ Successfully decoded with gbk, length: 1200

# 所有编码都失败
ERROR - ✗ Failed to decode text file with all encodings: /path/to/file.txt
```

#### _extract_pdf() - PDF 提取

```
INFO - PDF has 5 pages
DEBUG - Extracted page 1/5, length: 300
DEBUG - Extracted page 2/5, length: 450
DEBUG - Extracted page 3/5, length: 280
DEBUG - Extracted page 4/5, length: 320
DEBUG - Extracted page 5/5, length: 150
INFO - ✓ PDF extraction successful, total length: 1500

# 空白 PDF
WARNING - ✗ PDF extraction returned empty text

# PyPDF2 不可用
ERROR - ✗ PyPDF2 not available, cannot extract PDF
```

#### _extract_docx() - DOCX 提取

```
INFO - DOCX has 15 paragraphs
INFO - ✓ DOCX extraction successful, total length: 1500

# 空白文档
WARNING - ✗ DOCX extraction returned empty text

# python-docx 不可用
ERROR - ✗ python-docx not available, cannot extract DOCX
```

## 典型场景日志示例

### 场景 1: 成功上传中文文件名的 DOCX

```log
2025-12-15 18:05:30 - api - INFO - Upload request for file: 公司简介.docx, size: 15234
2025-12-15 18:05:30 - file_service - INFO - Processing file upload: original filename='公司简介.docx'
2025-12-15 18:05:30 - file_service - DEBUG - Extracted: name='公司简介', extension='.docx'
2025-12-15 18:05:30 - file_service - DEBUG - Sanitized name: ''
2025-12-15 18:05:30 - file_service - WARNING - Filename sanitized to empty, using timestamp: 'upload_1702632330'
2025-12-15 18:05:30 - file_service - INFO - Final filename: 'upload_1702632330.docx', saving to: '/home/u_topn/TOP_N/uploads/upload_1702632330.docx'
2025-12-15 18:05:30 - file_service - INFO - ✓ File saved successfully: original='公司简介.docx' → saved='upload_1702632330.docx'
2025-12-15 18:05:30 - api - INFO - File saved successfully: /home/u_topn/TOP_N/uploads/upload_1702632330.docx
2025-12-15 18:05:30 - file_service - INFO - Attempting to extract text from: /home/u_topn/TOP_N/uploads/upload_1702632330.docx
2025-12-15 18:05:30 - file_service - DEBUG - Detected file extension: 'docx'
2025-12-15 18:05:30 - file_service - INFO - Extracting DOCX: /home/u_topn/TOP_N/uploads/upload_1702632330.docx
2025-12-15 18:05:30 - file_service - INFO - DOCX has 15 paragraphs
2025-12-15 18:05:30 - file_service - INFO - ✓ DOCX extraction successful, total length: 1500
2025-12-15 18:05:30 - file_service - INFO - ✓ Successfully extracted 1500 characters. Preview: XXX科技有限公司成立于2020年...
2025-12-15 18:05:30 - api - INFO - ✓ Upload complete: file=公司简介.docx, text_length=1500
```

### 场景 2: 上传扩展名丢失（修复前的问题）

```log
2025-12-15 17:45:00 - api - INFO - Upload request for file: 测试.docx, size: 5678
2025-12-15 17:45:00 - file_service - INFO - Processing file upload: original filename='测试.docx'
2025-12-15 17:45:00 - file_service - DEBUG - Extracted: name='测试', extension='.docx'
2025-12-15 17:45:00 - file_service - DEBUG - Sanitized name: ''
2025-12-15 17:45:00 - file_service - WARNING - Filename sanitized to empty, using timestamp: 'upload_1702631100'
2025-12-15 17:45:00 - file_service - INFO - Final filename: 'upload_1702631100.docx', saving to: '/home/u_topn/TOP_N/uploads/upload_1702631100.docx'
2025-12-15 17:45:00 - file_service - INFO - ✓ File saved successfully: original='测试.docx' → saved='upload_1702631100.docx'
2025-12-15 17:45:00 - api - INFO - File saved successfully: /home/u_topn/TOP_N/uploads/upload_1702631100.docx
# 如果是旧版本，这里会显示：
# ERROR - ✗ File has no extension: /home/u_topn/TOP_N/uploads/docx
```

### 场景 3: 上传 GBK 编码的文本文件

```log
2025-12-15 18:10:00 - api - INFO - Upload request for file: readme.txt, size: 2048
2025-12-15 18:10:00 - file_service - INFO - Processing file upload: original filename='readme.txt'
2025-12-15 18:10:00 - file_service - DEBUG - Extracted: name='readme', extension='.txt'
2025-12-15 18:10:00 - file_service - DEBUG - Sanitized name: 'readme'
2025-12-15 18:10:00 - file_service - INFO - Final filename: 'readme.txt', saving to: '/home/u_topn/TOP_N/uploads/readme.txt'
2025-12-15 18:10:00 - file_service - INFO - ✓ File saved successfully: original='readme.txt' → saved='readme.txt'
2025-12-15 18:10:00 - api - INFO - File saved successfully: /home/u_topn/TOP_N/uploads/readme.txt
2025-12-15 18:10:00 - file_service - INFO - Attempting to extract text from: /home/u_topn/TOP_N/uploads/readme.txt
2025-12-15 18:10:00 - file_service - DEBUG - Detected file extension: 'txt'
2025-12-15 18:10:00 - file_service - INFO - Extracting text file (txt): /home/u_topn/TOP_N/uploads/readme.txt
2025-12-15 18:10:00 - file_service - DEBUG - Trying encoding: utf-8
2025-12-15 18:10:00 - file_service - DEBUG - Encoding utf-8 failed: 'utf-8' codec can't decode byte...
2025-12-15 18:10:00 - file_service - DEBUG - Trying encoding: gbk
2025-12-15 18:10:00 - file_service - INFO - ✓ Successfully decoded with gbk, length: 1200
2025-12-15 18:10:00 - file_service - INFO - ✓ Successfully extracted 1200 characters. Preview: 这是一个测试文件...
2025-12-15 18:10:00 - api - INFO - ✓ Upload complete: file=readme.txt, text_length=1200
```

### 场景 4: 上传多页 PDF

```log
2025-12-15 18:15:00 - api - INFO - Upload request for file: report.pdf, size: 102400
2025-12-15 18:15:00 - file_service - INFO - Processing file upload: original filename='report.pdf'
2025-12-15 18:15:00 - file_service - DEBUG - Extracted: name='report', extension='.pdf'
2025-12-15 18:15:00 - file_service - DEBUG - Sanitized name: 'report'
2025-12-15 18:15:00 - file_service - INFO - Final filename: 'report.pdf', saving to: '/home/u_topn/TOP_N/uploads/report.pdf'
2025-12-15 18:15:00 - file_service - INFO - ✓ File saved successfully: original='report.pdf' → saved='report.pdf'
2025-12-15 18:15:00 - api - INFO - File saved successfully: /home/u_topn/TOP_N/uploads/report.pdf
2025-12-15 18:15:00 - file_service - INFO - Attempting to extract text from: /home/u_topn/TOP_N/uploads/report.pdf
2025-12-15 18:15:00 - file_service - DEBUG - Detected file extension: 'pdf'
2025-12-15 18:15:00 - file_service - INFO - Extracting PDF: /home/u_topn/TOP_N/uploads/report.pdf
2025-12-15 18:15:00 - file_service - INFO - PDF has 10 pages
2025-12-15 18:15:01 - file_service - DEBUG - Extracted page 1/10, length: 450
2025-12-15 18:15:01 - file_service - DEBUG - Extracted page 2/10, length: 520
2025-12-15 18:15:02 - file_service - DEBUG - Extracted page 3/10, length: 480
... (省略中间页)
2025-12-15 18:15:05 - file_service - DEBUG - Extracted page 10/10, length: 390
2025-12-15 18:15:05 - file_service - INFO - ✓ PDF extraction successful, total length: 4500
2025-12-15 18:15:05 - file_service - INFO - ✓ Successfully extracted 4500 characters. Preview: 2024年度工作报告...
2025-12-15 18:15:05 - api - INFO - ✓ Upload complete: file=report.pdf, text_length=4500
```

## 查看日志

### 服务器端查看实时日志

```bash
# 查看最近50行日志
ssh u_topn@39.105.12.124 "tail -50 /tmp/topn.log"

# 实时监控日志
ssh u_topn@39.105.12.124 "tail -f /tmp/topn.log"

# 过滤文件上传相关日志
ssh u_topn@39.105.12.124 "grep 'Upload\|file_service' /tmp/topn.log | tail -50"

# 只看成功的上传
ssh u_topn@39.105.12.124 "grep '✓.*Upload complete' /tmp/topn.log | tail -20"

# 只看失败的上传
ssh u_topn@39.105.12.124 "grep '✗' /tmp/topn.log | tail -20"
```

### 本地开发环境

```bash
# Windows PowerShell
Get-Content D:\code\TOP_N\logs\app.log -Tail 50 -Wait

# 过滤上传相关
Select-String -Path D:\code\TOP_N\logs\app.log -Pattern "Upload|file_service" | Select-Object -Last 50
```

## 故障排查指南

### 问题 1: 文件上传但无法提取文本

**查找关键日志**:
```bash
grep "Upload complete\|Text extraction failed\|No text extracted" /tmp/topn.log
```

**可能原因**:
1. 文件扩展名丢失 → 看是否有 `File has no extension`
2. 文件格式不支持 → 看是否有 `Unsupported file type`
3. 文件为空或损坏 → 看是否有 `extraction returned empty text`
4. 缺少依赖库 → 看是否有 `PyPDF2 not available` 或 `python-docx not available`

### 问题 2: 中文文件名上传失败

**查找关键日志**:
```bash
grep "Processing file upload\|Sanitized name\|using timestamp" /tmp/topn.log
```

**正常行为**:
- 中文文件名会被清理为空
- 系统会使用时间戳作为文件名
- 扩展名会被保留

**异常行为**:
- 如果最终文件名没有扩展名，说明代码有问题

### 问题 3: 编码问题

**查找关键日志**:
```bash
grep "Trying encoding\|Successfully decoded\|Failed to decode" /tmp/topn.log
```

**系统尝试顺序**: utf-8 → gbk → gb2312 → gb18030 → latin1

### 问题 4: PDF 提取为空

**查找关键日志**:
```bash
grep "PDF has.*pages\|Extracted page\|PDF extraction" /tmp/topn.log
```

**检查点**:
- PDF 是否有页数？
- 每页是否成功提取？
- 总长度是否为 0？

## 日志保留策略

### 当前策略

- 日志文件: `/tmp/topn.log`
- 保留策略: 系统重启后清空（临时文件）
- 建议: 生产环境应该配置日志轮转

### 推荐的生产配置

```python
# logger_config.py 添加日志轮转
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    '/var/log/topn/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,  # 保留5个备份
    encoding='utf-8'
)
```

## 性能考虑

### 日志级别建议

- **开发环境**: DEBUG（查看所有细节）
- **测试环境**: INFO（查看主要流程）
- **生产环境**: WARNING（只记录警告和错误）

### 调整日志级别

```python
# 在 logger_config.py 中
logger.setLevel(logging.INFO)  # 生产环境
# logger.setLevel(logging.DEBUG)  # 开发环境
```

## 监控建议

### 关键指标

1. **上传成功率**: `grep "✓ Upload complete" | wc -l` / 总上传数
2. **文件名清理率**: `grep "using timestamp" | wc -l` / 总上传数
3. **提取失败率**: `grep "✗.*extraction" | wc -l` / 总上传数
4. **平均文本长度**: 从日志中提取 `text_length=` 的值

### 告警规则

- 上传成功率 < 95% → 告警
- 提取失败率 > 5% → 告警
- 连续 10 次文件名使用时间戳 → 检查文件名规则

## 总结

现在文件上传功能拥有完整的日志链路，包括：

✓ API 层请求接收和响应
✓ 文件名安全化过程（包含原始名→安全名的转换）
✓ 文件保存详情
✓ 文本提取过程（包含编码尝试、分页进度等）
✓ 成功/失败的明确标识（✓/✗ 符号）
✓ 文本预览（前100字符）

这些日志可以帮助快速诊断和解决文件上传相关的问题。
