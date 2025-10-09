Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' スクリプトのディレクトリを取得
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' カレントディレクトリを変更
objShell.CurrentDirectory = strScriptPath

' network_monitor_v2.pyのパス
strScript = strScriptPath & "\network_monitor_v2.py"

' pythonw.exeで実行（プロンプト画面なし、GUIは表示）
' --silentオプションのみ（--minimizedは使わない）
objShell.Run "pythonw.exe """ & strScript & """ --silent", 0, False

' 少し待ってからウィンドウを表示状態に
WScript.Sleep 1000

' ウィンドウを探して前面に表示
Set objWMI = GetObject("winmgmts:\\.\root\cimv2")
Set colProcesses = objWMI.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'pythonw.exe'")

For Each objProcess in colProcesses
    ' プロセスのコマンドラインに"network_monitor_v2.py"が含まれているか確認
    If InStr(objProcess.CommandLine, "network_monitor_v2.py") > 0 Then
        ' プロセスIDからウィンドウハンドルを取得して表示
        ' （Tkinterウィンドウは自動的にタスクバーに表示される）
        Exit For
    End If
Next

Set colProcesses = Nothing
Set objWMI = Nothing
Set objFSO = Nothing
Set objShell = Nothing
