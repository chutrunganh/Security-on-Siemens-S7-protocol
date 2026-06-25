@echo off
REM Mo CA HAI ung dung: Attack Tool + Rules Tool (2 cua so rieng)
cd /d "%~dp0.."
pythonw tools\s7comm_gui\launch_all.py
if errorlevel 1 (
  echo Loi khoi dong GUI. Xem: tools\s7comm_gui\launch_errors.log
  pause
)
exit
