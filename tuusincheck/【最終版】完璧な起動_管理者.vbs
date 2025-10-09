Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' スクリプトのディレクトリを取得
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' network_monitor_v2.pyのパス
strScript = strScriptPath & "\network_monitor_v2.py"

' 管理者権限で実行（pythonw.exeを使用してプロンプト非表示）
Set objApp = CreateObject("Shell.Application")
objApp.ShellExecute "pythonw.exe", """" & strScript & """ --silent", strScriptPath, "runas", 0

Set objApp = Nothing
Set objFSO = Nothing
Set objShell = Nothing
