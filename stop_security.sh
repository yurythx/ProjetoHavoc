#!/bin/bash
# Script para parar o sistema de segurança Projeto Havoc

echo "🛑 Parando Sistema de Segurança Projeto Havoc..."

# Parar processos usando PIDs salvos
if [ -f ".security_monitor.pid" ]; then
    PID=$(cat .security_monitor.pid)
    kill $PID 2>/dev/null && echo "✅ Monitor de segurança parado"
    rm .security_monitor.pid
fi

if [ -f ".security_dashboard.pid" ]; then
    PID=$(cat .security_dashboard.pid)
    kill $PID 2>/dev/null && echo "✅ Dashboard parado"
    rm .security_dashboard.pid
fi

if [ -f ".security_audit.pid" ]; then
    PID=$(cat .security_audit.pid)
    kill $PID 2>/dev/null && echo "✅ Auditoria agendada parada"
    rm .security_audit.pid
fi

# Parar processos por nome (fallback)
pkill -f "security_monitor.py" 2>/dev/null
pkill -f "security_dashboard.py" 2>/dev/null
pkill -f "security_test.py.*schedule" 2>/dev/null

echo "🎉 Sistema de Segurança Projeto Havoc parado!"
