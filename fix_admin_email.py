#!/usr/bin/env python
"""
Corrigir email do usuário admin
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

def fix_admin_email():
    """Corrigir email do usuário admin"""
    print("🔧 === CORRIGINDO EMAIL DO USUÁRIO ADMIN ===")
    
    User = get_user_model()
    
    try:
        admin_user = User.objects.get(username='admin')
        
        print(f"📊 Estado atual:")
        print(f"   👤 Usuário: {admin_user.username}")
        print(f"   📧 Email: {admin_user.email}")
        print(f"   ✉️ Email verificado: {admin_user.email_verificado}")
        print(f"   🔐 Código ativação: {admin_user.codigo_ativacao}")
        
        # Ativar email
        admin_user.email_verificado = True
        admin_user.codigo_ativacao = None
        admin_user.save()
        
        print(f"\n✅ Email ativado com sucesso!")
        print(f"   ✉️ Email verificado: {admin_user.email_verificado}")
        print(f"   🔐 Código ativação: {admin_user.codigo_ativacao}")
        
        # Testar acesso
        from django.test import Client
        
        client = Client()
        login_success = client.login(username='admin', password='admin123')
        
        if login_success:
            print(f"\n🔑 Login testado: ✅")
            
            # Testar config
            response = client.get('/config/system/system-config/')
            print(f"📄 Config page: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
            # Testar profile
            profile_response = client.get('/accounts/profile/')
            print(f"👤 Profile page: {profile_response.status_code} {'✅' if profile_response.status_code == 200 else '❌'}")
            
            if profile_response.status_code == 302:
                print(f"   🔄 Ainda redireciona para: {profile_response.url}")
        else:
            print(f"\n🔑 Login testado: ❌")
            
    except User.DoesNotExist:
        print("❌ Usuário admin não encontrado")

if __name__ == '__main__':
    fix_admin_email()
