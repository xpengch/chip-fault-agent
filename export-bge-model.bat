@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Export BGE Model for Offline Deployment
echo ==========================================
echo.

set MODEL_DIR=offline-package\bge-model
set MODEL_NAME=BAAI/bge-large-zh-v1.5

echo [1/3] Creating model directory...
if exist %MODEL_DIR% rmdir /s /q %MODEL_DIR%
mkdir %MODEL_DIR%
echo [OK] Directory created
echo.

echo [2/3] Downloading BGE model...
echo     This is a large download (~1.3GB)
echo     Please be patient...
echo.

python -c "from sentence_transformers import SentenceTransformer; import os; os.environ['TRANSFORMERS_CACHE']='%MODEL_DIR%'; model=SentenceTransformer('%MODEL_NAME%'); print('Model downloaded successfully')"

echo.
echo [3/3] Verifying model files...
dir %MODEL_DIR% /s | find "File(s)"
echo.

echo ==========================================
echo   BGE Model Export Complete!
echo ==========================================
echo.
echo Model location: %MODEL_DIR%\
echo Model size:
du -sh %MODEL_DIR% 2>/dev/null || dir %MODEL_DIR% /s
echo.
pause
