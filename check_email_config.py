#!/usr/bin/env python
"""
Script para verificar e corrigir configurações de email
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import EmailConfig

def check_email_configs():
    """Verifica todas as configurações de email"""
    print("🔍 VERIFICANDO CONFIGURAÇÕES DE EMAIL")
    print("=" * 50)
    
    configs = EmailConfig.objects.all()
    
    for config in configs:
        print(f"\n🏷️ {config.slug}")
        print(f"   📧 Host: {config.email_host}:{config.email_port}")
        print(f"   👤 Usuário: {config.email_host_user}")
        print(f"   🔑 Senha: {'✅ Configurada' if config.email_host_password else '❌ Não configurada'}")
        print(f"   🔒 TLS: {config.email_use_tls}")
        print(f"   ✅ Ativo: {config.is_active}")
        print(f"   ⭐ Padrão: {config.is_default}")
        
        if config.email_host_password:
            print(f"   🔐 Senha (primeiros 4 chars): {config.email_host_password[:4]}...")

def fix_gmail_config():
    """Corrige a configuração do Gmail"""
    print("\n🔧 CORRIGINDO CONFIGURAÇÃO DO GMAIL")
    print("=" * 40)
    
    try:
        # Buscar configuração do Gmail
        gmail_config = EmailConfig.objects.filter(
            email_host='smtp.gmail.com'
        ).first()
        
        if gmail_config:
            print(f"📧 Configuração encontrada: {gmail_config.slug}")
            
            # Atualizar com dados corretos
            gmail_config.email_host_user = 'projetohavoc@gmail.com'
            gmail_config.email_host_password = 'jovbcnpsshqjrooh'
            gmail_config.default_from_email = 'projetohavoc@gmail.com'
            gmail_config.is_active = True
            gmail_config.is_default = True
            gmail_config.save()
            
            print("✅ Gmail atualizado com sucesso!")
            
            # Desativar outras configurações como padrão
            other_configs = EmailConfig.objects.exclude(id=gmail_config.id)
            for config in other_configs:
                if config.is_default:
                    config.is_default = False
                    config.save()
                    print(f"🔄 {config.slug} removido como padrão")
            
            return gmail_config
        else:
            print("❌ Configuração Gmail não encontrada")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao corrigir Gmail: {e}")
        return None

def test_email_sending():
    """Testa envio de email"""
    print("\n🧪 TESTANDO ENVIO DE EMAIL")
    print("=" * 30)
    
    try:
        from django.core.mail import send_mail
        
        # Enviar email de teste
        result = send_mail(
            subject='Teste Final - ProjetoHavoc',
            message='Este é um teste final para confirmar que o email está funcionando perfeitamente!',
            from_email='projetohavoc@gmail.com',
            recipient_list=['projetohavoc@gmail.com'],
            fail_silently=False,
        )
        
        if result:
            print("✅ Email enviado com sucesso!")
            print("📬 Verifique sua caixa de entrada")
            return True
        else:
            print("❌ Falha no envio do email")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de email: {e}")
        return False

def force_apply_gmail_settings():
    """Força aplicação das configurações do Gmail"""
    print("\n⚡ FORÇANDO APLICAÇÃO DAS CONFIGURAÇÕES")
    print("=" * 45)
    
    try:
        from django.conf import settings
        
        # Aplicar configurações diretamente
        settings.EMAIL_HOST = 'smtp.gmail.com'
        settings.EMAIL_PORT = 587
        settings.EMAIL_HOST_USER = 'projetohavoc@gmail.com'
        settings.EMAIL_HOST_PASSWORD = 'jovbcnpsshqjrooh'
        settings.EMAIL_USE_TLS = True
        settings.DEFAULT_FROM_EMAIL = 'projetohavoc@gmail.com'
        
        print("✅ Configurações aplicadas diretamente no Django")
        
        # Verificar se as configurações foram aplicadas
        print(f"📧 HOST: {settings.EMAIL_HOST}")
        print(f"🔌 PORT: {settings.EMAIL_PORT}")
        print(f"👤 USER: {settings.EMAIL_HOST_USER}")
        print(f"🔑 PASSWORD: {'*' * 12}")
        print(f"🔒 TLS: {settings.EMAIL_USE_TLS}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar configurações: {e}")
        return False

if __name__ == "__main__":
    print("🔬 DIAGNÓSTICO COMPLETO DE EMAIL")
    print("=" * 60)
    
    # Verificar configurações atuais
    check_email_configs()
    
    # Corrigir Gmail
    gmail_config = fix_gmail_config()
    
    if gmail_config:
        # Forçar aplicação das configurações
        force_apply_gmail_settings()
        
        # Testar envio
        test_success = test_email_sending()
        
        if test_success:
            print("\n🎉 TUDO FUNCIONANDO PERFEITAMENTE!")
        else:
            print("\n⚠️ Configuração correta, mas teste falhou")
    
    # Verificar estado final
    print("\n📊 ESTADO FINAL:")
    check_email_configs()
