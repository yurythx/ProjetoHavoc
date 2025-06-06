@echo off
echo 🔴 INICIANDO REDIS SERVER - ProjetoHavoc
echo ========================================

REM Verificar se Redis está instalado
where redis-server >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Redis não está instalado!
    echo.
    echo 💡 OPÇÕES PARA INSTALAR REDIS:
    echo.
    echo 1. DOCKER (Recomendado):
    echo    docker run -d -p 6379:6379 --name redis-havoc redis:alpine
    echo.
    echo 2. WINDOWS NATIVO:
    echo    - Baixe: https://github.com/microsoftarchive/redis/releases
    echo    - Instale e adicione ao PATH
    echo.
    echo 3. WSL (Windows Subsystem for Linux):
    echo    sudo apt update && sudo apt install redis-server
    echo    redis-server
    echo.
    pause
    exit /b 1
)

echo ✅ Redis encontrado!
echo 🚀 Iniciando Redis Server...
echo ⚡ Pressione Ctrl+C para parar
echo.

redis-server

pause
