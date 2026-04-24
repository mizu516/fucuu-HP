@echo off
cls
echo ===================================
echo   FUCUU DEPLOY SYSTEM
echo ===================================
echo.

echo [1/3] Preparing files...
git add .

echo [2/3] Recording changes...
git commit -m "Auto-update blog and SEO"

echo [3/3] Uploading to GitHub...
git push origin main

echo.
echo ===================================
echo   SUCCESS! 
echo   Your site will be updated in a few minutes.
echo ===================================
pause
