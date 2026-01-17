@echo off
title Yoga AI Robust Build System
echo ======================================================
echo 1. Cleaning old build files...
if exist dist rd /s /q dist
if exist build rd /s /q build
if exist *.spec del /f /q *.spec

echo 2. Starting Robust Packaging (ONEDIR mode)...
echo ======================================================


pyinstaller --noconsole --onedir ^
 --name "YogaAI_Du" ^
 --add-data "assets;assets" ^
 --collect-all mediapipe ^
 --hidden-import pythoncom ^
 --hidden-import pyttsx3.drivers ^
 --hidden-import pyttsx3.drivers.sapi5 ^
 main_gui.py

echo ======================================================
echo 3. Success! 
echo Please find 'YogaAI_Du' FOLDER in 'dist'.
echo ======================================================
pause