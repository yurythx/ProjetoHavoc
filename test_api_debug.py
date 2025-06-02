#!/usr/bin/env python
"""
Teste específico para API de debug
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
import json

def test_api_debug():
    """Testa se debug_mode está na API"""
    print("🌐 === TESTANDO API DE DEBUG ===")
    
    client = Client()
    
    # Fazer login
    login_success = client.login(username='admin', password='admin123')
    if not login_success:
        print("   ❌ Falha no login")
        return
    
    print("   ✅ Login realizado")
    
    # Testar API de status
    response = client.get('/config/api/status/')
    
    if response.status_code == 200:
        print("   ✅ API acessível")
        
        try:
            data = response.json()
            print(f"   📊 Dados recebidos: {json.dumps(data, indent=2)}")
            
            # Verificar se debug_mode está nos dados
            if 'modules' in data and 'system' in data['modules']:
                system_module = data['modules']['system']
                if 'details' in system_module and 'debug_mode' in system_module['details']:
                    debug_mode = system_module['details']['debug_mode']
                    print(f"   ✅ Debug_mode encontrado na API: {debug_mode}")
                else:
                    print("   ❌ Debug_mode não encontrado nos detalhes do sistema")
            else:
                print("   ❌ Estrutura de módulos não encontrada")
                
        except json.JSONDecodeError:
            print("   ❌ Erro ao decodificar JSON")
    else:
        print(f"   ❌ Erro na API: {response.status_code}")

if __name__ == '__main__':
    test_api_debug()
