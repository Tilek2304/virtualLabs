@echo off
REM Python тиркемелерин EXE форматына чогултуу үчүн скрипт
REM .\venv ичиндеги виртуалдык чөйрөнү колдонот
REM labsKG папкасындагы бардык main.py файлдарын чогултат

setlocal enabledelayedexpansion

echo 🔨 building exe files...
echo.

REM Виртуалдык чөйрөнү иштетүү (venv папкасынан)
if exist ".\venv\Scripts\activate.bat" (
    call .\venv\Scripts\activate.bat
) else (
    echo ❌ error: .\venv is not found!
    pause
    exit /b
)

echo ✅ venv activated

REM Керектүү пакеттерди орнотуу
echo 📦 pip installing
pip install --quiet pyinstaller pyside6 numpy

echo.

REM Сборкалар үчүн папканы түзүү (эгер жок болсо)
REM Биз dist_kg деп атайбыз, орус версиясы менен чаташтырбоо үчүн
if not exist dist_kg mkdir dist_kg

REM Ийгиликтүү чогултулган файлдардын саны
set BUILT=0
set FAILED=0

REM labsKG папкасынын ичиндеги бардык папкаларды карайбыз
for /d %%D in (labsKG\*) do (
    REM Толук жолду алабыз (мисалы: labsKG\l1)
    set FULL_PATH=%%D
    REM Папканын атын гана алабыз (мисалы: l1)
    set LAB_NAME=%%~nxD
    
    REM main.py бар экенин текшерүү
    if exist "!FULL_PATH!\main.py" (
        echo 🔨 !LAB_NAME! building...
        
        REM PyInstaller иштетүү
        pyinstaller ^
            --onefile ^
            --windowed ^
            --name "!LAB_NAME!" ^
            --distpath ".\dist_kg" ^
            --workpath ".\build_kg\!LAB_NAME!" ^
            --specpath ".\specs_kg" ^
            --noupx ^
            --hidden-import=PySide6 ^
            "!FULL_PATH!\main.py" 2>&1 | find "completed successfully"
        
        if !errorlevel! equ 0 (
            echo ✅ !LAB_NAME! success
            set /a BUILT+=1
        ) else (
            echo ❌ !LAB_NAME! error
            set /a FAILED+=1
        )
        echo.
    )
)

echo ═══════════════════════════════════════════
echo 📊 result:
echo ✅ builded successfully: %BUILT%
if %FAILED% gtr 0 (
    echo ❌ errors: %FAILED%
)
echo 📁 EXE files in here: .\dist_kg\
echo ═══════════════════════════════════════════
echo.
echo 💡 Эскертүүлөр:
echo   - Эгер SmartScreen файлдарды бөгөттөп жатса:
echo   - Файлды касиеттери аркылуу бөгөттөн чыгарыңыз (Properties -> Unblock)
echo   - Же файлды браузер аркылуу кайра жүктөп көрүңүз
echo.
pause