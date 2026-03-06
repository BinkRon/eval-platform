#!/bin/bash
# Stop hook: 任务完成后自动检测未提交变更并触发 /commit skill
# [已关闭] 项目初期直接放行，后续稳定后启用

exit 0

# --- 以下逻辑暂时关闭 ---

INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# 防止无限循环：commit 后再次触发时直接放行
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

# 切换到项目目录
cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0

# 检查是否在 git 仓库中
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# 检查工作区是否有变更（已修改、已暂存、新文件）
if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null && [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
  # 没有变更，正常结束
  exit 0
fi

# 有未提交变更，阻止 Claude 停止，让它继续执行 commit
cat <<'EOF'
{"decision": "block", "reason": "检测到未提交的变更，请调用 /commit 技能提交更新。"}
EOF
