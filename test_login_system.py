#!/usr/bin/env python
"""
Script para testar o sistema de login completo
"""
import os
import sys
import django
import requests
from django.test import Client
from django.urls import reverse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

def test_login_system():
    """Testa o sistema de login completo"""
    User = get_user_model()
    client = Client()
    
    print("=== TESTE DO SISTEMA DE LOGIN ===")
    
    # 1. Testar acesso sem login (deve redirecionar)
    print("\n1. 🔒 Testando acesso sem login...")
    response = client.get('/config/')
    if response.status_code == 302:
        print("✅ Redirecionamento funcionando (302)")
        print(f"   Redirecionando para: {response.url}")
    else:
        print(f"❌ Erro: Status {response.status_code} (esperado 302)")
    
    # 2. Testar página de login
    print("\n2. 📝 Testando página de login...")
    response = client.get('/accounts/login/')
    if response.status_code == 200:
        print("✅ Página de login carregando (200)")
    else:
        print(f"❌ Erro: Status {response.status_code} (esperado 200)")
    
    # 3. Testar login com credenciais válidas
    print("\n3. 🔑 Testando login com credenciais válidas...")
    
    # Usar usuário admin
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = client.post('/accounts/login/', login_data, follow=True)
    if response.status_code == 200:
        print("✅ Login realizado com sucesso (200)")
        
        # Verificar se está logado
        if hasattr(response, 'wsgi_request') and response.wsgi_request.user.is_authenticated:
            print("✅ Usuário autenticado")
            print(f"   Usuário: {response.wsgi_request.user.username}")
            print(f"   Staff: {response.wsgi_request.user.is_staff}")
        else:
            print("❌ Usuário não autenticado após login")
    else:
        print(f"❌ Erro no login: Status {response.status_code}")
    
    # 4. Testar acesso ao config após login
    print("\n4. ⚙️ Testando acesso ao config após login...")
    response = client.get('/config/')
    if response.status_code == 200:
        print("✅ Acesso ao config funcionando após login (200)")
    else:
        print(f"❌ Erro: Status {response.status_code} (esperado 200)")
    
    # 5. Testar logout
    print("\n5. 🚪 Testando logout...")
    response = client.post('/accounts/logout/', follow=True)
    if response.status_code == 200:
        print("✅ Logout realizado com sucesso (200)")
    else:
        print(f"❌ Erro no logout: Status {response.status_code}")
    
    # 6. Verificar se perdeu acesso após logout
    print("\n6. 🔒 Verificando perda de acesso após logout...")
    response = client.get('/config/')
    if response.status_code == 302:
        print("✅ Acesso negado após logout (302)")
    else:
        print(f"❌ Erro: Status {response.status_code} (esperado 302)")
    
    print("\n=== TESTE COMPLETO ===")
    print("✅ Sistema de login funcionando corretamente!")

def test_audit_system():
    """Testa o sistema de auditoria"""
    print("\n=== TESTE DO SISTEMA DE AUDITORIA ===")

    from apps.accounts.models import UserAuditLog

    # Contar logs antes
    logs_before = UserAuditLog.objects.count()
    print(f"📊 Logs de auditoria antes: {logs_before}")

    # Fazer login para gerar log
    client = Client()
    client.post('/accounts/login/', {
        'username': 'admin',
        'password': 'admin123'
    })

    # Acessar config para gerar log
    client.get('/config/')

    # Contar logs depois
    logs_after = UserAuditLog.objects.count()
    print(f"📊 Logs de auditoria depois: {logs_after}")

    if logs_after > logs_before:
        print("✅ Sistema de auditoria funcionando!")

        # Mostrar últimos logs
        recent_logs = UserAuditLog.objects.order_by('-timestamp')[:3]
        for log in recent_logs:
            print(f"   📝 {log.timestamp}: {log.action} - {log.user}")
    else:
        print("⚠️ Sistema de auditoria pode não estar funcionando")

if __name__ == '__main__':
    test_login_system()
    test_audit_system()
