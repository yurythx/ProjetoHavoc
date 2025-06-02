#!/usr/bin/env python
"""
Script para corrigir usuários e ativar o sistema de login
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

def main():
    User = get_user_model()
    
    print("=== CORRIGINDO USUÁRIOS ===")
    
    # Ativar usuário yurymenezes
    try:
        user = User.objects.get(username='yurymenezes')
        user.is_active = True
        user.save()
        print(f"✅ Usuário {user.username} ativado")
    except User.DoesNotExist:
        print("❌ Usuário yurymenezes não encontrado")
    
    # Ativar usuário admin
    try:
        user = User.objects.get(username='admin')
        user.is_active = True
        user.save()
        print(f"✅ Usuário {user.username} ativado")
    except User.DoesNotExist:
        print("❌ Usuário admin não encontrado")
    
    # Criar usuário de teste simples se não existir
    test_username = 'teste'
    if not User.objects.filter(username=test_username).exists():
        test_user = User.objects.create_user(
            username=test_username,
            email='teste@projetohavoc.com',
            password='123456',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print(f"✅ Usuário de teste criado: {test_user.username}")
    
    print("\n=== USUÁRIOS ATIVOS ===")
    active_users = User.objects.filter(is_active=True)
    for user in active_users:
        print(f"👤 {user.username} - Staff: {user.is_staff} - Superuser: {user.is_superuser}")
    
    print("\n=== CREDENCIAIS PARA TESTE ===")
    print("🔑 admin / admin123")
    print("🔑 teste / 123456")

if __name__ == '__main__':
    main()
