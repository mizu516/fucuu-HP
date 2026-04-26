@echo off
cls
echo ===================================
echo   FUCUU AI BLOG AUTO-PILOT
echo ===================================
echo.
echo AI is choosing a topic and generating a rich article...
echo.

cd /d %~dp0.agents\blog_tool
python blog_generator.py --auto

echo.
echo ===================================
echo   AUTO-PILOT FINISHED!
echo ===================================
rem 'pause' is removed to allow automatic daily updates via Task Scheduler.
