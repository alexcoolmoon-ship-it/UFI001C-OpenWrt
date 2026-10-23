@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem --- Проверка драйвера Qualcomm (нужен для режима EDL 9008) ---
echo Проверка драйвера Qualcomm...
pnputil /enum-drivers 2>nul | findstr /i "qualcomm" >nul
if %errorlevel%==0 goto driver_ok
pnputil /enum-devices /connected 2>nul | findstr /i "9008" >nul
if %errorlevel%==0 goto driver_ok

echo.
echo ============================================================
echo  НЕ НАЙДЕН драйвер Qualcomm (нужен для режима EDL 9008).
echo  Без него модем в сервисном режиме не будет виден.
echo ============================================================
echo.
echo  Как установить:
echo    1. Положите файлы драйвера (.inf, .cat, .sys) в tools\drivers\
echo    2. Запустите tools\DRIVER-HELP.cmd от имени администратора
echo  Подробности: tools\DRIVER-RU.txt
echo.
set /p UFI_NODRIVER="Продолжить без драйвера? [y/N]: "
if /i not "%UFI_NODRIVER%"=="y" exit /b 1
echo.

:driver_ok
call "%~dp0tools\RUN.cmd" install
set "UFI_RESULT=%ERRORLEVEL%"
echo.
if not "%UFI_RESULT%"=="0" echo Выполнение остановлено. Сохраните папку UFI001C-backups и журнал.
pause
exit /b %UFI_RESULT%
