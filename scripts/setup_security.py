#!/usr/bin/env python
"""
Script de Configuração Automática do Sistema de Segurança Projeto Havoc
Configura monitoramento, alertas e testes automatizados
"""

import os
import json
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Cria diretórios necessários"""
    directories = [
        'logs',
        'reports',
        'scripts',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def create_config_files():
    """Cria arquivos de configuração"""
    
    # Configuração do monitor de segurança
    monitor_config = {
        "log_files": [
            "logs/security.log",
            "logs/django.log"
        ],
        "alert_thresholds": {
            "failed_logins_per_minute": 10,
            "requests_per_minute_per_ip": 100,
            "suspicious_requests_per_hour": 50,
            "error_rate_threshold": 0.1
        },
        "email_alerts": {
            "enabled": False,
            "smtp_server": "localhost",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_email": "security@projetohavoc.com",
            "to_emails": ["admin@projetohavoc.com"]
        },
        "webhook_alerts": {
            "enabled": False,
            "url": "",
            "headers": {}
        },
        "monitoring_interval": 30,
        "retention_days": 30
    }
    
    with open('security_monitor_config.json', 'w') as f:
        json.dump(monitor_config, f, indent=2)
    print("✅ Configuração do monitor criada: security_monitor_config.json")
    
    # Script de inicialização
    startup_script = """#!/bin/bash
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
"""
    
    with open('start_security.sh', 'w', encoding='utf-8') as f:
        f.write(startup_script)
    os.chmod('start_security.sh', 0o755)
    print("✅ Script de inicialização criado: start_security.sh")
    
    # Script de parada
    stop_script = """#!/bin/bash
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
"""
    
    with open('stop_security.sh', 'w', encoding='utf-8') as f:
        f.write(stop_script)
    os.chmod('stop_security.sh', 0o755)
    print("✅ Script de parada criado: stop_security.sh")

def create_systemd_service():
    """Cria serviço systemd para Linux"""
    if sys.platform != 'linux':
        print("⚠️  Serviço systemd disponível apenas no Linux")
        return
    
    current_dir = os.getcwd()
    service_content = f"""[Unit]
Description=Projeto Havoc Security Monitoring System
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory={current_dir}
ExecStart={current_dir}/start_security.sh
ExecStop={current_dir}/stop_security.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = 'projeto-havoc-security.service'
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Serviço systemd criado: {service_file}")
    print("   Para instalar:")
    print(f"   sudo cp {service_file} /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable projeto-havoc-security")
    print("   sudo systemctl start projeto-havoc-security")

def install_dependencies():
    """Instala dependências Python necessárias"""
    dependencies = [
        'flask',
        'requests'
    ]
    
    print("📦 Instalando dependências...")
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            print(f"✅ {dep} instalado")
        except subprocess.CalledProcessError:
            print(f"❌ Erro ao instalar {dep}")

def create_cron_jobs():
    """Cria jobs do cron para execução automática"""
    cron_content = """# Projeto Havoc Security System Cron Jobs

# Executar auditoria de segurança diariamente às 2:00
0 2 * * * cd /path/to/projeto-havoc && python scripts/security_test.py >> logs/cron_audit.log 2>&1

# Executar teste de penetração semanalmente aos domingos às 3:00
0 3 * * 0 cd /path/to/projeto-havoc && python scripts/penetration_test.py >> logs/cron_pentest.log 2>&1

# Limpeza de logs antigos mensalmente
0 4 1 * * find /path/to/projeto-havoc/logs -name "*.log" -mtime +30 -delete
0 4 1 * * find /path/to/projeto-havoc/reports -name "*.json" -mtime +90 -delete
"""
    
    with open('projeto_havoc_security_cron.txt', 'w', encoding='utf-8') as f:
        f.write(cron_content.replace('/path/to/projeto-havoc', os.getcwd()))

    print("✅ Jobs do cron criados: projeto_havoc_security_cron.txt")
    print("   Para instalar:")
    print("   crontab projeto_havoc_security_cron.txt")

