@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

rem --- 移動元フォルダ: %USERPROFILE%\Downloads ---

rem --- 振り分け処理 ---

rem --- [ルール] 「kaunet_」を含むファイルを「"C:\LocalApp\kaunet_APP\DATA"」へ安全に移動 ---
if not exist ""C:\LocalApp\kaunet_APP\DATA"" (mkdir ""C:\LocalApp\kaunet_APP\DATA"")
for %%F in ("%USERPROFILE%\Downloads\*kaunet_*") do (
    echo.
    echo [処理対象] "%%~nxF"
    copy "%%F" ""C:\LocalApp\kaunet_APP\DATA"\" > nul
    fc /b "%%F" ""C:\LocalApp\kaunet_APP\DATA"\%%~nxF" > nul
    if !errorlevel! == 0 (
        echo   ...OK。元ファイルを削除します。
        del "%%F"
    ) else (
        echo   ...[警告] 整合性エラー。ファイルを両方残します。
    )
)

rem --- [ルール] 「業務日報_」を含むファイルを「"C:\LocalApp\nippo\DATA"」へ安全に移動 ---
if not exist ""C:\LocalApp\nippo\DATA"" (mkdir ""C:\LocalApp\nippo\DATA"")
for %%F in ("%USERPROFILE%\Downloads\*業務日報_*") do (
    echo.
    echo [処理対象] "%%~nxF"
    copy "%%F" ""C:\LocalApp\nippo\DATA"\" > nul
    fc /b "%%F" ""C:\LocalApp\nippo\DATA"\%%~nxF" > nul
    if !errorlevel! == 0 (
        echo   ...OK。元ファイルを削除します。
        del "%%F"
    ) else (
        echo   ...[警告] 整合性エラー。ファイルを両方残します。
    )
)

rem --- [ルール] 「todolist.csv」を含むファイルを「"C:\LocalApp\TODOlist_APP"」へ安全に移動 ---
if not exist ""C:\LocalApp\TODOlist_APP"" (mkdir ""C:\LocalApp\TODOlist_APP"")
for %%F in ("%USERPROFILE%\Downloads\*todolist.csv*") do (
    echo.
    echo [処理対象] "%%~nxF"
    copy "%%F" ""C:\LocalApp\TODOlist_APP"\" > nul
    fc /b "%%F" ""C:\LocalApp\TODOlist_APP"\%%~nxF" > nul
    if !errorlevel! == 0 (
        echo   ...OK。元ファイルを削除します。
        del "%%F"
    ) else (
        echo   ...[警告] 整合性エラー。ファイルを両方残します。
    )
)

rem --- [ルール] 「日報APP_」を含むファイルを「"C:\LocalApp\nippo\DATA"」へ安全に移動 ---
if not exist ""C:\LocalApp\nippo\DATA"" (mkdir ""C:\LocalApp\nippo\DATA"")
for %%F in ("%USERPROFILE%\Downloads\*日報APP_*") do (
    echo.
    echo [処理対象] "%%~nxF"
    copy "%%F" ""C:\LocalApp\nippo\DATA"\" > nul
    fc /b "%%F" ""C:\LocalApp\nippo\DATA"\%%~nxF" > nul
    if !errorlevel! == 0 (
        echo   ...OK。元ファイルを削除します。
        del "%%F"
    ) else (
        echo   ...[警告] 整合性エラー。ファイルを両方残します。
    )
)

rem --- 処理完了 ---
echo.
echo 全ての処理が完了しました。
pause
