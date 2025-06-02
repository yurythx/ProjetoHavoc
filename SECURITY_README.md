# 🛡️ Sistema de Segurança Projeto Havoc

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
