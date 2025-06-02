#!/bin/bash
# Script de inicialização do sistema de segurança Projeto Havoc

echo "🚀 Iniciando Sistema de Segurança Projeto Havoc..."

# Ativar ambiente virtual se existir
if [ -d "env" ]; then
    source env/bin/activate
    echo "✅ Ambiente virtual ativado"
fi

# Instalar dependências se necessário
pip install flask requests > /dev/null 2>&1

# Iniciar monitor de segurança em background
echo "🔍 Iniciando monitor de segurança..."
python scripts/security_monitor.py &
MONITOR_PID=$!
echo "Monitor PID: $MONITOR_PID"

# Iniciar dashboard em background
echo "📊 Iniciando dashboard de segurança..."
python scripts/security_dashboard.py --host 0.0.0.0 &
DASHBOARD_PID=$!
echo "Dashboard PID: $DASHBOARD_PID"

# Iniciar auditoria agendada
echo "🕐 Iniciando auditoria agendada..."
python scripts/security_test.py --schedule --interval 24 &
AUDIT_PID=$!
echo "Auditoria PID: $AUDIT_PID"

echo ""
echo "🎉 Sistema de Segurança Projeto Havoc iniciado com sucesso!"
echo ""
echo "📊 Dashboard: http://localhost:5000"
echo "🔍 Monitor: Executando em background"
echo "🕐 Auditoria: A cada 24 horas"
echo ""
echo "Para parar o sistema, execute: ./stop_security.sh"

# Salvar PIDs para poder parar depois
echo "$MONITOR_PID" > .security_monitor.pid
echo "$DASHBOARD_PID" > .security_dashboard.pid
echo "$AUDIT_PID" > .security_audit.pid

# Manter script rodando
wait
