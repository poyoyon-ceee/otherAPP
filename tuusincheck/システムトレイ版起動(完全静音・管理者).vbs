Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' スクリプトのディレクトリを取得
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' 管理者権限チェック用のバッチファイルを一時作成
strTempBat = objFSO.GetSpecialFolder(2) & "\network_monitor_launcher.bat"

' バッチファイルの内容を作成
Set objFile = objFSO.CreateTextFile(strTempBat, True)
objFile.WriteLine "@echo off"
objFile.WriteLine "cd /d """ & strScriptPath & """"
objFile.WriteLine "pythonw network_monitor_v3.py --silent --minimized"
objFile.Close

' 管理者権限で実行（ウィンドウは非表示）
Set objApp = CreateObject("Shell.Application")
objApp.ShellExecute strTempBat, "", "", "runas", 0

' 少し待ってから一時ファイルを削除
WScript.Sleep 2000
On Error Resume Next
objFSO.DeleteFile strTempBat
On Error Goto 0

Set objFile = Nothing
Set objApp = Nothing
Set objShell = Nothing
Set objFSO = Nothing
