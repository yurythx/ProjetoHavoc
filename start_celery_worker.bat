@echo off
echo 🚀 INICIANDO CELERY WORKER - ProjetoHavoc
echo ==========================================

REM Ativar ambiente virtual
call env\Scripts\activate

REM Verificar se Redis está rodando
echo 🔍 Verificando Redis...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Redis não está rodando!
    echo 💡 Inicie o Redis primeiro:
    echo    - Windows: Baixe e instale Redis
    echo    - Docker: docker run -d -p 6379:6379 redis:alpine
    pause
    exit /b 1
)
echo ✅ Redis está rodando!

REM Iniciar worker Celery
echo 🏃 Iniciando Celery Worker...
echo ⚡ Pressione Ctrl+C para parar
echo.

celery -A core worker --loglevel=info --pool=solo

pause
