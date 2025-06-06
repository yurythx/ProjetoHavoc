#!/usr/bin/env python
"""
Teste direto do logout
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Criar cliente de teste
client = Client()

print("🧪 TESTE DIRETO DO LOGOUT")
print("=" * 40)

# Fazer login primeiro
user = User.objects.get(username='yurymenezes')
client.force_login(user)
print(f"✅ Login forçado para: {user.username}")

# Testar logout
response = client.get('/accounts/logout/')
print(f"📤 GET /accounts/logout/")
print(f"📊 Status Code: {response.status_code}")
print(f"🔄 Redirect URL: {response.get('Location', 'Nenhum redirect')}")

if response.status_code == 302:
    print("✅ LOGOUT FUNCIONANDO! (Redirect 302)")
elif response.status_code == 200:
    print("❌ LOGOUT MOSTRANDO PÁGINA (200)")
    print("🔍 Conteúdo da resposta:")
    print(response.content.decode()[:200] + "...")
else:
    print(f"❓ Status inesperado: {response.status_code}")

# Verificar se usuário foi deslogado
response2 = client.get('/accounts/profile/')
print(f"\n📤 GET /accounts/profile/ (após logout)")
print(f"📊 Status Code: {response2.status_code}")

if response2.status_code == 302:
    print("✅ Usuário foi deslogado (redirecionado para login)")
else:
    print("❌ Usuário ainda está logado")
