@echo off
echo ========================================
echo   Fake Food Detection - GitHub Push
echo ========================================
echo.

REM Initialize git if not already done
if not exist .git (
    echo Initializing Git repository...
    git init
    echo.
)

REM Add all files
echo Adding all files...
git add .
echo.

REM Commit changes
echo Committing changes...
git commit -m "Fake Food Detection System - Complete Implementation"
echo.

REM Add remote (replace with your GitHub URL)
echo Adding remote repository...
git remote remove origin 2>nul
git remote add origin https://github.com/Rsingh230105/Project_Major_Food.git
echo.

REM Push to GitHub
echo Pushing to GitHub...
git branch -M main
git push -u origin main --force
echo.

echo ========================================
echo   Push Complete!
echo ========================================
pause
