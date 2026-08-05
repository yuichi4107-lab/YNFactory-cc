@echo off
setlocal
cd /d "%~dp0"

rem Step 1: fetch recent Limitless lifelogs (last 3 days).
rem Failure here must not block the Notion sync, so errors are tolerated.
rem Run from biz_idea_generator so load_dotenv() finds LIMITLESS_API_KEY.
pushd "..\..\biz_idea_generator"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -X utf8 "..\04_インプット\inputs\sync_limitless.py" --range 3
) else (
  py -3 -X utf8 "..\04_インプット\inputs\sync_limitless.py" --range 3
)
popd

rem Step 2: register new inputs into Notion (create-only; Notion is the master).
if exist "..\..\biz_idea_generator\.venv\Scripts\python.exe" (
  "..\..\biz_idea_generator\.venv\Scripts\python.exe" "sync_notion.py" %*
) else (
  py -3 "sync_notion.py" %*
)

rem Step 3: mirror Notion (master) back to local files for backup and pipelines.
if exist "..\..\biz_idea_generator\.venv\Scripts\python.exe" (
  "..\..\biz_idea_generator\.venv\Scripts\python.exe" "mirror_notion.py"
) else (
  py -3 "mirror_notion.py"
)
