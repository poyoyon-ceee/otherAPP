Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' スクリプトのディレクトリを取得
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' カレントディレクトリを変更
objShell.CurrentDirectory = strScriptPath

' Pythonスクリプトのパスを構築
strPythonScript = strScriptPath & "\network_monitor_v3.py"

' 完全にバックグラウンドで実行（ウィンドウ非表示、フォーカス奪取なし）
objShell.Run "pythonw """ & strPythonScript & """ --silent --minimized", 0, False

Set objShell = Nothing
Set objFSO = Nothing
