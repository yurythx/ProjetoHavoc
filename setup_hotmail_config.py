#!/usr/bin/env python
"""
Script para configurar email Hotmail/Outlook automaticamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import EmailConfig

def setup_hotmail_config():
    """Configura email Hotmail/Outlook"""
    print("🔧 CONFIGURANDO EMAIL HOTMAIL/OUTLOOK")
    print("=" * 50)
    
    # Configurações do Hotmail/Outlook
    config_data = {
        'email_host': 'smtp-mail.outlook.com',
        'email_port': 587,
        'email_host_user': 'yurymenezes@hotmail.com',  # Seu email
        'email_use_tls': True,
        'default_from_email': 'yurymenezes@hotmail.com',
        'is_active': True,
        'is_default': True
    }
    
    try:
        # Verificar se já existe configuração para Hotmail
        existing_config = EmailConfig.objects.filter(
            email_host='smtp-mail.outlook.com',
            email_host_user='yurymenezes@hotmail.com'
        ).first()
        
        if existing_config:
            print(f"📧 Configuração existente encontrada: {existing_config.slug}")
            print("🔄 Atualizando configuração...")
            
            # Atualizar configuração existente
            for key, value in config_data.items():
                setattr(existing_config, key, value)
            
            existing_config.save()
            config = existing_config
            
        else:
            print("📧 Criando nova configuração Hotmail...")
            config = EmailConfig.objects.create(**config_data)
        
        print(f"✅ Configuração criada/atualizada com sucesso!")
        print(f"🏷️ Slug: {config.slug}")
        print(f"📧 Host: {config.email_host}:{config.email_port}")
        print(f"👤 Usuário: {config.email_host_user}")
        print(f"🔒 TLS: {config.email_use_tls}")
        print(f"⭐ Padrão: {config.is_default}")
        
        print("\n📝 PRÓXIMOS PASSOS:")
        print("1. Acesse: http://127.0.0.1:8000/config/email/")
        print("2. Encontre a configuração do Hotmail")
        print("3. Clique em 'Editar' e adicione sua senha")
        print("4. Teste a configuração")
        
        print("\n💡 DICA IMPORTANTE:")
        print("Para Hotmail/Outlook, você pode usar sua senha normal")
        print("Não precisa de senha de app como no Gmail")
        
        return config
        
    except Exception as e:
        print(f"❌ Erro ao configurar Hotmail: {e}")
        return None

def show_email_configs():
    """Mostra todas as configurações de email"""
    print("\n📋 CONFIGURAÇÕES DE EMAIL EXISTENTES:")
    print("=" * 40)
    
    configs = EmailConfig.objects.all()
    
    if configs.exists():
        for i, config in enumerate(configs, 1):
            print(f"{i}. 🏷️ {config.slug}")
            print(f"   📧 {config.email_host}:{config.email_port}")
            print(f"   👤 {config.email_host_user}")
            print(f"   ✅ Ativo: {config.is_active}")
            print(f"   ⭐ Padrão: {config.is_default}")
            print()
    else:
        print("ℹ️ Nenhuma configuração encontrada")

def cleanup_gmail_configs():
    """Remove configurações do Gmail se houver"""
    print("\n🧹 LIMPANDO CONFIGURAÇÕES DO GMAIL...")
    
    gmail_configs = EmailConfig.objects.filter(email_host='smtp.gmail.com')
    
    if gmail_configs.exists():
        count = gmail_configs.count()
        gmail_configs.delete()
        print(f"🗑️ {count} configuração(ões) do Gmail removida(s)")
    else:
        print("ℹ️ Nenhuma configuração do Gmail encontrada")

if __name__ == "__main__":
    print("🚀 SETUP AUTOMÁTICO DE EMAIL HOTMAIL")
    print("=" * 60)
    
    # Mostrar configurações atuais
    show_email_configs()
    
    # Limpar configurações do Gmail (opcional)
    cleanup_gmail_configs()
    
    # Configurar Hotmail
    config = setup_hotmail_config()
    
    if config:
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("Agora você pode testar o envio de emails com Hotmail")
    else:
        print("\n❌ Falha na configuração")
    
    # Mostrar estado final
    show_email_configs()
