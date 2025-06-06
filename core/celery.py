#!/usr/bin/env python
"""
Configuração do Celery para ProjetoHavoc

O Celery é um sistema de filas de tarefas distribuídas que permite
executar tarefas em background de forma assíncrona.

Como funciona:
1. Web App envia tarefa para o Broker (Redis)
2. Worker pega a tarefa do Broker
3. Worker executa a tarefa (ex: enviar email)
4. Resultado é armazenado no Result Backend
5. Web App pode verificar o status/resultado
"""
import os
from celery import Celery
from django.conf import settings

# Definir configurações padrão do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Criar instância do Celery
app = Celery('projetohavoc')

# Configurar Celery usando as configurações do Django
# namespace='CELERY' significa que todas as configurações do Celery
# no settings.py devem começar com 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobrir automaticamente tarefas em todos os apps Django
# Procura por arquivos tasks.py em cada app
app.autodiscover_tasks()

# Configurações específicas do Celery
app.conf.update(
    # Configurações de retry
    task_acks_late=True,  # Confirma tarefa apenas após conclusão
    worker_prefetch_multiplier=1,  # Worker pega uma tarefa por vez
    
    # Configurações de tempo
    task_soft_time_limit=300,  # 5 minutos limite suave
    task_time_limit=600,       # 10 minutos limite rígido
    
    # Configurações de resultado
    result_expires=3600,  # Resultados expiram em 1 hora
    
    # Configurações de serialização
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
)

@app.task(bind=True)
def debug_task(self):
    """Tarefa de debug para testar se o Celery está funcionando"""
    print(f'Request: {self.request!r}')
    return 'Celery está funcionando!'

# Configuração para desenvolvimento
if settings.DEBUG:
    app.conf.update(
        # Em desenvolvimento, mostrar mais logs
        worker_log_level='INFO',
        worker_hijack_root_logger=False,
    )
