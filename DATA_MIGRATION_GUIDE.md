# 发布历史数据整合迁移指南

## 📋 概述

本指南说明如何将 `publish_tasks`、`articles` 表的数据整合到 `publish_history` 表中，确保数据一致性。

## 🎯 迁移目的

1. **补充缺失数据**：为 `publish_history` 表中缺少 `article_title` 和 `article_content` 的记录补充数据
2. **创建缺失记录**：将 `publish_tasks` 中成功的发布记录（但没有对应 `publish_history`）迁移过来
3. **统一数据源**：确保发布历史数据完整存储在 `publish_history` 表中

## 📊 迁移逻辑

### 数据补充优先级

```
publish_history 表中的记录
    ↓
缺少 article_title 或 article_content？
    ↓
├─ 优先级1：从 publish_tasks 表补充（通过 URL 匹配）
├─ 优先级2：从 publish_tasks 表补充（通过 article_id 匹配）
└─ 优先级3：从 articles 表补充（通过 article_id 关联）
```

### 记录创建逻辑

```
publish_tasks 表中的成功记录
    ↓
检查 publish_history 是否已存在（通过 user_id + url）
    ↓
如果不存在 → 创建新的 publish_history 记录
```

## 🚀 使用方法

### 方法1：本地执行（推荐）

#### 步骤1：备份数据库

```bash
# Windows
copy D:\code\TOP_N\data\topn.db D:\code\TOP_N\data\topn.db.backup

# Linux
cp /path/to/topn.db /path/to/topn.db.backup
```

#### 步骤2：执行迁移脚本

```bash
# Windows
cd D:\code\TOP_N\backend
D:\Python3.13.1\python.exe migrate_consolidate_publish_data_auto.py

# Linux
cd /path/to/backend
python3 migrate_consolidate_publish_data_auto.py
```

#### 步骤3：查看迁移结果

脚本会显示详细的迁移信息：
- 当前数据统计
- 补充的记录数
- 创建的新记录数
- 迁移前后对比

### 方法2：使用批处理文件（Windows）

```bash
cd D:\code\TOP_N\backend
run_migration.bat
```

这会自动：
1. 备份数据库（带时间戳）
2. 执行迁移
3. 显示结果

### 方法3：远程服务器执行

#### SSH登录远程服务器

```bash
ssh user@39.105.12.124
```

#### 上传迁移脚本

```bash
# 从本地上传到远程
scp D:\code\TOP_N\backend\migrate_consolidate_publish_data_auto.py user@39.105.12.124:/path/to/backend/
```

#### 在远程服务器执行

```bash
cd /path/to/backend

# 备份数据库
cp ../data/topn.db ../data/topn.db.backup_$(date +%Y%m%d_%H%M%S)

# 执行迁移
python3 migrate_consolidate_publish_data_auto.py
```

## 📝 迁移脚本说明

### migrate_consolidate_publish_data_auto.py

**功能：**
1. ✅ 自动执行，无需交互
2. ✅ 补充 publish_history 中缺失的 article_title 和 article_content
3. ✅ 从 publish_tasks 创建缺失的 publish_history 记录
4. ✅ 从 articles 表补充关联数据
5. ✅ 显示详细的迁移统计

**输出示例：**

```
================================================================================
发布历史数据整合迁移
================================================================================
开始时间: 2025-12-15 18:53:59

第1步：统计当前数据
--------------------------------------------------------------------------------
publish_history 表：5 条记录
publish_tasks 表：20 条记录
articles 表：3 条记录
publish_history 中缺少标题的记录：3 条
publish_history 中缺少内容的记录：2 条

第2步：从 publish_tasks 表补充数据
--------------------------------------------------------------------------------
找到 3 条需要补充的记录
  [URL匹配] 记录 #1 从 task #10 补充数据
  [URL匹配] 记录 #2 从 task #12 补充数据
从 publish_tasks 补充：2 条记录

第3步：从 articles 表补充数据
--------------------------------------------------------------------------------
找到 1 条有 article_id 但缺少数据的记录
  记录 #3 从 article #1 补充数据
从 articles 补充：1 条记录

第4步：从 publish_tasks 创建缺失的 publish_history 记录
--------------------------------------------------------------------------------
找到 20 条成功的任务记录
  创建新记录：task #5 -> 如何选择合适的云服务提供商...
  创建新记录：task #7 -> 大模型应用开发最佳实践...
  ...
从 publish_tasks 创建新记录：15 条

第5步：提交更改到数据库
--------------------------------------------------------------------------------
✓ 数据已成功提交

第6步：验证迁移结果
--------------------------------------------------------------------------------
迁移后统计：
  总记录数：5 -> 20 (增加 15)
  缺少标题：3 -> 0 (减少 3)
  缺少内容：2 -> 0 (减少 2)

================================================================================
迁移总结
================================================================================
✓ 从 publish_tasks 补充数据：2 条
✓ 从 articles 补充数据：1 条
✓ 从 publish_tasks 创建新记录：15 条
✓ 总计处理：18 条

完成时间: 2025-12-15 18:54:05
================================================================================
```

