@echo off
echo Compilando ADB Toolbox...

set PY=python
where py >nul 2>nul && set PY=py -3

%PY% -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "ADB_Toolbox" ^
  --collect-all customtkinter ^
  --collect-all PIL ^
  --exclude-module numpy ^
  adb_toolbox.py

echo.
echo Listo. El ejecutable esta en:  dist\ADB_Toolbox.exe
pause
