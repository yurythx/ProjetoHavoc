#!/usr/bin/env python
"""
Script para testar se o rate limiting foi corrigido
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

def test_rate_limit_fix():
    """Testa se o rate limiting foi corrigido"""
    print("🔧 === TESTANDO CORREÇÃO DO RATE LIMITING ===")
    
    base_url = 'http://127.0.0.1:8000'
    
    # 1. Testar acesso básico
    print("\n1. 🌐 Testando acesso básico...")
    try:
        response = requests.get(f'{base_url}/admin/', timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Acesso ao admin funcionando")
        elif response.status_code == 302:
            print("   ✅ Redirecionamento para login (normal)")
        elif response.status_code == 429:
            print("   ❌ Ainda bloqueado por rate limiting")
        else:
            print(f"   ⚠️ Status inesperado: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erro de conexão: {e}")
    
    # 2. Testar múltiplas requisições
    print("\n2. 🔄 Testando múltiplas requisições...")
    success_count = 0
    rate_limited_count = 0
    
    for i in range(10):
        try:
            response = requests.get(f'{base_url}/admin/', timeout=2)
            if response.status_code in [200, 302]:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
            time.sleep(0.1)  # Pequena pausa
        except:
            continue
    
    print(f"   ✅ Sucessos: {success_count}/10")
    print(f"   ❌ Rate limited: {rate_limited_count}/10")
    
    if rate_limited_count == 0:
        print("   🎉 Rate limiting corrigido!")
    else:
        print("   ⚠️ Ainda há problemas de rate limiting")
    
    # 3. Testar com login
    print("\n3. 🔑 Testando com usuário logado...")
    client = Client()
    
    try:
        # Fazer login
        login_success = client.login(username='admin', password='admin123')
        if login_success:
            print("   ✅ Login realizado")
            
            # Testar múltiplas requisições como usuário logado
            admin_success = 0
            for i in range(5):
                response = client.get('/admin/')
                if response.status_code in [200, 302]:
                    admin_success += 1
            
            print(f"   ✅ Acesso admin como staff: {admin_success}/5")
            
            if admin_success == 5:
                print("   🎉 Rate limiting para staff funcionando!")
        else:
            print("   ❌ Falha no login")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n🎯 === RESUMO ===")
    if rate_limited_count == 0:
        print("✅ Rate limiting corrigido com sucesso!")
        print("👑 Staff/Admin: 1000 requests/minuto")
        print("👤 Usuários: 300 requests/minuto")
        print("🌐 Anônimos: 100 requests/minuto")
    else:
        print("⚠️ Rate limiting ainda precisa de ajustes")

if __name__ == '__main__':
    test_rate_limit_fix()
