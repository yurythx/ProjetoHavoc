#!/usr/bin/env python
"""
Script para verificar o status do usuário yurymenezes@hotmail.com
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import CustomUser

def check_user_status():
    """Verifica o status do usuário"""
    email = "yurymenezes@hotmail.com"
    
    print(f"🔍 Verificando usuário: {email}")
    print("=" * 50)
    
    try:
        # Buscar usuário pelo email
        user = CustomUser.objects.get(email=email)
        
        print(f"✅ Usuário encontrado!")
        print(f"📧 Email: {user.email}")
        print(f"👤 Username: {user.username}")
        print(f"📛 Nome: {user.first_name} {user.last_name}")
        print(f"🔑 ID: {user.id}")
        print(f"📅 Criado em: {user.date_joined}")
        print(f"🕐 Último login: {user.last_login}")
        print()
        
        # Status do usuário
        print("📊 STATUS DO USUÁRIO:")
        print(f"   ✓ Ativo: {'✅ SIM' if user.is_active else '❌ NÃO'}")
        print(f"   ✓ Staff: {'✅ SIM' if user.is_staff else '❌ NÃO'}")
        print(f"   ✓ Superuser: {'✅ SIM' if user.is_superuser else '❌ NÃO'}")
        print()
        
        # Verificar email
        print("📧 STATUS DO EMAIL:")
        if hasattr(user, 'emailaddress_set'):
            email_addresses = user.emailaddress_set.all()
            if email_addresses:
                for email_addr in email_addresses:
                    print(f"   📧 {email_addr.email}")
                    print(f"      ✓ Verificado: {'✅ SIM' if email_addr.verified else '❌ NÃO'}")
                    print(f"      ✓ Primário: {'✅ SIM' if email_addr.primary else '❌ NÃO'}")
            else:
                print("   ⚠️ Nenhum endereço de email encontrado no allauth")
        else:
            print("   ℹ️ Sistema allauth não configurado para este usuário")
        print()
        
        # Verificar senha
        print("🔐 STATUS DA SENHA:")
        if user.password:
            print(f"   ✓ Senha definida: ✅ SIM")
            print(f"   ✓ Hash da senha: {user.password[:20]}...")
            
            # Testar se a senha pode ser verificada
            from django.contrib.auth import authenticate
            print("   🧪 Testando autenticação...")
            
            # Não vamos testar com senha real por segurança
            print("   ℹ️ Para testar login, use o formulário web")
        else:
            print("   ❌ Senha não definida!")
        print()
        
        # Verificar grupos e permissões
        print("👥 GRUPOS E PERMISSÕES:")
        groups = user.groups.all()
        if groups:
            for group in groups:
                print(f"   👥 Grupo: {group.name}")
        else:
            print("   ℹ️ Usuário não pertence a nenhum grupo")
        
        user_permissions = user.user_permissions.all()
        if user_permissions:
            print("   🔑 Permissões específicas:")
            for perm in user_permissions:
                print(f"      - {perm.name}")
        else:
            print("   ℹ️ Nenhuma permissão específica")
        print()
        
        # Sugestões de correção
        print("🔧 SUGESTÕES DE CORREÇÃO:")
        
        if not user.is_active:
            print("   ❗ PROBLEMA: Usuário não está ativo")
            print("   💡 SOLUÇÃO: Ativar usuário")
            user.is_active = True
            user.save()
            print("   ✅ Usuário ativado!")
        
        # Verificar email verification
        if hasattr(user, 'emailaddress_set'):
            email_addresses = user.emailaddress_set.all()
            unverified_emails = [ea for ea in email_addresses if not ea.verified]
            if unverified_emails:
                print("   ❗ PROBLEMA: Email não verificado")
                print("   💡 SOLUÇÃO: Verificar email automaticamente")
                for email_addr in unverified_emails:
                    email_addr.verified = True
                    email_addr.save()
                    print(f"   ✅ Email {email_addr.email} verificado!")
        
        print("\n🎉 Verificação concluída!")
        
    except CustomUser.DoesNotExist:
        print(f"❌ Usuário com email {email} não encontrado!")
        print("\n🔍 Buscando usuários similares...")
        
        # Buscar usuários com emails similares
        similar_users = CustomUser.objects.filter(email__icontains="yury")
        if similar_users:
            print("👥 Usuários encontrados com 'yury':")
            for user in similar_users:
                print(f"   📧 {user.email} - {'✅ Ativo' if user.is_active else '❌ Inativo'}")
        
        # Listar todos os usuários
        all_users = CustomUser.objects.all()[:10]
        print(f"\n👥 Primeiros 10 usuários no sistema:")
        for user in all_users:
            print(f"   📧 {user.email} - {'✅ Ativo' if user.is_active else '❌ Inativo'}")
    
    except Exception as e:
        print(f"❌ Erro ao verificar usuário: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_user_status()
