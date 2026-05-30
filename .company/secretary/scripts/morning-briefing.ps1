# Morning Briefing Script for YNFactory Secretary
# - Reads today's TODO file from .company/secretary/todos/YYYY-MM-DD.md
# - If missing: carries over unchecked tasks from the latest previous day's file
# - Displays a Windows toast notification summarizing priorities
# - Sends the briefing to Telegram

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'

$TodosDir = 'G:\マイドライブ\YNFactory-cc\.company\secretary\todos'
$LogDir   = 'G:\マイドライブ\YNFactory-cc\.company\secretary\scripts\logs'

# Telegram config (kyoyaru_bot = 今日のやること)
# 2026-05-30 ハードコード除去。User環境変数 TG_BOT_TOKEN / TG_CHAT_ID から取得する。
# Task Scheduler から実行する場合、登録ユーザーの環境変数が引き継がれることを確認すること。
$TG_BOT_TOKEN = [Environment]::GetEnvironmentVariable('TG_BOT_TOKEN','User')
$TG_CHAT_ID   = [Environment]::GetEnvironmentVariable('TG_CHAT_ID','User')
if ([string]::IsNullOrEmpty($TG_BOT_TOKEN)) { $TG_CHAT_ID = '8571447808' }
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile  = Join-Path $LogDir ('briefing-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')

