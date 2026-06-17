#!/usr/bin/env bash
# Shared environment helpers for shorts-factory shell entrypoints.

shorts_resolve_repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

  local candidates=()
  if [ -n "${SHORTS_REPO_ROOT:-}" ]; then
    candidates+=("$SHORTS_REPO_ROOT")
  fi
  if [ -n "${YNFACTORY_ROOT:-}" ]; then
    candidates+=("$YNFACTORY_ROOT")
  fi
  candidates+=(
    "$script_dir/../.."
    "$(pwd)"
    "$HOME/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc"
    "$HOME/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc"
    "$HOME/YNFactory-cc"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    [ -n "$candidate" ] || continue
    if [ -d "$candidate/shorts-factory/src" ]; then
      (cd "$candidate" && pwd -P)
      return 0
    fi
  done

  return 1
}
