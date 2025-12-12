#!/bin/bash
# GitHub 自动推送脚本

echo "============================================================"
echo "TOP_N Project - GitHub Push Script"
echo "============================================================"

cd D:/code/TOP_N

# 检查是否有远程仓库
echo ""
echo "[1] Checking remote repository..."
if git remote | grep -q origin; then
    echo "    Remote 'origin' already exists:"
    git remote -v | head -2

    read -p "    Remove and re-add? (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        git remote remove origin
        echo "    Remote removed."
    else
        echo "    Keeping existing remote."
    fi
fi

# 添加远程仓库（如果不存在）
if ! git remote | grep -q origin; then
    echo ""
    echo "[2] Adding remote repository..."
    echo "    Choose authentication method:"
    echo "    1) HTTPS with username/password"
    echo "    2) HTTPS with Personal Access Token"
    echo "    3) SSH (requires SSH key setup on GitHub)"

    read -p "    Select (1-3): " method

    case $method in
        1)
            git remote add origin https://github.com/topn2024/TOP_N.git
            echo "    Added: https://github.com/topn2024/TOP_N.git"
            echo "    You will be prompted for username and password"
            ;;
        2)
            read -p "    Enter your Personal Access Token: " token
            git remote add origin https://topn2024:$token@github.com/topn2024/TOP_N.git
            echo "    Added: https://topn2024:<TOKEN>@github.com/topn2024/TOP_N.git"
            ;;
        3)
            git remote add origin git@github.com:topn2024/TOP_N.git
            echo "    Added: git@github.com:topn2024/TOP_N.git"
            ;;
        *)
            echo "    Invalid selection. Using HTTPS..."
            git remote add origin https://github.com/topn2024/TOP_N.git
            ;;
    esac
fi

# 显示当前状态
echo ""
echo "[3] Current repository status:"
echo "    Remote:"
git remote -v | head -2 | sed 's/^/      /'
echo ""
echo "    Commits:"
git log --oneline -1 | sed 's/^/      /'
echo ""
echo "    Files to push: $(git ls-files | wc -l) files"

# 确认推送
echo ""
read -p "[4] Push to GitHub? (Y/n): " confirm
if [[ $confirm == [nN] ]]; then
    echo "    Cancelled by user."
    exit 0
fi

# 推送代码
echo ""
echo "[5] Pushing to GitHub..."
echo "    This may take a while for initial push..."
echo ""

if git push -u origin master; then
    echo ""
    echo "============================================================"
    echo "SUCCESS! Code pushed to GitHub!"
    echo "============================================================"
    echo ""
    echo "Repository URL:"
    echo "  https://github.com/topn2024/TOP_N"
    echo ""
    echo "Next steps:"
    echo "  1. Visit the repository to verify"
    echo "  2. Add repository description and topics"
    echo "  3. Create a release (optional)"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "PUSH FAILED"
    echo "============================================================"
    echo ""
    echo "Common issues:"
    echo "  1. Authentication failed"
    echo "     - Use Personal Access Token instead of password"
    echo "     - Or setup SSH keys"
    echo ""
    echo "  2. Repository doesn't exist"
    echo "     - Create repository on GitHub first:"
    echo "       https://github.com/new"
    echo "     - Repository name: TOP_N"
    echo "     - Don't initialize with README"
    echo ""
    echo "  3. Network issues"
    echo "     - Check internet connection"
    echo "     - Try again later"
    echo ""
    echo "For detailed instructions, see:"
    echo "  GITHUB_SETUP_GUIDE.md"
    echo ""
    exit 1
fi