function Write-Log($msg) {
    $line = '[' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '] ' + $msg
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

try {
    $today     = Get-Date
    $todayStr  = $today.ToString('yyyy-MM-dd')
    $dayJp     = @('日','月','火','水','木','金','土')[[int]$today.DayOfWeek]
    $todayFile = Join-Path $TodosDir ($todayStr + '.md')

    Write-Log "Start briefing for $todayStr ($dayJp)"

    # Parse a TODO file into sections -> list of lines
    function Parse-Todo($path) {
        $sections = [ordered]@{
            '最優先'         = New-Object System.Collections.Generic.List[string]
            '通常'           = New-Object System.Collections.Generic.List[string]
            '余裕があれば'   = New-Object System.Collections.Generic.List[string]
            '完了'           = New-Object System.Collections.Generic.List[string]
            'メモ・振り返り' = New-Object System.Collections.Generic.List[string]
        }
        if (-not (Test-Path -LiteralPath $path)) { return $sections }
        $current = $null
        foreach ($line in Get-Content -LiteralPath $path -Encoding UTF8) {
            if ($line -match '^##\s+(.+)$') {
                $name = $matches[1].Trim()
                if ($sections.Contains($name)) { $current = $name } else { $current = $null }
                continue
            }
            if ($null -ne $current) { $sections[$current].Add($line) }
        }
        return $sections
    }

    # Build today's file from yesterday's unfinished tasks if missing
    if (-not (Test-Path -LiteralPath $todayFile)) {
        Write-Log "Today's file missing. Carrying over from previous day."

        $prev = Get-ChildItem -LiteralPath $TodosDir -Filter '*.md' |
                Where-Object { $_.BaseName -match '^\d{4}-\d{2}-\d{2}$' -and $_.BaseName -lt $todayStr } |
                Sort-Object BaseName -Descending |
                Select-Object -First 1

        $carried = @{ '最優先' = @(); '通常' = @(); '余裕があれば' = @() }
        if ($null -ne $prev) {
            Write-Log ('Previous file: ' + $prev.Name)
            $parsed = Parse-Todo $prev.FullName
            foreach ($sec in @('最優先','通常','余裕があれば')) {
                $carried[$sec] = @($parsed[$sec] | Where-Object { $_ -match '^\s*-\s*\[\s\]\s*.+' })
            }
        } else {
            Write-Log 'No previous TODO file found.'
        }

        $lines = New-Object System.Collections.Generic.List[string]
        $lines.Add('---')
        $lines.Add('date: "' + $todayStr + '"')
        $lines.Add('type: daily')
        $lines.Add('---')
        $lines.Add('')
        $lines.Add('# ' + $todayStr + ' (' + $dayJp + ')')
        $lines.Add('')
        foreach ($sec in @('最優先','通常','余裕があれば')) {
            $lines.Add('## ' + $sec)
            if ($carried[$sec] -and $carried[$sec].Count -gt 0) {
                foreach ($t in $carried[$sec]) { $lines.Add($t) }
            } else {
                $lines.Add('- [ ]')
            }
            $lines.Add('')
        }
        $lines.Add('## 完了')
        $lines.Add('- [x]')
        $lines.Add('')
        $lines.Add('## メモ・振り返り')
        $lines.Add('-')
        $lines.Add('')

        Set-Content -LiteralPath $todayFile -Value $lines -Encoding UTF8
        Write-Log ('Created: ' + $todayFile)
    } else {
        Write-Log 'Today file already exists.'
    }

    # Read today's tasks for briefing
    $todos = Parse-Todo $todayFile
    function Get-Open($section) {
        return @($todos[$section] | Where-Object { $_ -match '^\s*-\s*\[\s\]\s*\S' } |
                 ForEach-Object { ($_ -replace '^\s*-\s*\[\s\]\s*','').Trim() })
    }
    $p1 = Get-Open '最優先'
    $p2 = Get-Open '通常'
    $p3 = Get-Open '余裕があれば'

    Write-Log ('Counts: 最優先=' + @($p1).Count + ' 通常=' + @($p2).Count + ' 余裕=' + @($p3).Count)

    function Fmt-Task($s, $limit = 60) {
        if ($s.Length -gt $limit) { return $s.Substring(0, $limit) + '…' } else { return $s }
    }
    $bodyLines = New-Object System.Collections.Generic.List[string]
    if (@($p1).Count -gt 0) {
        $bodyLines.Add('[最優先] (' + @($p1).Count + '件)')
        foreach ($t in ($p1 | Select-Object -First 3)) { $bodyLines.Add('・' + (Fmt-Task $t)) }
    }
    if (@($p2).Count -gt 0) {
        $bodyLines.Add('[通常] (' + @($p2).Count + '件)')
        foreach ($t in ($p2 | Select-Object -First 2)) { $bodyLines.Add('・' + (Fmt-Task $t)) }
    }
    if (@($p3).Count -gt 0) {
        $bodyLines.Add('[余裕があれば] (' + @($p3).Count + '件)')
    }
    if ($bodyLines.Count -eq 0) { $bodyLines.Add('本日の未完了タスクはありません') }

    $title = 'おはようございます — ' + $todayStr + ' (' + $dayJp + ')'
    $body  = $bodyLines -join "`n"

    # Try WinRT Toast (native Windows 10/11)
    $toastShown = $false
    try {
        [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
        [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]

        $escTitle = [System.Security.SecurityElement]::Escape($title)
        $escBody  = [System.Security.SecurityElement]::Escape($body)
        $xmlStr = "<toast><visual><binding template='ToastGeneric'><text>$escTitle</text><text>$escBody</text></binding></visual></toast>"

        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($xmlStr)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('YNFactory.Secretary')
        $notifier.Show($toast)
        $toastShown = $true
        Write-Log 'Toast shown via WinRT API.'
    } catch {
        Write-Log ('WinRT toast failed: ' + $_.Exception.Message)
    }

    if (-not $toastShown) {
        # Fallback: MessageBox
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show($body, $title) | Out-Null
        Write-Log 'Shown via MessageBox fallback.'
    }

    # Send to Telegram (skip if already sent today — prevents duplicate from Drive sync)
    $sentMarkerDir = Join-Path $env:LOCALAPPDATA 'YNFactory-Briefing'
    New-Item -ItemType Directory -Force -Path $sentMarkerDir | Out-Null
    $sentMarker = Join-Path $sentMarkerDir ('tg-sent-' + $todayStr)
    if (Test-Path -LiteralPath $sentMarker) {
        Write-Log 'Telegram already sent today, skipping.'
    } else {
        try {
            $tgText = $title + "`n`n" + $body
            $tgUrl  = "https://api.telegram.org/bot$TG_BOT_TOKEN/sendMessage"
            $postData = 'chat_id=' + [System.Uri]::EscapeDataString($TG_CHAT_ID) + '&text=' + [System.Uri]::EscapeDataString($tgText)
            $wc = New-Object System.Net.WebClient
            $wc.Encoding = [System.Text.Encoding]::UTF8
            $wc.Headers.Add('Content-Type', 'application/x-www-form-urlencoded; charset=utf-8')
            $resp = $wc.UploadString($tgUrl, $postData)
            Set-Content -LiteralPath $sentMarker -Value (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
            Write-Log 'Telegram sent OK.'
        } catch {
            Write-Log ('Telegram send failed: ' + $_.Exception.Message)
        }
    }

    Write-Log 'Done.'
    exit 0
} catch {
    Write-Log ('ERROR: ' + $_.Exception.Message)
    Write-Log $_.ScriptStackTrace
    exit 1
}
