#!/usr/bin/env python
"""
Teste do sistema de registro com transação atômica
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from apps.config.models import EmailConfig

User = get_user_model()

print("🧪 TESTE DE TRANSAÇÃO ATÔMICA NO REGISTRO")
print("=" * 50)

# Contar usuários antes
users_before = User.objects.count()
print(f"👥 Usuários antes do teste: {users_before}")

# Simular falha de email temporariamente
print("\n🔧 Simulando falha de email...")

# Desativar configuração de email temporariamente
gmail_config = EmailConfig.objects.filter(email_host='smtp.gmail.com').first()
if gmail_config:
    gmail_config.is_active = False
    gmail_config.save()
    print("✅ Configuração Gmail desativada temporariamente")

# Tentar criar usuário com email inválido
client = Client()

print("\n📝 Tentando registrar usuário com email que falhará...")
response = client.post('/accounts/register/', {
    'username': 'teste_transacao',
    'email': 'teste@exemplo.com',
    'first_name': 'Teste',
    'last_name': 'Transacao',
    'password1': 'senha123456',
    'password2': 'senha123456',
})

print(f"📊 Status da resposta: {response.status_code}")

# Contar usuários depois
users_after = User.objects.count()
print(f"👥 Usuários depois do teste: {users_after}")

# Verificar se usuário foi criado
test_user = User.objects.filter(username='teste_transacao').first()

if test_user:
    print("❌ PROBLEMA: Usuário foi criado mesmo com falha no email!")
    print(f"   👤 Usuário: {test_user.username}")
    print(f"   📧 Email: {test_user.email}")
    print(f"   ✅ Ativo: {test_user.is_active}")
    
    # Limpar usuário de teste
    test_user.delete()
    print("🗑️ Usuário de teste removido")
else:
    print("✅ SUCESSO: Usuário NÃO foi criado (transação funcionou!)")

# Reativar configuração de email
if gmail_config:
    gmail_config.is_active = True
    gmail_config.save()
    print("\n🔧 Configuração Gmail reativada")

print(f"\n📊 Diferença de usuários: {users_after - users_before}")

if users_after == users_before:
    print("🎉 TRANSAÇÃO ATÔMICA FUNCIONANDO CORRETAMENTE!")
    print("✅ Usuários só são salvos se o email for enviado com sucesso")
else:
    print("❌ PROBLEMA: Transação não está funcionando corretamente")
    print("⚠️ Usuários estão sendo salvos mesmo com falha no email")
