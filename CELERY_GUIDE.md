# 🚀 GUIA COMPLETO DO CELERY - ProjetoHavoc

## 📚 O QUE É CELERY?

**Celery** é um sistema de **filas de tarefas distribuídas** que permite executar tarefas em **background** (segundo plano) de forma **assíncrona**.

### 🔄 Como Funciona:

```
[Web App] → [Envia tarefa] → [Redis Broker] → [Worker] → [Executa tarefa] → [Resultado]
    ↓                                                                           ↑
[Resposta imediata]                                                    [Resultado salvo]
```

### 🎯 Benefícios:

- ✅ **Interface rápida**: Usuário não espera email ser enviado
- ✅ **Confiabilidade**: Retry automático em caso de falha
- ✅ **Escalabilidade**: Múltiplos workers podem processar tarefas
- ✅ **Monitoramento**: Acompanhar status das tarefas

## 🛠️ INSTALAÇÃO E CONFIGURAÇÃO

### 1. Dependências Instaladas:
```bash
pip install celery redis django-celery-results
```

### 2. Arquivos Criados:
- `core/celery.py` - Configuração principal do Celery
- `apps/accounts/tasks.py` - Tarefas assíncronas
- `core/settings.py` - Configurações Django + Celery

### 3. Configurações Adicionadas:
- Redis como Broker (fila de tarefas)
- Django DB como Result Backend (resultados)
- Retry automático para falhas
- Timeout e limites de tempo

## 🚀 COMO USAR

### Passo 1: Iniciar Redis
```bash
# Opção 1: Docker (Recomendado)
docker run -d -p 6379:6379 --name redis-havoc redis:alpine

# Opção 2: Windows nativo
redis-server

# Opção 3: Script automático
start_redis.bat
```

### Passo 2: Iniciar Worker Celery
```bash
# Terminal separado
celery -A core worker --loglevel=info --pool=solo

# Ou usar script automático
start_celery_worker.bat
```

### Passo 3: Iniciar Django
```bash
python manage.py runserver
```

## 📧 TAREFAS IMPLEMENTADAS

### 1. Email de Ativação
```python
# Antes (síncrono - lento)
send_email_with_config(subject, message, [email])

# Agora (assíncrono - rápido)
task = send_activation_email_async.delay(user_id, codigo)
```

### 2. Email de Recuperação de Senha
```python
task = send_password_reset_email_async.delay(user_id, token)
```

### 3. Email em Massa
```python
task = send_bulk_email_async.delay(subject, message, recipient_list)
```

### 4. Limpeza de Usuários Expirados
```python
task = cleanup_expired_users.delay()
```

### 5. Teste do Sistema
```python
task = test_celery_task.delay()
```

## 🔍 MONITORAMENTO

### Verificar Status de Tarefa:
```python
task = send_activation_email_async.delay(user_id, codigo)
print(f"Task ID: {task.id}")

# Verificar resultado
result = task.get(timeout=30)
print(f"Sucesso: {result['success']}")
```

### Inspecionar Workers:
```python
from celery import current_app
inspect = current_app.control.inspect()

# Workers ativos
active = inspect.active()
print(f"Workers: {list(active.keys())}")

# Estatísticas
stats = inspect.stats()
```

## 🧪 TESTES

### Teste Completo do Sistema:
```bash
python test_celery_system.py
```

### Testes Individuais:
```python
# Teste básico
from apps.accounts.tasks import test_celery_task
task = test_celery_task.delay()
result = task.get()

# Teste de email
from apps.accounts.tasks import send_activation_email_async
task = send_activation_email_async.delay(user_id, "123456")
result = task.get()
```

## ⚡ PERFORMANCE

### Antes (Síncrono):
- ❌ Registro: 4-5 segundos (usuário espera)
- ❌ Interface trava durante envio
- ❌ Falhas bloqueiam o processo

### Depois (Assíncrono):
- ✅ Registro: < 500ms (resposta imediata)
- ✅ Interface sempre responsiva
- ✅ Falhas não afetam usuário

## 🔧 CONFIGURAÇÕES AVANÇADAS

### Filas Específicas:
```python
# settings.py
CELERY_TASK_ROUTES = {
    'apps.accounts.tasks.send_activation_email_async': {'queue': 'email'},
    'apps.accounts.tasks.cleanup_expired_users': {'queue': 'maintenance'},
}

# Iniciar worker para fila específica
celery -A core worker -Q email --loglevel=info
```

### Retry Personalizado:
```python
@shared_task(bind=True, max_retries=5, default_retry_delay=120)
def my_task(self):
    try:
        # Código da tarefa
        pass
    except Exception as e:
        # Retry com delay exponencial
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### Agendamento de Tarefas:
```python
# Instalar celery-beat
pip install django-celery-beat

# settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-users': {
        'task': 'apps.accounts.tasks.cleanup_expired_users',
        'schedule': crontab(hour=2, minute=0),  # Todo dia às 2h
    },
}
```

## 🚨 TROUBLESHOOTING

### Redis não conecta:
```bash
# Verificar se Redis está rodando
redis-cli ping

# Deve retornar: PONG
```

### Worker não inicia:
```bash
# Verificar configurações
python -c "from core.celery import app; print(app.conf.broker_url)"

# Verificar tasks registradas
celery -A core inspect registered
```

### Tarefas não executam:
```bash
# Verificar workers ativos
celery -A core inspect active

# Verificar filas
celery -A core inspect reserved
```

### Logs detalhados:
```bash
# Worker com debug
celery -A core worker --loglevel=debug

# Logs específicos
import logging
logging.getLogger('celery').setLevel(logging.DEBUG)
```

## 📊 MONITORAMENTO EM PRODUÇÃO

### Flower (Interface Web):
```bash
pip install flower
celery -A core flower
# Acesse: http://localhost:5555
```

### Métricas Importantes:
- Taxa de sucesso das tarefas
- Tempo médio de execução
- Filas com backlog
- Workers ativos/inativos

## 🎯 PRÓXIMOS PASSOS

1. **✅ Implementado**: Email assíncrono básico
2. **🔄 Próximo**: Agendamento de tarefas (Celery Beat)
3. **📊 Futuro**: Monitoramento com Flower
4. **🚀 Produção**: Redis Cluster + múltiplos workers

## 💡 DICAS IMPORTANTES

- **Desenvolvimento**: Use `CELERY_TASK_ALWAYS_EAGER=True` para debug
- **Produção**: Use Redis/RabbitMQ como broker
- **Monitoramento**: Implemente logs estruturados
- **Backup**: Redis persistence para não perder tarefas
- **Segurança**: Autenticação no Redis em produção

---

🎉 **Sistema Celery implementado com sucesso!**
⚡ **Emails agora são enviados de forma assíncrona e rápida!**
