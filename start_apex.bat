@echo off
REM APEX Startup Script - Starts all services
REM Context: 32K tokens (optimized for RTX 5090 32GB)

echo ============================================
echo APEX - Autonomous Production Engineering Executor
echo ============================================
echo.
echo Configuration:
echo   - Model: qwen2.5-coder-32b.gguf
echo   - Context: 32,768 tokens
echo   - GPU Layers: 40 (full offload)
echo   - VRAM Budget: ~24GB / 32GB
echo.

REM Check if llama-server is running
tasklist /FI "IMAGENAME eq llama-server.exe" | find "llama-server.exe" >nul
if %errorlevel% equ 0 (
    echo [OK] llama-server already running
) else (
    echo [START] Starting llama-server on GPU...
    start "" "D:\Users\CASE\Desktop\llama.cpp\cuda-bin\full\llama-server.exe" -m "D:\Users\CASE\projects\inference.saas\stage1\data\models\qwen2.5-coder-32b.gguf" --host 127.0.0.1 --port 8080 --ctx-size 32768 -ngl 40
    timeout /t 20 /nobreak >nul
)

REM Check Stage 1
curl -s http://127.0.0.1:3000/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Stage 1 (Inference Proxy) already running
) else (
    echo [START] Starting Stage 1 on port 3000...
    cd /d "%~dp0"
    start /B python -m stage1.main
    timeout /t 3 /nobreak >nul
)

REM Check Stage 2
curl -s http://127.0.0.1:3001/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Stage 2 (Intelligence API) already running
) else (
    echo [START] Starting Stage 2 on port 3001...
    cd /d "%~dp0"
    start /B python -m stage2.main
    timeout /t 8 /nobreak >nul
)

echo.
echo ============================================
echo Services Status:
echo ============================================
curl -s http://127.0.0.1:8080/health
echo.
curl -s http://127.0.0.1:3000/v1/health
echo.
curl -s http://127.0.0.1:3001/health
echo.
echo ============================================
echo.
echo APEX is ready!
echo.
echo In VSCode:
echo   1. Press Ctrl+Shift+P
echo   2. Type: Developer: Reload Window
echo   3. Use Ctrl+Shift+A for completions
echo.
echo Press any key to exit...
pause >nul
