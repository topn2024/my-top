# TOP_N平台 RBAC权限管理系统设计方案

## 一、系统概述

设计一套灵活、可扩展的基于角色的访问控制(RBAC)系统,支持个人用户和企业用户,实现细粒度的权限管理。

## 二、核心概念

### 2.1 用户类型
- **个人用户(Individual)**: 独立注册使用的个人账号
- **企业用户(Enterprise)**: 企业组织账号,可包含多个成员

### 2.2 角色定义

#### 系统级角色
- **SUPER_ADMIN**: 超级管理员 - 系统最高权限
- **PLATFORM_ADMIN**: 平台管理员 - 管理平台用户和企业

#### 企业级角色
- **ENTERPRISE_OWNER**: 企业所有者 - 企业最高权限
- **ENTERPRISE_ADMIN**: 企业管理员 - 管理企业成员和权限
- **ENTERPRISE_MEMBER**: 企业普通成员 - 基本使用权限
- **ENTERPRISE_VIEWER**: 企业查看者 - 仅查看权限

#### 个人用户角色
- **INDIVIDUAL_USER**: 个人用户 - 个人账号权限

### 2.3 权限定义

#### 资源类型
- **workflow**: 工作流管理
- **article**: 文章管理
- **platform_account**: 平台账号管理
- **user**: 用户管理
- **enterprise**: 企业管理
- **publish**: 发布管理

#### 操作类型
- **create**: 创建
- **read**: 读取
- **update**: 更新
- **delete**: 删除
- **execute**: 执行(如发布文章)
- **manage**: 管理(如管理成员)

## 三、数据库表设计

### 3.1 新增表

#### 1. enterprises (企业表)
```sql
CREATE TABLE enterprises (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL COMMENT '企业名称',
    code VARCHAR(50) UNIQUE NOT NULL COMMENT '企业唯一标识码',
    industry VARCHAR(100) COMMENT '所属行业',
    description TEXT COMMENT '企业描述',
    logo_url VARCHAR(500) COMMENT '企业Logo',
    contact_email VARCHAR(100) COMMENT '联系邮箱',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    status VARCHAR(50) DEFAULT 'active' COMMENT '状态: active, suspended, closed',
    max_members INT DEFAULT 10 COMMENT '最大成员数限制',
    subscription_plan VARCHAR(50) DEFAULT 'free' COMMENT '订阅计划: free, basic, pro, enterprise',
    subscription_expires_at TIMESTAMP NULL COMMENT '订阅到期时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业表';
```

#### 2. roles (角色表)
```sql
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL COMMENT '角色名称',
    code VARCHAR(50) UNIQUE NOT NULL COMMENT '角色代码',
    type VARCHAR(50) NOT NULL COMMENT '角色类型: system, enterprise, individual',
    description TEXT COMMENT '角色描述',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统角色',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';
```

#### 3. permissions (权限表)
```sql
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resource VARCHAR(50) NOT NULL COMMENT '资源类型',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    code VARCHAR(100) UNIQUE NOT NULL COMMENT '权限代码',
    description TEXT COMMENT '权限描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_resource_action (resource, action),
    INDEX idx_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';
```

#### 4. role_permissions (角色-权限关联表)
```sql
CREATE TABLE role_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';
```

#### 5. enterprise_members (企业成员表)
```sql
CREATE TABLE enterprise_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    enterprise_id INT NOT NULL,
    user_id INT NOT NULL,
    role_id INT NOT NULL COMMENT '企业内角色',
    status VARCHAR(50) DEFAULT 'active' COMMENT '状态: active, suspended, left',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    UNIQUE KEY uk_enterprise_user (enterprise_id, user_id),
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业成员表';
```

### 3.2 修改现有表

#### users表新增字段
```sql
ALTER TABLE users
ADD COLUMN user_type VARCHAR(50) DEFAULT 'individual' COMMENT '用户类型: individual, enterprise' AFTER is_active,
ADD COLUMN role_id INT NULL COMMENT '系统级角色(仅用于admin等系统角色)' AFTER user_type,
ADD INDEX idx_user_type (user_type);
```

