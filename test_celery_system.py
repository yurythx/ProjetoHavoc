#!/usr/bin/env python
"""
Teste completo do sistema Celery

Este script testa todas as funcionalidades do Celery implementadas:
1. Conexão com Redis
2. Tarefas básicas
3. Tarefas de email
4. Monitoramento de resultados
"""
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.tasks import (
    test_celery_task, 
    send_activation_email_async,
    send_bulk_email_async,
    cleanup_expired_users
)
from django.contrib.auth import get_user_model
from celery import current_app
import redis

User = get_user_model()

def test_redis_connection():
    """Testa conexão com Redis"""
    print("🔗 TESTANDO CONEXÃO COM REDIS")
    print("-" * 40)
    
    try:
        # Tentar conectar ao Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis conectado com sucesso!")
        
        # Informações do Redis
        info = r.info()
        print(f"📊 Versão Redis: {info.get('redis_version', 'N/A')}")
        print(f"💾 Memória usada: {info.get('used_memory_human', 'N/A')}")
        print(f"🔌 Conexões: {info.get('connected_clients', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Redis: {e}")
        print("💡 Certifique-se de que o Redis está rodando:")
        print("   - Windows: Baixe e instale Redis")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
        return False

def test_celery_basic():
    """Testa tarefa básica do Celery"""
    print("\n🧪 TESTANDO TAREFA BÁSICA DO CELERY")
    print("-" * 40)
    
    try:
        # Enviar tarefa para fila
        task = test_celery_task.delay()
        print(f"📤 Tarefa enviada - ID: {task.id}")
        
        # Aguardar resultado (máximo 10 segundos)
        print("⏳ Aguardando resultado...")
        result = task.get(timeout=10)
        
        print(f"✅ Resultado: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Erro na tarefa básica: {e}")
        return False

def test_email_task():
    """Testa tarefa de email"""
    print("\n📧 TESTANDO TAREFA DE EMAIL")
    print("-" * 40)
    
    try:
        # Buscar um usuário para teste
        user = User.objects.first()
        if not user:
            print("⚠️ Nenhum usuário encontrado para teste")
            return False
        
        print(f"👤 Testando com usuário: {user.username} ({user.email})")
        
        # Enviar email de ativação
        task = send_activation_email_async.delay(user.id, "123456")
        print(f"📤 Email enviado para fila - Task ID: {task.id}")
        
        # Aguardar resultado
        print("⏳ Aguardando processamento do email...")
        result = task.get(timeout=30)  # Email pode demorar mais
        
        if result.get('success'):
            print(f"✅ Email processado: {result.get('message')}")
        else:
            print(f"❌ Falha no email: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Erro na tarefa de email: {e}")
        return False

def test_bulk_email():
    """Testa email em massa"""
    print("\n📬 TESTANDO EMAIL EM MASSA")
    print("-" * 40)
    
    try:
        # Lista de emails de teste
        recipients = ['teste1@exemplo.com', 'teste2@exemplo.com']
        
        task = send_bulk_email_async.delay(
            subject="Teste Celery - Email em Massa",
            message="Este é um teste do sistema Celery para emails em massa.",
            recipient_list=recipients
        )
        
        print(f"📤 Email em massa enviado - Task ID: {task.id}")
        
        result = task.get(timeout=30)
        
        if result.get('success'):
            print(f"✅ Email em massa processado: {result.get('message')}")
        else:
            print(f"❌ Falha no email em massa: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Erro no email em massa: {e}")
        return False

def test_cleanup_task():
    """Testa tarefa de limpeza"""
    print("\n🧹 TESTANDO TAREFA DE LIMPEZA")
    print("-" * 40)
    
    try:
        task = cleanup_expired_users.delay()
        print(f"📤 Limpeza iniciada - Task ID: {task.id}")
        
        result = task.get(timeout=15)
        
        if result.get('success'):
            print(f"✅ Limpeza concluída: {result.get('message')}")
        else:
            print(f"❌ Falha na limpeza: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")
        return False

def test_celery_inspect():
    """Testa inspeção do Celery"""
    print("\n🔍 INSPECIONANDO WORKERS CELERY")
    print("-" * 40)
    
    try:
        inspect = current_app.control.inspect()
        
        # Workers ativos
        active = inspect.active()
        if active:
            print(f"👷 Workers ativos: {list(active.keys())}")
            for worker, tasks in active.items():
                print(f"   {worker}: {len(tasks)} tarefas ativas")
        else:
            print("⚠️ Nenhum worker ativo encontrado")
        
        # Estatísticas
        stats = inspect.stats()
        if stats:
            print(f"📊 Estatísticas disponíveis para {len(stats)} workers")
        
        # Tarefas registradas
        registered = inspect.registered()
        if registered:
            for worker, tasks in registered.items():
                print(f"📋 {worker}: {len(tasks)} tarefas registradas")
        
        return bool(active)
        
    except Exception as e:
        print(f"❌ Erro na inspeção: {e}")
        return False

def show_celery_info():
    """Mostra informações do Celery"""
    print("\n📋 INFORMAÇÕES DO CELERY")
    print("-" * 40)
    
    print(f"🏷️ App Name: {current_app.main}")
    print(f"🔗 Broker URL: {current_app.conf.broker_url}")
    print(f"💾 Result Backend: {current_app.conf.result_backend}")
    print(f"🕒 Timezone: {current_app.conf.timezone}")
    print(f"📦 Task Serializer: {current_app.conf.task_serializer}")

def main():
    """Função principal do teste"""
    print("🚀 TESTE COMPLETO DO SISTEMA CELERY")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Celery Basic Task", test_celery_basic),
        ("Email Task", test_email_task),
        ("Bulk Email", test_bulk_email),
        ("Cleanup Task", test_cleanup_task),
        ("Worker Inspection", test_celery_inspect),
    ]
    
    results = {}
    
    # Mostrar informações do Celery
    show_celery_info()
    
    # Executar testes
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Erro crítico em {test_name}: {e}")
            results[test_name] = False
    
    # Resumo final
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:<20} | {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"📈 Resultado: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Celery está funcionando perfeitamente!")
    elif passed >= total * 0.7:
        print("⚠️ Maioria dos testes passou. Verifique os erros acima.")
    else:
        print("❌ Muitos testes falharam. Verifique a configuração do Celery.")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Certifique-se de que Redis está rodando")
    print("2. Inicie o worker Celery: celery -A core worker --loglevel=info")
    print("3. Execute este teste novamente")
    print("4. Teste o registro de usuários na interface web")

if __name__ == "__main__":
    main()
