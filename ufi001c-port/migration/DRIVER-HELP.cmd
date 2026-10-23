@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo Установка драйверов Qualcomm из папки drivers\
echo.
set "DRVDIR=%~dp0drivers"
if not exist "%DRVDIR%\*.inf" (
  echo В папке drivers\ нет .inf файлов.
  echo Положите туда файлы драйвера ^(.inf, .cat, .sys^) и запустите снова.
  echo Где взять драйвер: см. DRIVER-RU.txt
  pause
  exit /b 1
)
echo Найдены INF-файлы, устанавливаю (нужны права администратора)...
pnputil /add-driver "%DRVDIR%\*.inf" /install
set "UFI_RESULT=%ERRORLEVEL%"
echo.
if "%UFI_RESULT%"=="0" (
  echo Драйверы установлены. Переподключите модем.
) else (
  echo Не удалось установить автоматически (код %UFI_RESULT%).
  echo Попробуйте вручную: правый клик по .inf -^> Установить,
  echo или запустите этот файл от имени администратора.
)
pause
exit /b %UFI_RESULT%
