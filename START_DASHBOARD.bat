@echo off
title E-Commerce Customer Intelligence Dashboard Server
cd /d "%~dp0"
echo ========================================================
echo   E-COMMERCE CUSTOMER INTELLIGENCE DASHBOARD SERVER
echo ========================================================
echo.
echo [1/2] Opening browser at http://localhost:8080 ...
start "" "http://localhost:8080"
echo.
echo [2/2] Starting Python Local HTTP Server on port 8080...
echo (Is window ko band mat karna jab tak dashboard dekh rahe ho)
echo.
python -m http.server 8080
if %ERRORLEVEL% NEQ 0 (
    echo Python command me error aaya. Direct file open kar rahe hain...
    start "" "dashboards\customer_intelligence_v4.html"
)
pause
