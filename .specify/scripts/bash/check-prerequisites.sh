#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != "--json" ]]; then
  echo '{"error":"expected --json"}'
  exit 1
fi

if [[ "${2:-}" != "--require-tasks" ]]; then
  echo '{"error":"expected --require-tasks"}'
  exit 1
fi

if [[ "${3:-}" != "--include-tasks" ]]; then
  echo '{"error":"expected --include-tasks"}'
  exit 1
fi

if [[ -f "specs/job-copilot-backend/tasks.md" && -f "specs/job-copilot-backend/plan.md" ]]; then
  printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":["plan.md","tasks.md"]}\n' "$(pwd)/specs/job-copilot-backend"
else
  printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":[]}\n' "$(pwd)/specs/job-copilot-backend"
fi
