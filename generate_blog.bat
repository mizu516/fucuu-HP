@echo off
cls
echo ===================================
echo   FUCUU AI BLOG GENERATOR
echo ===================================
echo.

set /p keyword="Enter keyword (e.g. Onkatsu Aroma): "

echo.
echo [1/2] Generating quality article for "%keyword%"...
cd /d %~dp0.agents\blog_tool
python blog_generator.py "%keyword%"

echo.
echo [2/2] Process finished!
echo.
pause
