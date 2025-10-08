Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' スクリプトのディレクトリを取得
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Pythonスクリプトのパスを構築
strPythonScript = strScriptPath & "\network_monitor_v2.py"

' 管理者権限でサイレントモード＆最小化実行
objShell.Run "pythonw """ & strPythonScript & """ --silent --minimized", 0, False

Set objShell = Nothing
Set objFSO = Nothing
