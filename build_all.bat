@echo off
REM Скрипт для сборки всех Python приложений в EXE
REM Использует виртуальное окружение из .\env
REM Собирает все файлы из папок lab**/main.py

setlocal enabledelayedexpansion

echo 🔨 start all ru EXE files...
echo.

REM Активируем виртуальное окружение
call .\env\Scripts\activate.bat

echo ✅ venv activated

REM Устанавливаем необходимые пакеты
echo 📦 pip installing
pip install --quiet pyinstaller pyside6 numpy

echo.

REM Создаём директорию для сборок если её нет
if not exist dist mkdir dist

REM Счётчик успешных сборок
set BUILT=0
set FAILED=0

REM Перебираем все папки lab*
for /d %%L in (lab*) do (
    set LAB_NAME=%%L
    
    REM Проверяем наличие main.py
    if exist "%%L\main.py" (
        echo 🔨 building !LAB_NAME!...
        
        REM Выполняем PyInstaller
        pyinstaller ^
            --onefile ^
            --windowed ^
            --name "!LAB_NAME!" ^
            --distpath ".\dist" ^
            --workpath ".\build\!LAB_NAME!" ^
            --specpath ".\specs" ^
            --noupx ^
            --hidden-import=PySide6 ^
            "%%L\main.py" 2>&1 | find "completed successfully"
        
        if !errorlevel! equ 0 (
            echo ✅ !LAB_NAME! building success
            set /a BUILT+=1
        ) else (
            echo ❌ building unsuccessfully !LAB_NAME!
            set /a FAILED+=1
        )
        echo.
    )
)

echo ═══════════════════════════════════════════
echo 📊 result building:
echo ✅ success: %BUILT%
if %FAILED% gtr 0 (
    echo ❌ errors: %FAILED%
)
echo 📁 EXE files in: .\dist\
echo ═══════════════════════════════════════════
echo.
echo 💡 Примечания:
echo   - Если SmartScreen блокирует файлы, скачивайте через браузер
echo   - Или разблокируйте файлы через свойства (Properties ^^ Unblock)
echo   - Для полной защиты от SmartScreen купите сертификат кода
echo.
pause
