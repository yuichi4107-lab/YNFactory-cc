---
date: 2026-06-14
status: implemented
owner_request: "G Drive dependent scheduled tasks should run from the local C-drive/local workspace foundation"
---

# Local Scheduled Tasks Drive Decoupling

## Goal

Move recurring scheduled-task execution away from Google Drive paths so startup timing and Drive sync state do not break regular automation.

## Scope

- Mac LaunchAgent runners:
  - `com.ynfactory.inputs-auto-import`
  - `com.yn.limitless-sync`
  - `com.yn.daily-priority`
  - `com.ynfactory.telegram-channel`
  - indirect `com.ynfactory.daily-handoff` dependency via `tg-bot`
- Windows scheduled-task wrappers that still referenced `G:\マイドライブ\YNFactory-cc`.
- Local runtime support:
  - local Python venv under `/Users/yuichi/YNFactory-cc/biz_idea_generator/.venv`
  - local `.env` copy, kept ignored by git

## Non-Scope

- Deleting old Google Drive source folders.
- Publishing, posting, or sending external messages.
- Changing external Google Apps Script authorization.

## Completion Criteria

- Scheduled runners use `/Users/yuichi/YNFactory-cc` on Mac and `C:\YNFactory-cc` in Windows wrappers.
- Python execution prefers the local project venv and does not execute packages from Google Drive.
- `daily_priority.py` reads TODO, persona, and env from the local workspace by default.
- `inputs-auto-import` and `limitless-sync` can be syntax-checked and manually smoke-tested without Google Drive as cwd.
- Remaining Drive references are either historical logs/docs or external input/storage descriptions, not active scheduled-task runtime paths.

## Quality Check

Score: 91/100 PASS

- Drive runtime dependency removed from active wrappers: 25/25
- Local venv/env foundation prepared: 20/20
- Input automation keeps existing importer behavior: 18/20
- Windows C-drive wrappers aligned: 14/15
- Verification coverage: 14/20

Residual risk:

- Real launchd re-bootstrap may require a logged-in GUI session; manual smoke tests cover script execution paths.
- If Google Apps Script still writes only to the old Drive-synced `00_INPUT_BOX` / `00_GOOGLE_MEET_BOX`, those folders must either be copied/synced into the local workspace or passed via `YN_INPUT_BOX` / `--source-dir`.
