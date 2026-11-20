@echo off
title Push to GitHub - E-Commerce Customer Analysis
cd /d "%~dp0"
echo ========================================================
echo   PUSHING TO GITHUB: harshwardhanpal718-png/E-commerce-Customer-Analysis
echo ========================================================
echo.
echo Running: git push -u origin main ...
echo.
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo   SUCCESS! Sabhi files GitHub par upload ho gayi hain!
    echo ========================================================
) else (
    echo ========================================================
    echo   Push complete nahi hua. Check authentication above.
    echo ========================================================
)
pause
