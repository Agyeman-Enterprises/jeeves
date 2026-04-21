@echo off
set NODE_ENV=development
cd /d C:\DEV\JARVIS\frontend
C:\nvm4w\nodejs\node.exe node_modules\@playwright\test\cli.js test --config=e2e/playwright.config.ts --project=chromium --reporter=list > C:\DEV\JARVIS\frontend\e2e-out.txt 2>&1
echo EXIT_CODE=%ERRORLEVEL% >> C:\DEV\JARVIS\frontend\e2e-out.txt
