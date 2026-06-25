@echo off
cd /d "%~dp0.."
start "" pythonw -m tools.s7comm_gui.rules_app
exit
