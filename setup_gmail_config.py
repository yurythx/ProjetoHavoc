#!/usr/bin/env python
"""
Script para configurar Gmail com senha de app
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import EmailConfig

def setup_gmail_config():
    """Configura Gmail com senha de app"""
    print("🔧 CONFIGURANDO GMAIL COM SENHA DE APP")
    print("=" * 50)
    
    # Configurações do Gmail
    config_data = {
        'email_host': 'smtp.gmail.com',
        'email_port': 587,
        'email_host_user': 'projetohavoc@gmail.com',
        'email_host_password': 'jovbcnpsshqjrooh',  # Senha de app
        'email_use_tls': True,
        'default_from_email': 'projetohavoc@gmail.com',
        'is_active': True,
        'is_default': True
    }
    
    try:
        # Verificar se já existe configuração para Gmail
        existing_config = EmailConfig.objects.filter(
            email_host='smtp.gmail.com',
            email_host_user='projetohavoc@gmail.com'
        ).first()
        
        if existing_config:
            print(f"📧 Configuração Gmail existente encontrada: {existing_config.slug}")
            print("🔄 Atualizando com senha de app...")
            
            # Atualizar configuração existente
            for key, value in config_data.items():
                setattr(existing_config, key, value)
            
            existing_config.save()
            config = existing_config
            
        else:
            print("📧 Criando nova configuração Gmail...")
            config = EmailConfig.objects.create(**config_data)
        
        print(f"✅ Gmail configurado com sucesso!")
        print(f"🏷️ Slug: {config.slug}")
        print(f"📧 Host: {config.email_host}:{config.email_port}")
        print(f"👤 Usuário: {config.email_host_user}")
        print(f"🔒 TLS: {config.email_use_tls}")
        print(f"🔑 Senha de app: {'*' * 12} (configurada)")
        print(f"⭐ Padrão: {config.is_default}")
        
        return config
        
    except Exception as e:
        print(f"❌ Erro ao configurar Gmail: {e}")
        return None

def test_gmail_connection():
    """Testa a conexão com Gmail"""
    print("\n🧪 TESTANDO CONEXÃO COM GMAIL...")
    print("=" * 40)
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Configurar temporariamente as configurações de email
        gmail_config = EmailConfig.objects.filter(
            email_host='smtp.gmail.com',
            is_active=True
        ).first()
        
        if not gmail_config:
            print("❌ Configuração Gmail não encontrada")
            return False
        
        # Aplicar configurações
        settings.EMAIL_HOST = gmail_config.email_host
        settings.EMAIL_PORT = gmail_config.email_port
        settings.EMAIL_HOST_USER = gmail_config.email_host_user
        settings.EMAIL_HOST_PASSWORD = gmail_config.email_host_password
        settings.EMAIL_USE_TLS = gmail_config.email_use_tls
        settings.DEFAULT_FROM_EMAIL = gmail_config.default_from_email
        
        print(f"📧 Enviando email de teste para: {gmail_config.email_host_user}")
        
        # Enviar email de teste
        send_mail(
            subject='Teste de Configuração Gmail - ProjetoHavoc',
            message='Este é um email de teste para verificar se a configuração do Gmail está funcionando corretamente.\n\nSe você recebeu este email, a configuração está perfeita!',
            from_email=gmail_config.default_from_email,
            recipient_list=[gmail_config.email_host_user],
            fail_silently=False,
        )
        
        print("✅ Email de teste enviado com sucesso!")
        print("📬 Verifique sua caixa de entrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email de teste: {e}")
        return False

def cleanup_other_configs():
    """Remove outras configurações e deixa apenas Gmail"""
    print("\n🧹 LIMPANDO OUTRAS CONFIGURAÇÕES...")
    print("=" * 40)
    
    # Desativar outras configurações
    other_configs = EmailConfig.objects.exclude(
        email_host='smtp.gmail.com',
        email_host_user='projetohavoc@gmail.com'
    )
    
    if other_configs.exists():
        count = 0
        for config in other_configs:
            if config.is_default:
                config.is_default = False
                config.is_active = False
                config.save()
                count += 1
                print(f"🔄 Desativado: {config.slug}")
        
        print(f"✅ {count} configuração(ões) desativada(s)")
    else:
        print("ℹ️ Nenhuma outra configuração encontrada")

def show_final_status():
    """Mostra status final das configurações"""
    print("\n📊 STATUS FINAL DAS CONFIGURAÇÕES:")
    print("=" * 40)
    
    configs = EmailConfig.objects.all()
    
    for config in configs:
        status = "✅ ATIVO" if config.is_active else "❌ INATIVO"
        default = "⭐ PADRÃO" if config.is_default else ""
        
        print(f"🏷️ {config.slug}")
        print(f"   📧 {config.email_host}:{config.email_port}")
        print(f"   👤 {config.email_host_user}")
        print(f"   {status} {default}")
        print()

if __name__ == "__main__":
    print("🚀 CONFIGURAÇÃO AUTOMÁTICA DO GMAIL")
    print("=" * 60)
    
    # Configurar Gmail
    config = setup_gmail_config()
    
    if config:
        # Limpar outras configurações
        cleanup_other_configs()
        
        # Testar conexão
        test_success = test_gmail_connection()
        
        # Mostrar status final
        show_final_status()
        
        if test_success:
            print("🎉 GMAIL CONFIGURADO E TESTADO COM SUCESSO!")
            print("📧 Sua aplicação está pronta para enviar emails!")
        else:
            print("⚠️ Gmail configurado, mas teste falhou")
            print("💡 Verifique se a senha de app está correta")
    else:
        print("❌ Falha na configuração do Gmail")
