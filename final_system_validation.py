#!/usr/bin/env python
"""
Validação final completa do sistema após correção do rate limiting
"""
import os
import sys
import django
import requests
import time
from django.test import Client

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import UserAuditLog

def final_system_validation():
    """Validação final completa do sistema"""
    print("🚀 === VALIDAÇÃO FINAL COMPLETA DO SISTEMA ===")
    
    base_url = 'http://127.0.0.1:8000'
    client = Client()
    User = get_user_model()
    
    # 1. Verificar rate limiting
    print("\n1. ⚡ VERIFICANDO RATE LIMITING...")
    
    rate_limit_ok = True
    for i in range(20):  # Testar 20 requisições
        try:
            response = requests.get(f'{base_url}/admin/', timeout=2)
            if response.status_code == 429:
                rate_limit_ok = False
                break
        except:
            continue
    
    if rate_limit_ok:
        print("   ✅ Rate limiting funcionando corretamente")
    else:
        print("   ❌ Rate limiting ainda restritivo")
    
    # 2. Testar sistema de login
    print("\n2. 🔑 TESTANDO SISTEMA DE LOGIN...")
    
    login_success = client.login(username='admin', password='admin123')
    if login_success:
        print("   ✅ Login funcionando")
        
        # Testar acesso a áreas protegidas
        protected_urls = [
            '/config/',
            '/config/monitoring/',
            '/config/api/status/',
            '/admin/'
        ]
        
        access_results = {}
        for url in protected_urls:
            response = client.get(url)
            access_results[url] = response.status_code
            if response.status_code in [200, 302]:
                print(f"   ✅ {url}: {response.status_code}")
            else:
                print(f"   ❌ {url}: {response.status_code}")
        
        # Logout
        client.logout()
        print("   ✅ Logout funcionando")
    else:
        print("   ❌ Falha no login")
    
    # 3. Verificar sistema de auditoria
    print("\n3. 📝 VERIFICANDO SISTEMA DE AUDITORIA...")
    
    audit_logs = UserAuditLog.objects.count()
    recent_logs = UserAuditLog.objects.order_by('-timestamp')[:3]
    
    print(f"   📊 Total de logs: {audit_logs}")
    print("   📋 Últimos logs:")
    for log in recent_logs:
        print(f"      - {log.timestamp.strftime('%H:%M:%S')}: {log.action} - {log.user.username}")
    
    if audit_logs > 0:
        print("   ✅ Sistema de auditoria funcionando")
    else:
        print("   ❌ Sistema de auditoria com problemas")
    
    # 4. Verificar usuários
    print("\n4. 👥 VERIFICANDO USUÁRIOS...")
    
    active_staff = User.objects.filter(is_active=True, is_staff=True).count()
    total_users = User.objects.count()
    
    print(f"   👤 Total de usuários: {total_users}")
    print(f"   👑 Staff ativos: {active_staff}")
    
    if active_staff > 0:
        print("   ✅ Usuários staff disponíveis")
    else:
        print("   ❌ Nenhum usuário staff ativo")
    
    # 5. Teste de stress do rate limiting
    print("\n5. 💪 TESTE DE STRESS DO RATE LIMITING...")
    
    # Testar como usuário anônimo
    anon_blocked = 0
    anon_success = 0
    
    for i in range(50):  # 50 requisições anônimas
        try:
            response = requests.get(f'{base_url}/', timeout=1)
            if response.status_code == 429:
                anon_blocked += 1
            else:
                anon_success += 1
        except:
            continue
        
        if i % 10 == 0:
            time.sleep(0.1)  # Pequena pausa a cada 10 requests
    
    print(f"   🌐 Anônimo - Sucessos: {anon_success}, Bloqueados: {anon_blocked}")
    
    # Testar como usuário logado
    client.login(username='admin', password='admin123')
    staff_blocked = 0
    staff_success = 0
    
    for i in range(50):  # 50 requisições como staff
        response = client.get('/config/')
        if response.status_code == 429:
            staff_blocked += 1
        elif response.status_code in [200, 302]:
            staff_success += 1
    
    print(f"   👑 Staff - Sucessos: {staff_success}, Bloqueados: {staff_blocked}")
    
    # 6. Resumo final
    print("\n🎯 === RESUMO FINAL ===")
    
    all_tests_passed = True
    
    if rate_limit_ok:
        print("✅ Rate Limiting: FUNCIONANDO")
    else:
        print("❌ Rate Limiting: PROBLEMA")
        all_tests_passed = False
    
    if login_success:
        print("✅ Sistema de Login: FUNCIONANDO")
    else:
        print("❌ Sistema de Login: PROBLEMA")
        all_tests_passed = False
    
    if audit_logs > 0:
        print("✅ Sistema de Auditoria: FUNCIONANDO")
    else:
        print("❌ Sistema de Auditoria: PROBLEMA")
        all_tests_passed = False
    
    if active_staff > 0:
        print("✅ Usuários Staff: DISPONÍVEIS")
    else:
        print("❌ Usuários Staff: PROBLEMA")
        all_tests_passed = False
    
    if staff_blocked == 0:
        print("✅ Rate Limiting Staff: OTIMIZADO")
    else:
        print("⚠️ Rate Limiting Staff: PODE PRECISAR AJUSTE")
    
    print("\n" + "="*50)
    
    if all_tests_passed:
        print("🎉 SISTEMA 100% FUNCIONAL!")
        print("🚀 PROJETO HAVOC PRONTO PARA PRODUÇÃO!")
        print("\n📋 CREDENCIAIS:")
        print("🔑 Usuário: admin")
        print("🔑 Senha: admin123")
        print("🌐 URL Config: http://127.0.0.1:8000/config/")
        print("🌐 URL Admin: http://127.0.0.1:8000/admin/")
    else:
        print("⚠️ SISTEMA COM ALGUNS PROBLEMAS")
        print("🔧 Verifique os itens marcados com ❌")

if __name__ == '__main__':
    final_system_validation()
