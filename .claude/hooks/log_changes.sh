#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

DATE=$(date '+%Y-%m-%d %H:%M:%S')
TOOL=$(echo "$INPUT" | jq -r '.tool_name')
echo "- [$DATE] \`$TOOL\` → \`$FILE\`" >> "$CLAUDE_PROJECT_DIR/CHANGES.md"
exit 0
