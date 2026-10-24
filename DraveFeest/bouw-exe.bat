@echo off
title DraveFeest - EXE bouwen
cd /d "%~dp0"
set "VPY=%~dp0.venv\Scripts\python.exe"
if not exist "%VPY%" (
  echo Nieuwe .venv maken met Python 3.13...
  py -3.13 -m venv .venv || goto mislukt
)
"%VPY%" -m pip install -q --upgrade pip
"%VPY%" -m pip install -q -r requirements.txt pyinstaller pillow || goto mislukt
"%VPY%" make_icon.py
"%VPY%" -m PyInstaller --noconfirm --clean --windowed --onedir --name DraveFeest --icon assets\icon.ico --add-data "assets;assets" --hidden-import dorp --hidden-import sintmaarten --hidden-import sinterklaas --hidden-import kerst --hidden-import nieuwjaar --hidden-import pasen --hidden-import koningsdag --hidden-import valentijn --hidden-import carnaval --hidden-import halloween --hidden-import muziek --hidden-import basis --hidden-import drave_update --exclude-module tkinter --exclude-module PIL --exclude-module matplotlib main.py
if errorlevel 1 goto mislukt
if not exist "dist\DraveFeest\DraveFeest.exe" goto mislukt
xcopy /e /i /y assets "dist\DraveFeest\assets" >nul
if exist DraveFeest-Snelgids.pdf copy /y DraveFeest-Snelgids.pdf "dist\DraveFeest\" >nul
echo.
echo KLAAR: dist\DraveFeest\DraveFeest.exe
exit /b 0
:mislukt
echo MISLUKT - kijk hierboven voor de fout.
exit /b 1
