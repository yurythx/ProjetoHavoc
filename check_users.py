#!/usr/bin/env python
"""
Script para verificar usuários existentes no sistema
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
    
    print("=== USUÁRIOS EXISTENTES ===")
    users = User.objects.all()
    
    if not users.exists():
        print("❌ Nenhum usuário encontrado!")
        print("\n🔧 Criando usuário admin...")
        
        # Criar usuário admin
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@projetohavoc.com',
            password='admin123',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print(f"✅ Usuário admin criado: {admin_user.username}")
        
        # Verificar novamente
        users = User.objects.all()
    
    for user in users:
        print(f"👤 {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   🔧 Staff: {user.is_staff}")
        print(f"   👑 Superuser: {user.is_superuser}")
        print(f"   ✅ Ativo: {user.is_active}")
        print(f"   📅 Criado: {user.date_joined}")
        print()

if __name__ == '__main__':
    main()
