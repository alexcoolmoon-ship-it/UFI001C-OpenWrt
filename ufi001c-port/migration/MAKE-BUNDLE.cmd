@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
call "%~dp0RUN.cmd" bundle
set "UFI_RESULT=%ERRORLEVEL%"
echo.
if not "%UFI_RESULT%"=="0" echo Выполнение остановлено. Сохраните папку UFI001C-backups и журнал.
pause
exit /b %UFI_RESULT%
