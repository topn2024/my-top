# TOP_N 生产部署执行指南

**部署阶段**: P4 - 生产部署  
**预计时间**: 30-60 分钟  
**风险等级**: 中（有完整回滚方案）

---

## 部署方法: 使用自动化脚本

### 步骤 1: 准备部署脚本

```bash
cd /d/code/TOP_N
chmod +x deploy_to_production.sh
chmod +x rollback_deployment.sh
chmod +x verify_production.sh
```

### 步骤 2: 提交代码到 Git (如果还没有)

```bash
git add .
git commit -m "架构清理：P0-P3完成，准备部署"
git push origin main
```

### 步骤 3: 执行部署

```bash
./deploy_to_production.sh
```

脚本会自动执行所有部署步骤。

### 步骤 4: 验证部署

```bash
./verify_production.sh
```

### 步骤 5: 开始监控

参考 `PRODUCTION_MONITORING_GUIDE.md` 进行 48 小时监控。

---

## 如果需要回滚

```bash
./rollback_deployment.sh
```

---

**详细说明**: 见完整版本的部署文档
