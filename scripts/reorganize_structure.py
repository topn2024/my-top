#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录结构重组脚本
将混乱的文件组织到合理的目录结构中
"""
import os
import shutil
from pathlib import Path

# 基础路径 (项目根目录)
BASE_DIR = Path(__file__).parent.parent

# 新的目录结构
STRUCTURE = {
    'scripts': {
        'deploy': [],  # 部署相关脚本
        'install': [],  # 安装相关脚本
        'test': [],     # 测试脚本
        'fix': [],      # 修复脚本
        'check': [],    # 检查脚本
    },
    'docs': [],        # 文档文件
    'archive': {       # 归档旧文件
        'python_installers': [],  # Python安装包
        'chromedriver': [],       # ChromeDriver文件
        'temp': [],               # 临时文件
    },
}

# 文件分类规则
FILE_RULES = {
    # 部署脚本
    'scripts/deploy': [
        'deploy*.py', 'upload*.py', 'auto_deploy.*',
        'complete_deployment.py', 'setup*.py',
        '*.sh', '*.ps1', '*.exp'
    ],
    # 安装脚本
    'scripts/install': [
        'install*.py', 'upgrade*.py', 'configure*.py',
        'smart_upgrade.py'
    ],
    # 测试脚本
    'scripts/test': [
        'test*.py', 'run*.py', 'local_test*.py',
        'diagnose*.py', 'verify*.py'
    ],
    # 修复脚本
    'scripts/fix': [
        'fix*.py', 'enhance*.py', 'add*.py',
        'update*.py', 'create*.py'
    ],
    # 检查脚本
    'scripts/check': [
        'check*.py', 'monitor*.py', 'get*.py'
    ],
    # 文档
    'docs': [
        '*.md', '*.txt', '*.docx', '*.csv'
    ],
    # Python安装包归档
    'archive/python_installers': [
        'python*.exe', '*.bat'
    ],
    # ChromeDriver归档
    'archive/chromedriver': [
        'chromedriver*.zip', 'ChromeDriver*.md'
    ],
    # 临时文件归档
    'archive/temp': [
        '*.html', '*.png', 'temp*.py', 'nul',
        '*output.txt', '*.backup', '~$*',
        'qrcode_login*.py', 'zhihu_auto_post.py'
    ],
}

# 需要保留在根目录的文件
ROOT_FILES = [
    'README.md', 'readme.txt', 'MYSQL_MIGRATION_README.md',
    'requirements.txt', 'requirements_new.txt',
    'start.sh', '公司介绍.docx'
]

# 需要保留的目录（不移动）
KEEP_DIRS = [
    'backend', 'frontend', 'static', 'templates',
    'accounts', 'data', 'uploads', '.claude',
    'chromedriver-linux64'
]


def create_directory_structure():
    """创建新的目录结构"""
    def create_dirs(structure, parent_path=''):
        for name, sub in structure.items():
            dir_path = BASE_DIR / parent_path / name if parent_path else BASE_DIR / name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[OK] 创建目录: {dir_path.relative_to(BASE_DIR)}")

            if isinstance(sub, dict):
                create_dirs(sub, f"{parent_path}/{name}" if parent_path else name)

    create_dirs(STRUCTURE)


def match_pattern(filename, patterns):
    """检查文件名是否匹配任何模式"""
    from fnmatch import fnmatch
    return any(fnmatch(filename, pattern) for pattern in patterns)


def categorize_and_move_files():
    """分类并移动文件"""
    moved_count = 0
    skipped_count = 0

    # 获取根目录所有文件
    root_files = [f for f in BASE_DIR.iterdir() if f.is_file()]

    for file_path in root_files:
        filename = file_path.name

        # 跳过需要保留在根目录的文件
        if filename in ROOT_FILES or filename == os.path.basename(__file__):
            print(f"[SKIP] 保留根目录: {filename}")
            skipped_count += 1
            continue

        # 查找匹配的目标目录
        target_dir = None
        for dir_path, patterns in FILE_RULES.items():
            if match_pattern(filename, patterns):
                target_dir = BASE_DIR / dir_path
                break

        if target_dir is None:
            # 未分类的文件放到 archive/temp
            target_dir = BASE_DIR / 'archive' / 'temp'
            print(f"? 未分类文件: {filename} -> archive/temp")

        # 移动文件
        try:
            target_path = target_dir / filename

            # 如果目标已存在,添加时间戳
            if target_path.exists():
                import time
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                stem = target_path.stem
                suffix = target_path.suffix
                target_path = target_dir / f"{stem}_{timestamp}{suffix}"

            shutil.move(str(file_path), str(target_path))
            print(f"[MOVE] 移动: {filename} -> {target_dir.relative_to(BASE_DIR)}/")
            moved_count += 1
        except Exception as e:
            print(f"[ERROR] 移动失败 {filename}: {e}")

    return moved_count, skipped_count


def clean_empty_directories():
    """清理空目录"""
    cleaned = []
    for dir_path in BASE_DIR.rglob('*'):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            try:
                dir_path.rmdir()
                cleaned.append(str(dir_path.relative_to(BASE_DIR)))
            except:
                pass

    if cleaned:
        print(f"\n清理了 {len(cleaned)} 个空目录")


def generate_structure_report():
    """生成目录结构报告"""
    report_path = BASE_DIR / 'docs' / 'DIRECTORY_STRUCTURE.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# TOP_N 项目目录结构\n\n")
        f.write("## 目录说明\n\n")
        f.write("```\n")
        f.write("TOP_N/\n")
        f.write("├── backend/           # 后端代码\n")
        f.write("│   ├── models.py      # 数据库模型\n")
        f.write("│   ├── auth.py        # 认证模块\n")
        f.write("│   ├── encryption.py  # 加密工具\n")
        f.write("│   └── app_with_upload.py  # 主应用\n")
        f.write("├── frontend/          # 前端代码（月栖官网）\n")
        f.write("├── static/            # 静态资源（CSS/JS/图片）\n")
        f.write("├── templates/         # HTML模板\n")
        f.write("├── accounts/          # 平台账号配置\n")
        f.write("├── data/              # 生成的文章数据\n")
        f.write("├── uploads/           # 用户上传文件\n")
        f.write("├── scripts/           # 脚本文件\n")
        f.write("│   ├── deploy/        # 部署脚本\n")
        f.write("│   ├── install/       # 安装脚本\n")
        f.write("│   ├── test/          # 测试脚本\n")
        f.write("│   ├── fix/           # 修复脚本\n")
        f.write("│   └── check/         # 检查脚本\n")
        f.write("├── docs/              # 文档\n")
        f.write("├── archive/           # 归档文件\n")
        f.write("│   ├── python_installers/  # Python安装包\n")
        f.write("│   ├── chromedriver/       # ChromeDriver文件\n")
        f.write("│   └── temp/              # 临时文件\n")
        f.write("├── README.md          # 项目说明\n")
        f.write("├── MYSQL_MIGRATION_README.md  # MySQL迁移文档\n")
        f.write("├── requirements.txt   # Python依赖\n")
        f.write("└── start.sh           # 启动脚本\n")
        f.write("```\n\n")
        f.write(f"**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"\n[OK] 目录结构文档已生成: {report_path.relative_to(BASE_DIR)}")


def main():
    """主函数"""
    print("=" * 70)
    print("TOP_N 项目目录重组")
    print("=" * 70)

    # 步骤 1: 创建目录结构
    print("\n[步骤 1/5] 创建新目录结构...")
    create_directory_structure()

    # 步骤 2: 移动文件
    print("\n[步骤 2/5] 分类和移动文件...")
    moved, skipped = categorize_and_move_files()

    # 步骤 3: 清理空目录
    print("\n[步骤 3/5] 清理空目录...")
    clean_empty_directories()

    # 步骤 4: 生成文档
    print("\n[步骤 4/5] 生成目录结构文档...")
    generate_structure_report()

    # 步骤 5: 总结
    print("\n[步骤 5/5] 重组完成!")
    print("=" * 70)
    print(f"[OK] 已移动文件: {moved} 个")
    print(f"[SKIP] 保留根目录: {skipped} 个")
    print(f"[OK] 新目录结构已创建")
    print("=" * 70)

    print("\n重要目录:")
    for dir_name in ['backend', 'static', 'templates', 'scripts', 'docs', 'archive']:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists():
            file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
            print(f"  {dir_name}/  ({file_count} 个文件)")

    print("\n下一步:")
    print("  1. 检查 docs/DIRECTORY_STRUCTURE.md 确认目录结构")
    print("  2. 在服务器上执行相同的重组")
    print("  3. 测试系统功能是否正常")


if __name__ == '__main__':
    main()