#### workflows表新增字段
```sql
ALTER TABLE workflows
ADD COLUMN enterprise_id INT NULL COMMENT '所属企业ID(企业用户创建)' AFTER user_id,
ADD COLUMN visibility VARCHAR(50) DEFAULT 'private' COMMENT '可见性: private, team, public' AFTER enterprise_id,
ADD INDEX idx_enterprise_id (enterprise_id);
```

## 四、权限矩阵

### 4.1 系统级角色权限

| 角色 | 权限范围 |
|-----|---------|
| SUPER_ADMIN | 所有权限 |
| PLATFORM_ADMIN | 用户管理、企业管理、系统配置 |

### 4.2 企业级角色权限

| 资源 / 角色 | OWNER | ADMIN | MEMBER | VIEWER |
|-----------|-------|-------|--------|--------|
| workflow.create | ✓ | ✓ | ✓ | ✗ |
| workflow.read | ✓ | ✓ | ✓ | ✓ |
| workflow.update | ✓ | ✓ | Own | ✗ |
| workflow.delete | ✓ | ✓ | Own | ✗ |
| article.create | ✓ | ✓ | ✓ | ✗ |
| article.read | ✓ | ✓ | ✓ | ✓ |
| article.update | ✓ | ✓ | Own | ✗ |
| article.delete | ✓ | ✓ | Own | ✗ |
| publish.execute | ✓ | ✓ | ✓ | ✗ |
| platform_account.create | ✓ | ✓ | ✓ | ✗ |
| platform_account.read | ✓ | ✓ | ✓ | ✓ |
| platform_account.update | ✓ | ✓ | Own | ✗ |
| platform_account.delete | ✓ | ✓ | Own | ✗ |
| enterprise.manage | ✓ | Partial | ✗ | ✗ |
| user.invite | ✓ | ✓ | ✗ | ✗ |
| user.remove | ✓ | ✓ | ✗ | ✗ |

注:
- ✓ = 完全权限
- Own = 仅自己创建的资源
- Partial = 部分权限
- ✗ = 无权限

### 4.3 个人用户权限

个人用户对自己的资源拥有完全控制权:
- workflow: create, read, update, delete
- article: create, read, update, delete
- platform_account: create, read, update, delete
- publish: execute

## 五、权限检查流程

### 5.1 权限验证装饰器

```python
@require_permission('workflow', 'create')
def create_workflow():
    pass

@require_enterprise_role(['OWNER', 'ADMIN'])
def manage_members():
    pass

@require_resource_owner('workflow', workflow_id)
def update_workflow(workflow_id):
    pass
```

### 5.2 权限检查逻辑

```
1. 检查用户是否登录
2. 检查用户是否激活
3. 检查是否超级管理员(跳过所有检查)
4. 根据用户类型:
   a. 个人用户:
      - 检查资源所有权
      - 检查操作权限
   b. 企业用户:
      - 检查企业成员资格
      - 检查企业内角色
      - 检查角色权限
      - 检查资源可见性
5. 返回权限检查结果
```

## 六、API接口设计

### 6.1 企业管理API

```
POST   /api/enterprises              创建企业
GET    /api/enterprises              获取企业列表
GET    /api/enterprises/<id>         获取企业详情
PUT    /api/enterprises/<id>         更新企业信息
DELETE /api/enterprises/<id>         删除企业

POST   /api/enterprises/<id>/members        添加成员
GET    /api/enterprises/<id>/members        获取成员列表
PUT    /api/enterprises/<id>/members/<uid>  更新成员角色
DELETE /api/enterprises/<id>/members/<uid>  移除成员

POST   /api/enterprises/<id>/invite         邀请成员(发送邀请)
POST   /api/enterprises/accept-invite       接受邀请
```

### 6.2 角色权限API

```
GET    /api/roles                    获取角色列表
GET    /api/roles/<id>               获取角色详情
POST   /api/roles                    创建自定义角色(企业)
PUT    /api/roles/<id>               更新角色
DELETE /api/roles/<id>               删除角色

GET    /api/permissions              获取权限列表
POST   /api/roles/<id>/permissions   为角色分配权限
DELETE /api/roles/<id>/permissions   移除角色权限
```

