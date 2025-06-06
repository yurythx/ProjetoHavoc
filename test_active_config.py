#!/usr/bin/env python
"""
Teste rápido da função get_active_email_config corrigida
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.email_utils import get_active_email_config, send_test_email

print("🧪 TESTANDO FUNÇÃO CORRIGIDA")
print("=" * 40)

# Testar get_active_email_config
active_config = get_active_email_config()

if active_config:
    print(f"✅ Configuração ativa encontrada: {active_config.slug}")
    print(f"📧 Host: {active_config.email_host}")
    print(f"👤 User: {active_config.email_host_user}")
    print(f"🔑 Senha: {'✅ OK' if active_config.get_password() else '❌ Vazia'}")
    
    # Testar envio usando a configuração ativa (sem passar config)
    print("\n📧 Testando envio sem passar config...")
    success, message = send_test_email('projetohavoc@gmail.com')
    
    if success:
        print(f"✅ {message}")
        print("🎉 PROBLEMA RESOLVIDO! Interface web deve funcionar agora!")
    else:
        print(f"❌ {message}")
else:
    print("❌ Ainda não encontrou configuração ativa")
