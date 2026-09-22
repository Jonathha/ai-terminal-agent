@echo off
title AI Terminal Agent
cd /d "C:\Users\jogon\.gemini\antigravity\scratch\ai_terminal"
python main.py
if errorlevel 1 (
    echo.
    echo Ocorreu um erro ao rodar o AI Terminal. Pressione qualquer tecla para fechar.
    pause >nul
)