### 6.3 用户权限API

```
GET    /api/auth/me/permissions      获取当前用户权限
GET    /api/users/<id>/permissions   获取指定用户权限
```

## 七、前端页面设计

### 7.1 企业管理页面

**路径**: `/enterprise`

**功能**:
- 企业信息展示与编辑
- 成员列表管理
- 角色权限分配
- 邀请成员
- 订阅管理

### 7.2 角色管理页面

**路径**: `/enterprise/roles`

**功能**:
- 角色列表展示
- 创建/编辑角色
- 权限配置
- 角色成员查看

### 7.3 用户设置页面增强

**路径**: `/settings`

**新增**:
- 企业切换(如果用户属于多个企业)
- 角色与权限查看
- 企业邀请管理

## 八、实施步骤

### 第一阶段: 数据库层(1-2天)
1. ✅ 创建新表: enterprises, roles, permissions, role_permissions, enterprise_members
2. ✅ 修改现有表: users, workflows
3. ✅ 初始化系统角色和权限数据
4. ✅ 数据迁移脚本

### 第二阶段: ORM模型层(1天)
1. ✅ 创建新的SQLAlchemy模型
2. ✅ 更新现有模型关系
3. ✅ 编写模型测试

### 第三阶段: 权限验证层(2天)
1. ✅ 实现权限检查装饰器
2. ✅ 实现权限验证函数
3. ✅ 集成到现有API

### 第四阶段: 企业管理API(2-3天)
1. ✅ 企业CRUD API
2. ✅ 成员管理API
3. ✅ 邀请系统API
4. ✅ 角色权限API

### 第五阶段: 前端页面(3-4天)
1. ✅ 企业管理页面
2. ✅ 角色管理页面
3. ✅ 成员邀请流程
4. ✅ 权限展示组件

### 第六阶段: 测试与优化(2天)
1. ✅ 单元测试
2. ✅ 集成测试
3. ✅ 性能优化
4. ✅ 文档完善

**总预计时间**: 11-14个工作日

## 九、安全考虑

### 9.1 数据隔离
- 个人用户只能访问自己的数据
- 企业成员只能访问企业内的数据
- 严格的权限检查,防止越权访问

### 9.2 操作审计
- 记录所有关键操作(创建、删除、权限变更)
- 保留操作日志,便于追溯

### 9.3 敏感信息保护
- 企业成员列表不对外公开
- 权限配置仅管理员可见
- API访问频率限制

## 十、优势与特点

### 10.1 灵活性
- 支持自定义企业角色
- 可按需配置权限
- 支持多企业成员

### 10.2 可扩展性
- 易于添加新的资源类型
- 易于添加新的操作权限
- 支持企业级功能扩展

### 10.3 易用性
- 清晰的角色层级
- 直观的权限配置
- 友好的用户界面

### 10.4 企业级功能
- 成员邀请与管理
- 订阅计划支持
- 资源共享与协作

## 十一、升级兼容性

### 11.1 现有用户迁移
```python
# 所有现有用户自动设置为individual类型
UPDATE users SET user_type = 'individual' WHERE user_type IS NULL;

# admin用户设置为system类型并分配角色
UPDATE users
SET user_type = 'system',
    role_id = (SELECT id FROM roles WHERE code = 'SUPER_ADMIN')
WHERE username = 'admin';
```

### 11.2 现有数据兼容
- 所有现有workflows保持private可见性
- 现有用户保留所有原有权限
- 不影响现有功能使用

## 十二、后续扩展

### 12.1 高级功能
- 部门/团队管理(企业内分组)
- 工作流审批流程
- 资源配额管理
- 操作日志详细记录

### 12.2 订阅计划
- Free: 基础功能,最多3成员
- Basic: 增强功能,最多10成员
- Pro: 完整功能,最多50成员
- Enterprise: 定制功能,无限成员

---

**文档版本**: v1.0
**创建日期**: 2025-12-07
**最后更新**: 2025-12-07
