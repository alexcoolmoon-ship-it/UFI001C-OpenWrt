@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
call "%~dp0RUN.cmd" probe
set "UFI_RESULT=%ERRORLEVEL%"
echo.
if not "%UFI_RESULT%"=="0" echo Проверка остановлена. Сохраните stock-probe.json (если создан) и журнал.
pause
exit /b %UFI_RESULT%
