@echo off
:loop
python psunote/noteapp.py
timeout /t 3 > nul
goto loop
