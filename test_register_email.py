#!/usr/bin/env python
"""
Teste do sistema de registro com email corrigido
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.email_utils import get_active_email_config, send_email_with_config

print("🧪 TESTE DO SISTEMA DE EMAIL NO REGISTRO")
print("=" * 50)

# Verificar configuração ativa
config = get_active_email_config()

if config:
    print(f"✅ Configuração ativa: {config.slug}")
    print(f"📧 Host: {config.email_host}")
    print(f"👤 User: {config.email_host_user}")
    print(f"🔑 Senha: {'✅ OK' if config.get_password() else '❌ Vazia'}")
    
    # Testar envio de email como o registro faria
    print("\n📧 Testando envio como no registro...")
    
    subject = "Código de Ativação da Conta"
    message = """
    <h2>Bem-vindo ao Projeto Havoc!</h2>
    <p>Seu código de ativação é: <strong>123456</strong></p>
    <p>Este é um teste do sistema de registro corrigido.</p>
    """
    
    success = send_email_with_config(
        subject=subject,
        message=message,
        recipient_list=['projetohavoc@gmail.com'],
        html_message=message
    )
    
    if success:
        print("✅ Email de teste enviado com sucesso!")
        print("🎉 Sistema de registro deve funcionar agora!")
    else:
        print("❌ Falha no envio do email de teste")
        
else:
    print("❌ Nenhuma configuração de email ativa encontrada")
    print("💡 Execute o script de configuração do Gmail primeiro")