def create_documentation():
    """Cria documentação do sistema"""
    docs = """# 🛡️ Sistema de Segurança Projeto Havoc

## 📋 Visão Geral

O Sistema de Segurança Projeto Havoc é uma solução completa de monitoramento e proteção que inclui:

- 🔍 **Monitor de Segurança**: Monitoramento em tempo real de logs e eventos
- 📊 **Dashboard Web**: Interface visual para acompanhar status de segurança
- 🧪 **Testes Automatizados**: Auditorias regulares de segurança
- 🔬 **Testes de Penetração**: Verificação de vulnerabilidades
- 🚨 **Sistema de Alertas**: Notificações por email e webhook

## 🚀 Início Rápido

### 1. Configuração Inicial
```bash
python scripts/setup_security.py
```

### 2. Iniciar Sistema
```bash
./start_security.sh
```

### 3. Acessar Dashboard
Abra http://localhost:5000 no navegador

### 4. Parar Sistema
```bash
./stop_security.sh
```

## 🔧 Configuração

### Monitor de Segurança
Edite `security_monitor_config.json` para configurar:
- Arquivos de log a monitorar
- Thresholds de alerta
- Configurações de email
- Webhooks

### Alertas por Email
```json
{
  "email_alerts": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "seu-email@gmail.com",
    "password": "sua-senha-app",
    "from_email": "security@projetohavoc.com",
    "to_emails": ["admin@projetohavoc.com"]
  }
}
```

### Webhooks
```json
{
  "webhook_alerts": {
    "enabled": true,
    "url": "https://hooks.slack.com/services/...",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

## 📊 Comandos Úteis

### Executar Auditoria Manual
```bash
python scripts/security_test.py
```

### Executar Teste de Penetração
```bash
python scripts/penetration_test.py
```

### Ver Estatísticas do Monitor
```bash
python scripts/security_monitor.py --stats
```

### Auditoria Agendada
```bash
python scripts/security_test.py --schedule --interval 12
```

## 📁 Estrutura de Arquivos

```
projeto-havoc/
├── scripts/
│   ├── security_monitor.py      # Monitor em tempo real
│   ├── security_dashboard.py    # Dashboard web
│   ├── security_test.py         # Testes de segurança
│   ├── penetration_test.py      # Testes de penetração
│   └── setup_security.py        # Configuração inicial
├── logs/
│   ├── security.log             # Logs de segurança
│   ├── django.log               # Logs do Django
│   └── security_monitor.db      # Banco de dados do monitor
├── reports/
│   ├── security_audit_*.json    # Relatórios de auditoria
│   └── penetration_test_*.json  # Relatórios de pentest
└── config/
    └── security_monitor_config.json
```

## 🚨 Tipos de Alertas

- **CRITICAL**: Vulnerabilidades críticas, ataques em andamento
- **HIGH**: Tentativas de invasão, falhas de segurança
- **MEDIUM**: Comportamento suspeito, thresholds excedidos
- **LOW**: Eventos informativos, métricas de performance

## 📈 Métricas Monitoradas

- Tentativas de login falhadas
- Requests suspeitos (SQL injection, XSS, etc.)
- Rate limiting
- Erros HTTP
- IPs suspeitos
- User agents maliciosos

## 🔧 Troubleshooting

### Dashboard não carrega
- Verifique se o Flask está instalado: `pip install flask`
- Verifique se a porta 5000 está livre
- Execute: `python scripts/security_dashboard.py --debug`

### Monitor não detecta eventos
- Verifique se os arquivos de log existem
- Verifique permissões de leitura
- Verifique configuração em `security_monitor_config.json`

### Alertas não são enviados
- Verifique configurações de email/webhook
- Teste conectividade SMTP
- Verifique logs de erro

## 📞 Suporte

Para suporte e dúvidas:
- Verifique logs em `logs/`
- Execute testes com `--debug`
- Consulte documentação do Django
"""
    
    with open('SECURITY_README.md', 'w', encoding='utf-8') as f:
        f.write(docs)
    
    print("✅ Documentação criada: SECURITY_README.md")

def main():
    """Função principal de configuração"""
    print("🛡️ Configurando Sistema de Segurança Projeto Havoc...")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('manage.py'):
        print("❌ Execute este script no diretório raiz do projeto Django")
        sys.exit(1)
    
    # Executar configurações
    create_directories()
    print()
    
    install_dependencies()
    print()
    
    create_config_files()
    print()
    
    create_systemd_service()
    print()
    
    create_cron_jobs()
    print()
    
    create_documentation()
    print()
    
    print("🎉 Configuração concluída com sucesso!")
    print()
    print("📋 Próximos passos:")
    print("1. Revisar configurações em security_monitor_config.json")
    print("2. Configurar alertas por email/webhook se necessário")
    print("3. Executar: ./start_security.sh")
    print("4. Acessar dashboard: http://localhost:5000")
    print()
    print("📖 Consulte SECURITY_README.md para documentação completa")

if __name__ == '__main__':
    main()
