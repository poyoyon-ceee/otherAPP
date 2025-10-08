Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' スクリプトのディレクトリを取得
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Pythonスクリプトのパスを構築
strPythonScript = strScriptPath & "\network_monitor_v2.py"

' バックグラウンドで実行（ウィンドウを表示しない）
objShell.Run "pythonw """ & strPythonScript & """", 0, False

' 完了メッセージ（オプション）
' MsgBox "アプリをバックグラウンドで起動しました", vbInformation, "起動完了"

Set objShell = Nothing
Set objFSO = Nothing
