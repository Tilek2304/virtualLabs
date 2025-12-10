#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка переведённых лабораторных работ в EXE файлы
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path("Переведённые_лабораторные")
OUTPUT_DIR = Path("distKG")
BUILD_DIR = Path("build")
SPECS_DIR = Path("specs")

# Создаём директории
OUTPUT_DIR.mkdir(exist_ok=True)
BUILD_DIR.mkdir(exist_ok=True)
SPECS_DIR.mkdir(exist_ok=True)

built = 0
failed = 0
errors = []

print("\n🔨 Начало сборки EXE файлов (Kyrgyz)...\n")

# Перебираем классы
class_dirs = sorted(BASE_DIR.glob("класс *"))
print(f"Найдено {len(list(class_dirs))} классов\n")

for class_dir in sorted(BASE_DIR.glob("класс *")):
    if not class_dir.is_dir():
        continue
    
    print(f"【 {class_dir.name} 】")
    print("─" * 60)
    
    # Перебираем лабораторные работы
    labs = sorted(class_dir.glob("lab*"))
    for lab_dir in labs:
        if not lab_dir.is_dir():
            continue
        
        main_py = lab_dir / "main.py"
        if not main_py.exists():
            continue
        
        lab_name = lab_dir.name
        exe_path = OUTPUT_DIR / f"{lab_name}.exe"
        
        print(f"  🔨 {lab_name}...", end=" ", flush=True)
        
        # Команда PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            f"--name={lab_name}",
            f"--distpath={OUTPUT_DIR}",
            f"--workpath={BUILD_DIR}/{lab_name}",
            f"--specpath={SPECS_DIR}",
            "--noupx",
            "--hidden-import=PySide6",
            str(main_py)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✅ ({size_mb:.1f} MB)")
            built += 1
        else:
            print("❌")
            failed += 1
            errors.append(f"{lab_name}: {result.stderr[:200]}")
    
    print()

print("═" * 60)
print(f"📊 ИТОГИ СБОРКИ:")
print(f"✅ Успешно: {built}")
if failed > 0:
    print(f"❌ Ошибок: {failed}")
print(f"📁 Выходная папка: {OUTPUT_DIR.absolute()}")
print("═" * 60)

if built > 0:
    print(f"\n✅ Собрано {built} EXE файлов\n")
    print("📋 Файлы:")
    for exe in sorted(OUTPUT_DIR.glob("*.exe")):
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"  • {exe.name} ({size_mb:.1f} MB)")
    print(f"\n💡 Для загрузки на сайт используй все файлы из папки: {OUTPUT_DIR.absolute()}")
else:
    print("\n❌ Ошибка при сборке.")

if errors:
    print("\n⚠️  Ошибки при сборке:")
    for err in errors[:5]:
        print(f"  • {err}")

print()
