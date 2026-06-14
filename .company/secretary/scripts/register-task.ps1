$taskName = 'YNFactory-MorningBriefing'
$scriptPath = 'C:\YNFactory-cc\.company\secretary\scripts\morning-briefing.ps1'

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$argStr = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $scriptPath + '"'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argStr
$trigger = New-ScheduledTaskTrigger -Daily -At '6:30AM'
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description '毎朝6:30に今日のTODOをブリーフィング通知(YNFactory秘書室)' | Out-Null

Get-ScheduledTask -TaskName $taskName |
    Select-Object TaskName, State, @{N='NextRun'; E={(Get-ScheduledTaskInfo $_).NextRunTime}} |
    Format-List