## ⚠️ 注意事项

### 1. 数据安全

- ✅ **必须先备份数据库**
- ⚠️ 迁移过程中会修改数据库
- 🔄 如果迁移失败，会自动回滚事务

### 2. 幂等性

- ✅ 脚本是幂等的，可以多次执行
- ✅ 不会创建重复的 publish_history 记录（通过 user_id + url 去重）
- ✅ 不会覆盖已存在的 article_title 和 article_content

### 3. 性能

- 📊 对于大量数据（>10000条），迁移可能需要几分钟
- 💾 迁移过程中会锁定数据库表
- ⏸️ 建议在低峰期执行

### 4. 回滚

如果需要回滚到迁移前的状态：

```bash
# Windows
copy D:\code\TOP_N\data\topn.db.backup D:\code\TOP_N\data\topn.db

# Linux
cp /path/to/topn.db.backup /path/to/topn.db
```

## 🔍 数据验证

迁移完成后，可以运行以下脚本验证数据：

```bash
cd D:\code\TOP_N\backend
python check_all_tables.py
```

应该看到：
- ✅ `publish_history` 记录数增加
- ✅ 缺少 article_title 的记录数减少到 0 或接近 0
- ✅ 所有成功的 publish_tasks 都有对应的 publish_history 记录

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `migrate_consolidate_publish_data_auto.py` | 自动迁移脚本（推荐使用） |
| `migrate_consolidate_publish_data.py` | 交互式迁移脚本（需要确认） |
| `run_migration.bat` | Windows批处理脚本 |
| `check_all_tables.py` | 数据验证脚本 |

## ❓ 常见问题

### Q1: 本地数据库没有数据怎么办？

A: 如果本地 `publish_history` 和 `publish_tasks` 都是空的，脚本会提示"没有需要迁移的数据"并退出。这是正常的。

### Q2: 远程服务器有数据但本地没有？

A: 这是预期的。远程服务器可能已经运行了一段时间，积累了发布历史数据。本地是开发环境，数据可能被清空过。

### Q3: 迁移后发布历史仍然显示"临时发布"？

A: 可能原因：
1. `publish_tasks` 表中也没有对应的记录
2. URL不匹配（检查 `publish_history.url` 和 `publish_tasks.result_url` 是否一致）
3. `articles` 表中也没有关联记录

### Q4: 可以在生产环境直接运行吗？

A: 可以，但建议：
1. ✅ 先在测试环境验证
2. ✅ 备份数据库
3. ✅ 在低峰期执行
4. ✅ 监控执行过程

## ✅ 迁移检查清单

执行迁移前请确认：

- [ ] 已备份数据库
- [ ] 已上传迁移脚本到服务器
- [ ] 已安装所需的Python依赖（sqlalchemy, models等）
- [ ] 有足够的磁盘空间
- [ ] 在低峰期执行（如果是生产环境）

执行迁移后请验证：

- [ ] 迁移成功完成（无报错）
- [ ] publish_history 记录数增加
- [ ] 缺少标题的记录数显著减少
- [ ] 前端发布历史页面能正常显示
- [ ] 重试功能正常工作

---

**更新时间：** 2025-12-15
**脚本版本：** 1.0
**维护人员：** Claude Code Assistant
