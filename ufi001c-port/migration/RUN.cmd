@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not defined UFI_EDL_ROOT set "UFI_EDL_ROOT=%USERPROFILE%\edl"
rem Smart launcher: prefer the bundled PyInstaller exe when present,
rem otherwise fall back to the EDL Python environment.
if exist "%~dp0runtime\UFI001C-Installer.exe" (
  "%~dp0runtime\UFI001C-Installer.exe" %*
  exit /b %ERRORLEVEL%
)
if not exist "%UFI_EDL_ROOT%\.venv\Scripts\python.exe" goto missing
set "PYTHONUTF8=1"
"%UFI_EDL_ROOT%\.venv\Scripts\python.exe" -u "%~dp0stock_install.py" %*
exit /b %ERRORLEVEL%
:missing
echo Не найден рабочий EDL: %UFI_EDL_ROOT%
echo На этом ПК нужен Python/EDL и USB-драйвер, с которыми уже прошивался модем.
echo Если EDL находится в другой папке, задайте UFI_EDL_ROOT и повторите запуск.
echo Инструкция: ..\ИНСТРУКЦИЯ.txt
pause
exit /b 1
