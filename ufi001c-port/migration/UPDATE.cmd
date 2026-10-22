@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ================================================================================
echo  ОБНОВЛЕНИЕ UFI001C (уже стоит OpenWrt)
echo ================================================================================
echo.
echo  Этот скрипт автоматически:
echo   1. Сделает бэкап текущего состояния
echo   2. Прошьёт новые boot.img и system.img
echo   3. Проверит результат
echo.
echo  Сохраните свою прокси-ссылку отдельно! Rootfs ставится начисто.
echo.
pause

set "PYTHON=%USERPROFILE%\edl\.venv\Scripts\python.exe"
set "BACKUP_DIR=%USERPROFILE%\UFI001C-backups"

if not exist "%PYTHON%" (
    echo ОШИБКА: Python окружение не найдено: %PYTHON%
    echo Сначала запустите DRIVER-HELP.cmd для настройки окружения.
    pause
    exit /b 1
)

echo.
echo [1/3] Создание бэкапа...
"%PYTHON%" ufi-install.py backup --images "%BACKUP_DIR%"
if %ERRORLEVEL% neq 0 (
    echo ОШИБКА бэкапа. Остановлено.
    pause
    exit /b 1
)

echo.
echo [2/3] Поиск свежего бэкапа...
for /f "delims=" %%f in ('dir /b /o-d "%BACKUP_DIR%\*\emmc.bin" 2^>nul') do (
    set "EMMC=%%f"
    goto :found
)
echo ОШИБКА: emmc.bin не найден в %BACKUP_DIR%
pause
exit /b 1

:found
echo  Найден: %EMMC%
echo.
echo [3/3] Прошивка обновления...
"%PYTHON%" ufi-install.py update --images . --backup "%EMMC%"
set "UFI_RESULT=%ERRORLEVEL%"

echo.
if "%UFI_RESULT%"=="0" (
    echo ================================================================================
    echo  ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО
    echo ================================================================================
    echo  Переподключите модем БЕЗ зажатой кнопки.
    echo  Откройте http://192.168.1.1 и настройте Podkop.
) else (
    echo  ОШИБКА обновления. Сохраните текст выше и папку %BACKUP_DIR%.
)
pause
exit /b %UFI_RESULT%
